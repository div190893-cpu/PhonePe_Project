from sql_connection import get_sql_connection
import pandas as pd
import json
import os
import mysql.connector
import traceback


BATCH_SIZE = 20000

def execute_query(cur, query):
    cur.execute(query)

def create_tables(connection):
    cur = connection.cursor()
    execute_query(cur, "CREATE DATABASE IF NOT EXISTS phonepe;")
    execute_query(cur, "USE phonepe;")

    table_queries = [
        """
        CREATE TABLE IF NOT EXISTS Aggregated_Transaction_Data (
            State VARCHAR(100), Year SMALLINT, Quarter TINYINT,
            Transaction_type VARCHAR(50),
            Transaction_count BIGINT,
            Transaction_amount DECIMAL(18,2),
            INDEX idx_trans (State, Year, Quarter)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Aggregated_Insurance_Data (
            State VARCHAR(100), Year SMALLINT, Quarter TINYINT,
            Transaction_count BIGINT,
            Transaction_amount DECIMAL(18,2),
            INDEX idx_insurance (State, Year, Quarter)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Aggregated_user_Data (
            Brand VARCHAR(100),
            Count BIGINT,
            State VARCHAR(100),
            Year SMALLINT,
            Quarter TINYINT,
            INDEX idx_user (State, Year, Quarter)
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS map_transaction_data (
            District VARCHAR(100),
            Count BIGINT,
            Amount DECIMAL(18,2),
            State VARCHAR(100),
            Year SMALLINT,
            Quarter TINYINT,
            INDEX idx_map_trans (State, Year, Quarter)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS map_insurance_data (
            Latitude VARCHAR(50),
            Longitude VARCHAR(50),
            Metric VARCHAR(50),
            District VARCHAR(100),
            Transaction_Count BIGINT,
            Transaction_Amount DECIMAL(18,2),
            State VARCHAR(100),
            Year SMALLINT,
            Quarter TINYINT,
            INDEX idx_map_ins (State, Year, Quarter)
            
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS map_user_data (
            registeredUsers BIGINT,
            appOpens BIGINT,
            District VARCHAR(100),
            State VARCHAR(100),
            Year SMALLINT,
            Quarter TINYINT,
            INDEX idx_map_user (State, Year, Quarter)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS top_user_data (
            Name VARCHAR(100),
            registeredUsers BIGINT,
            Level VARCHAR(50),
            State VARCHAR(100),
            Year SMALLINT,
            Quarter TINYINT,
            INDEX idx_top_user (State, Year, Quarter)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS top_transaction_data (
            EntityName VARCHAR(100),
            registeredUsers BIGINT,
            State VARCHAR(100),
            Year SMALLINT,
            Quarter TINYINT,
            INDEX idx_top_trans (State, Year, Quarter)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS top_insurance_data (
            EntityName VARCHAR(100),
            TxnCount BIGINT,
            TxnAmount DECIMAL(18,2),
            State VARCHAR(100),
            Year SMALLINT,
            Quarter TINYINT,
            INDEX idx_top_ins (State, Year, Quarter)
        );
        """
        ,
        """
        CREATE TABLE IF NOT EXISTS PincodeData (
            circlename VARCHAR(50),
            regionname VARCHAR(50),
            divisionname VARCHAR(50),
            officename VARCHAR(50),
            pincode VARCHAR(50),
            officetype VARCHAR(50),
            delivery VARCHAR(50),
            district VARCHAR(50),
            statename VARCHAR(50),
            latitude VARCHAR(50),
            longitude VARCHAR(50)
);
        
        
        """
    ]

    for query in table_queries:
        execute_query(cur, query)

    connection.commit()
    cur.close()
    print("✅ Database and tables created successfully")


