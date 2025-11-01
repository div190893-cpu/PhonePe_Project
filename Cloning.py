import git
repo_url = "https://github.com/PhonePe/pulse.git"
destination = "E:\\Mr.D\\Phonepay\\Data"
from git import Repo

Repo.clone_from(repo_url, destination)