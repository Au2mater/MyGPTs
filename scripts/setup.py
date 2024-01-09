
import os
import sys
if (
    path := os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
) not in sys.path:
    sys.path.append(path)
from src.sqlite.db_creation import initialize_database
# make sure the import above works when running python scripts\setup.py

if __name__ == "__main__":
    # 1- chack to see if a database already exists in data/db/myGPTs.db
    # 2- if it does, create a backup of the database in data/db/myGPTs.db.bak
    initialize_database()