def load_json_from_paths(excel_path, extract_func, table, columns):
    connection = get_sql_connection()
    cur = connection.cursor()
    cur.execute("USE phonepe;")

    paths_df = pd.read_excel(excel_path)
    pending_values = []
    errors = []

    for p in paths_df.iloc[:, 0]:
        try:
            with open(p, "r", encoding="utf-8") as f:
                js = json.load(f)
        except:
            errors.append(p)
            continue

        df = extract_func(js)
        if df.empty:
            continue

        parts = p.replace("\\", "/").split("/")
        df["State"], df["Year"] = parts[-3], parts[-2]
        df["Quarter"] = parts[-1].split(".")[0]
        df = df[columns]
        pending_values.extend([tuple(x) for x in df.to_numpy()])

        if len(pending_values) >= BATCH_SIZE:
            cur.executemany(
                f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join(['%s']*len(columns))})",
                pending_values
            )
            connection.commit()
            pending_values = []

    if pending_values:
        cur.executemany(
            f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join(['%s']*len(columns))})",
            pending_values
        )
        connection.commit()

    cur.close()
    connection.close()
    print(f"✅ Inserted data into {table}")
    if errors:
        print(f"⚠️ Failed files for {table}: {len(errors)}")


"""
JSON Extractor Functions
"""
def ext_agg_trans(js):
    d=[]
    for i in js.get("data",{}).get("transactionData",[]):
        if i.get("paymentInstruments"):
            d.append({
                "Transaction_type":i["name"],
                "Transaction_count":i["paymentInstruments"][0]["count"],
                "Transaction_amount":i["paymentInstruments"][0]["amount"]
            })
    return pd.DataFrame(d)


def ext_agg_user(js):
    data = js.get("data", {})
    devices = data.get("usersByDevice") or []
    output = []
    for device in devices:
        if device:
            brand = device.get("brand", "Unknown")
            count = device.get("count", 0)
            output.append({"Brand": brand, "Count": count})
    return pd.DataFrame(output)

def ext_agg_ins(js):
    d=[]
    for i in js.get("data",{}).get("transactionData",[]):
        if i.get("paymentInstruments"):
            d.append({
                "Transaction_count":i["paymentInstruments"][0]["count"],
                "Transaction_amount":i["paymentInstruments"][0]["amount"]
            })
    return pd.DataFrame(d)

def ext_map_trans(js):
    d=[]
    for r in js.get("data",{}).get("hoverDataList",[]):
        dist=r.get("name")
        for m in r.get("metric",[]):
            d.append({"District":dist,"Count":m["count"],"Amount":m["amount"]})
    return pd.DataFrame(d)

def ext_map_user(js):
    d=[]
    h=js.get("data",{}).get("hoverData",{})
    for dist,v in h.items():
        d.append({"District":dist,"registeredUsers":v["registeredUsers"],"appOpens":v["appOpens"]})
    return pd.DataFrame(d)


def ext_map_ins(js, state, year, quarter):
    """
    Extracts district-level metrics from map_insurance JSON and returns a DataFrame
    with columns: Latitude, Longitude, Metric, District, Transaction_Count,
    Transaction_Amount, State, Year, Quarter
    """
    hover_data_list = js.get("data", {}).get("hoverDataList", [])
    if not hover_data_list:
        return pd.DataFrame()

    records = []
    for item in hover_data_list:
        district = item.get("name", "").title()
        metrics = item.get("metric", [])
        if not metrics:
            # keep a record with zeros if metric missing (optional)
            records.append({
                "Latitude": None,
                "Longitude": None,
                "Metric": None,
                "District": district,
                "Transaction_Count": 0,
                "Transaction_Amount": 0.0,
                "State": state,
                "Year": year,
                "Quarter": quarter
            })
            continue

        for metric in metrics:
            # metric is expected to have "type", "count", "amount"
            records.append({
                "Latitude": None,
                "Longitude": None,
                "Metric": metric.get("type", "TOTAL"),
                "District": district,
                "Transaction_Count": int(metric.get("count", 0)) if metric.get("count", None) is not None else 0,
                "Transaction_Amount": float(metric.get("amount", 0.0)) if metric.get("amount", None) is not None else 0.0,
                "State": state,
                "Year": year,
                "Quarter": quarter
            })

    return pd.DataFrame(records)



def ext_top_user(js):
    d=[]
    for p in js.get("data",{}).get("pincodes",[]):
        d.append({"Name":p["name"],"registeredUsers":p["registeredUsers"],"Level":"Pincode"})
    return pd.DataFrame(d)

