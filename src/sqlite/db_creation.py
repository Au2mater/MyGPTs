# db_creation.py
# Creation and backup of the main database for managing users, assistants, and sources
# Also contains functions for backing up vector db

import sqlite3
import yaml
import shutil
import datetime
from pathlib import Path

# constants
database_location = Path("data/db/myGPTs.db")
vector_db_location = Path("data/vector_db")
backup_directory = Path("backup/db")

def get_or_create_database(db_name):
    # Create the destination directory if it does not exist
    db_name.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(db_name)
    return conn



def backup(sources: list| str):
    """
    Backup the source (file or directory) to a file in backup_directory
    Returns the backup file path
    This will be backup the main database or the vector database
    """
    dsts = []
    # Current datetime
    current_datetime = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")

    for src in list(sources):
        # Source file path
        src_path = Path(src)

        # Destination file path
        dst = backup_directory / f"{src_path.stem}_{current_datetime}.bak"
        dsts.append(dst)

        # Check if the source file exists
        if not src_path.exists():
            print(f"Source does not exist: {src_path}")
            return

        # Create the destination directory if it does not exist
        dst.parent.mkdir(exist_ok=True)

        # Copy the file or directory
        if src_path.is_file():
            shutil.copy2(src_path, dst)
            print(f"File backed up to: {dst}")
        elif src_path.is_dir():
            shutil.copytree(src_path, dst)
            print(f"Directory backed up to: {dst}")
        else:
            print(f"Source is neither a file nor a directory: {src_path}")
            return
    # return time string
    return current_datetime

def execute_query(query: str, fetchall=True):
    conn = get_or_create_database(database_location)
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    if fetchall:
        return cursor.fetchall()
    else:
        return cursor.fetchone()


def create_table(conn, table):
    """create named table if it does not exist"""
    cursor = conn.cursor()
    table_name = table["name"]
    fields = ", ".join(
        [" ".join([val for val in field.values()]) for field in table["fields"]]
    )
    primary_key = table["PRIMARY KEY"]
    print(f"CREATE TABLE {table_name} ({fields}) PRIMARY KEY ({primary_key}) ")
    cursor.execute(f"CREATE TABLE {table_name} ({fields})")
    conn.commit()


# use table descriptions from src/sqlite/users_db.yaml to create the tables
def create_tables(conn, tables):
    for table in tables:
        create_table(conn, table)


def delete_table(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE {table_name};")
    conn.commit()


# get tables in the database
def get_table_names(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = [t[0] for t in cursor.fetchall()]
    return table_names


def delete_tables(conn, table_names):
    """ deletes the tables in the list table_names from the database"""
    # prompt user to confirm deletion of tables
    print(f"Are you sure you want to delete {table_names}?")
    response = input("Enter 'y' to confirm: ")
    if response != "y":
        return None
    for table in table_names:
        try:
            delete_table(conn, table)
        #  capture exception and continue
        except:
            pass

def delete_vector_db(directory=vector_db_location):
    """delete the vector database"""
    # check if the vector database exists
    if directory.exists():
        print(f"Are you sure you want to delete {directory}?")
        response = input("Enter 'y' to confirm: ")
        if response != "y":
            return None
    shutil.rmtree(directory, ignore_errors=True)
    print(f"Deleted vector database: {directory}")



def initialize_database():
    """
    creates the main database for managing users, assistants, and sources
    backs up existing main database and vector database if any. After which existing vector database is deleted
    """
    # backup existing database if any
    backup([database_location, vector_db_location])
    delete_vector_db(vector_db_location)
    # read the database configuration from yaml file
    db_config = yaml.safe_load(open("src/sqlite/users_db.yaml"))
    tables = db_config["tables"]
    print(f"{len(tables)} table schemas found")
    conn = get_or_create_database(database_location)  # create the database
    # check if database already exists
    table_names = get_table_names(conn)
    if len(table_names) > 0:
        delete_tables(conn, table_names)

    create_tables(conn, tables)  # create the tables in the database


def recreate_db_from_backup(time: str):
    """
    recreate the main and vector database from a backup file and directory
    :param time: the time of the backup file to use 
        can be a string or a datetime object
        if string, it should be in the format: %Y_%m_%d_%H_%M or %Y_%m_%d_%H or %Y_%m_%d
        if hour or minute is not provided, the latest backup file for that day will be used 
    backups are located in backup_directory
    main db backup files have the format: myGPTs_%Y_%m_%d_%H_%M.bak
    vector db backup directories have the format: vector_db_%Y_%m_%d_%H_%M.bak
    """
    # convert datetime object to string
    if isinstance(time, datetime.datetime):
        time = time.strftime("%Y_%m_%d_%H_%M")
    prefixes = ["myGPTs", "vector_db"]
    bak_files = []
    for prefix in prefixes:
        # check for filenames in backup_directory containing the time string
        bak_file_paths = list(backup_directory.glob(f"*{prefix}_{time}*.bak"))
        # check if there are any backup files
        if len(bak_file_paths) < 2:
            print(f"No backup files found for {time}")
            return
        # get the latest backup file for both main and vector database
        print(f"Found backup files for {prefix}")
        bak_file_paths = sorted(bak_file_paths)
        bak_file_path = bak_file_paths[-1]
        bak_files.append(bak_file_path)

    # delete the database file if it exists
    database_location.unlink(missing_ok=True)
    print(f"Deleted database: {database_location}")
    # delete the vector database if it exists
    delete_vector_db(vector_db_location)
    # copy the backup file to the database file path
    shutil.copy2(bak_files[0], database_location)
    print(f"Database recreated from backup: {bak_files[1]}")
    # copy the backup directory to the vector database directory
    shutil.copytree(bak_files[1], vector_db_location)
    print(f"Vector database recreated from backup: {bak_files[1]}")




def test_functions():
    # read the database configuration from yaml file
    db_config = yaml.safe_load(open("src/sqlite/users_db.yaml"))

    tables = db_config["tables"]
    conn = get_or_create_database(database_location)  # create the database

    # test the functions
    test_table = tables[0]
    print(test_table["name"])
    create_table(conn, test_table)
    assert test_table["name"] in get_table_names(conn)
    delete_table(conn, test_table["name"])
    assert test_table["name"] not in get_table_names(conn)



if __name__ == "__main__":
    # test_functions()
    initialize_database() # automatically backs up existing database
    bkp = backup([database_location, vector_db_location]) ; print(bkp)
    recreate_db_from_backup("2024_01_09_18")
    no_bkp = backup_directory / "myGPTs_does_not_exist.bak"
    recreate_db_from_backup(no_bkp)
    initialize_database()
    # bkp = "backup/db/myGPTs_2024_01_09_16_50.bak"
    recreate_db_from_backup(bkp)
