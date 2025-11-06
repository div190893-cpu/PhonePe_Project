import mysql.connector
__conn=None

def get_sql_connection():
    global __conn
    if __conn is None:
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="123456",
                port=3306
                        )
            if conn.is_connected():
                print("Connection successful!")
                return conn


        except mysql.connector.Error as err:
            print(f"Error: {err}")
    return __conn