def ext_top_trans(js):
    d=[]
    for p in js.get("data",{}).get("pincodes",[]):
        d.append({"EntityName":p["name"],"registeredUsers":p["registeredUsers"]})
    return pd.DataFrame(d)

def ext_top_ins(js):
    d=[]
    for p in js.get("data",{}).get("pincodes",[]):
        m=p.get("metric")
        if m:
            d.append({"EntityName":p["entityName"],"TxnCount":m["count"],"TxnAmount":m["amount"]})
    return pd.DataFrame(d)

def load_data_Table_map_insurance(connection, excel_path, batch_size=50000, debug_limit=None):
    """
    Load map_insurance_data JSON files listed in Excel into MySQL in batches.

    - excel_path: path to Excel that contains file paths (first column)
    - debug_limit: if set (int), stops after processing that many files (useful for debugging)
    """
    cur = connection.cursor()
    cur.execute("USE phonepe;")
    print("\n🚀 Loading map_insurance_data...")
    try:
        load_data_Table_map_insurance(
            connection,
            r"E:/Mr.D/Phonepay/Data/data/FilePaths_map_insurance.xlsx",
            batch_size=50000,
            debug_limit=10  # process only 10 files for testing
        )
    except Exception as e:
        print("❌ map_insurance_data loading failed:", e)

        # Read file paths from excel
    try:
        paths_df = pd.read_excel(excel_path, header=None)
    except Exception as e:
        print("❌ Failed to read Excel:", excel_path, e)
        raise

    pending_values = []
    errors = []  # will hold tuples (path, error_message)
    processed = 0

    for idx, p in enumerate(paths_df.iloc[:, 0].dropna()):
        if debug_limit and processed >= debug_limit:
            break

        # sometimes cell has an Excel formula or stray; ensure string
        p = str(p).strip()
        if not os.path.exists(p):
            errors.append((p, "File does not exist"))
            print(f"⚠️ File not found: {p}")
            processed += 1
            continue

        try:
            with open(p, "r", encoding="utf-8") as f:
                js = json.load(f)
        except Exception as e:
            errors.append((p, f"JSON load error: {e}"))
            print(f"⚠️ JSON load error for {p}: {e}")
            processed += 1
            continue

        # Extract State, Year, Quarter from path robustly (fall back to None)
        parts = p.replace("\\", "/").split("/")
        state = None
        year = None
        quarter = None
        try:
            # best-effort mapping: assume .../<state>/<year>/<quarter>.json
            if len(parts) >= 3:
                state = parts[-3]
                year_raw = parts[-2]
                quarter_raw = parts[-1].split(".")[0]
                try:
                    year = int(year_raw)
                except:
                    year = year_raw  # keep as string if not int
                try:
                    quarter = int(quarter_raw)
                except:
                    quarter = quarter_raw
        except Exception:
            pass

        # If any of state/year/quarter not found, still proceed but mark values
        if state is None:
            state = "Unknown"
        if year is None:
            year = 0
        if quarter is None:
            quarter = 0

        try:
            df = ext_map_ins(js, state, year, quarter)
        except Exception as e:
            tb = traceback.format_exc()
            errors.append((p, f"Extractor error: {e}\n{tb}"))
            print(f"⚠️ Extractor error for {p}: {e}")
            processed += 1
            continue

        if df.empty:
            # nothing to insert for this file
            processed += 1
            continue

        # Ensure column order matches DB table
        expected_cols = [
            "Latitude", "Longitude", "Metric", "District",
            "Transaction_Count", "Transaction_Amount", "State", "Year", "Quarter"
        ]
        # add missing columns with default None/0 if extractor didn't provide
        for col in expected_cols:
            if col not in df.columns:
                if col in ("Transaction_Count",):
                    df[col] = 0
                elif col in ("Transaction_Amount",):
                    df[col] = 0.0
                else:
                    df[col] = None

        df = df[expected_cols]

        # Convert types to Python native types (avoid numpy types that mysql connector may choke on)
        df = df.where(pd.notnull(df), None)

        pending_values.extend([tuple(x) for x in df.to_numpy()])

        # Batch insert
        if len(pending_values) >= batch_size:
            insert_query = """
                INSERT INTO map_insurance_data
                (Latitude, Longitude, Metric, District, Transaction_Count, Transaction_Amount, State, Year, Quarter)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            try:
                cur.executemany(insert_query, pending_values)
                connection.commit()
                print(f"✅ Inserted batch of {len(pending_values)} rows into map_insurance_data")
            except Exception as e:
                tb = traceback.format_exc()
                print("❌ Batch insert error:", e)
                print(tb)
                # move failing batch into errors list with message
                errors.append(("BATCH_INSERT", f"{e}\n{tb}"))
            pending_values = []

        processed += 1

    # Insert any remaining rows
    if pending_values:
        insert_query = """
            INSERT INTO map_insurance_data
            (Latitude, Longitude, Metric, District, Transaction_Count, Transaction_Amount, State, Year, Quarter)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cur.executemany(insert_query, pending_values)
            connection.commit()
            print(f"✅ Inserted final {len(pending_values)} rows into map_insurance_data")
        except Exception as e:
            tb = traceback.format_exc()
            print("❌ Final insert error:", e)
            print(tb)
            errors.append(("FINAL_INSERT", f"{e}\n{tb}"))

    cur.close()

    # Print summary
    if errors:
        print(f"⚠️ Completed with {len(errors)} errors. Examples:")
        for epath, emsg in errors[:10]:
            print(" -", epath, ":", emsg)
    else:
        print("🎯 All map_insurance_data JSON files loaded successfully")


def main():
    connection = get_sql_connection()
    create_tables(connection)
    

    # loading Aggregated_Transaction_Data
    load_json_from_paths(r"E:/Mr.D/Phonepay/Data/data/FilePaths_agg_trans.xlsx", ext_agg_trans,
                         "Aggregated_Transaction_Data",                         
                         ["Transaction_type","Transaction_count","Transaction_amount","State","Year","Quarter"])
    

    # loading Aggregated_user_Data
    load_json_from_paths(r"E:/Mr.D/Phonepay/Data/data/FilePaths_agg_user.xlsx", ext_agg_user,
                         "Aggregated_user_Data",
                         ["Brand","Count","State","Year","Quarter"])
    
    # loading Aggregated_Insurance_Data
    load_json_from_paths(r"E:/Mr.D/Phonepay/Data/data/FilePaths_agg_ins.xlsx", ext_agg_ins,
                         "Aggregated_Insurance_Data",
                         ["Transaction_count","Transaction_amount","State","Year","Quarter"])
    
    # loading map_transaction_data
    load_json_from_paths(r"E:/Mr.D/Phonepay/Data/data/FilePaths_map.xlsx", ext_map_trans,
                         "map_transaction_data",
                         ["District","Count","Amount","State","Year","Quarter"])
    
    # loading map_user_data

    load_json_from_paths(r"E:/Mr.D/Phonepay/Data/data/FilePaths_map_users.xlsx", ext_map_user,
                         "map_user_data",
                         ["District","registeredUsers","appOpens","State","Year","Quarter"])
    
    # loading top_user_data

    load_json_from_paths(r"E:/Mr.D/Phonepay/Data/data/FilePaths_top_users.xlsx", ext_top_user,
                         "top_user_data",
                         ["Name","registeredUsers","Level","State","Year","Quarter"])
    
    # loading top_transaction_data

    load_json_from_paths(r"E:/Mr.D/Phonepay/Data/data/FilePaths_top_trans.xlsx", ext_top_trans,
                         "top_transaction_data",
                         ["EntityName","registeredUsers","State","Year","Quarter"])
    
    # loading top_insurance_data

    load_json_from_paths(r"E:/Mr.D/Phonepay/Data/data/FilePaths_top_insurance.xlsx", ext_top_ins,
                         "top_insurance_data",
                         ["EntityName","TxnCount","TxnAmount","State","Year","Quarter"])
    
    # loading map_insurance_data
    
    load_data_Table_map_insurance(connection,r"E:/Mr.D/Phonepay/Data/data/FilePaths_map_insurance.xlsx")
    
   
    
    

    print("🎯 All data loading complete")
    connection.close()

if __name__ == "__main__":
        main()
