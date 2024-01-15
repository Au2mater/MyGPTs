# db_creation.py
# Creation and backup of the main database for managing users, assistants, and sources
# Also contains functions for backing up vector db
import os
import sqlite3
from sqlite3 import Connection
import shutil
import datetime
from pathlib import Path
from src.basic_data_classes import GlobalSetting, LLM, Source, Assistant, User
from pydantic import BaseModel
from dotenv import load_dotenv

import logging

logging.basicConfig(
    level=logging.INFO,
    filename="sqlite.log",
    filemode="a",  # "a" stands for append, which means new log messages will be added to the end of the file instead of overwriting the existing conten
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Define the .env file path
env_path = Path(".") / ".env"

# Load the variables from the .env file into the environment
load_dotenv(dotenv_path=env_path)

# constants
data_classes = [GlobalSetting, Source, Assistant, User]
database_location = Path(
    os.environ.get("DATABASE_LOCATION", "data/db/myGPTs.db")
).resolve()
vector_db_location = Path(
    os.environ.get("VECTOR_DB_LOCATION", "data/vector_db")
).resolve()
backup_directory = Path(os.environ.get("BACKUP_DIRECTORY", "backup/db")).resolve()


def get_or_create_database(db_name) -> Connection:
    # Create the destination directory if it does not exist
    db_name.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn


def backup(sources: list | str):
    """
    :param sources: a list of file or directory paths to backup
    Backup the source (file or directory) to a file in {backup_directory}
    Returns the current datetime string used to name the backup files
    This will be used to backup the main database or the vector database
    """
    dsts = []
    # Current datetime
    current_datetime = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")
    logging.info(f"backup attempt started at {current_datetime}")

    for src in list(sources):
        # Source file path
        src_path = Path(src)

        # Destination file path
        dst = backup_directory / f"{src_path.stem}_{current_datetime}.bak"
        dsts.append(dst)

        # Check if the source file exists
        if not src_path.exists():
            # print(f'Source does not exist: {src_path}')
            logging.error(f"Source does not exist: {src_path}")
            return

        # Create the destination directory if it does not exist
        dst.parent.mkdir(exist_ok=True)

        # Copy the file or directory
        if src_path.is_file():
            shutil.copy2(src_path, dst)
            logging.info(f"File backed up to: {dst}")
        elif src_path.is_dir():
            shutil.copytree(src_path, dst)
            logging.info(f"Directory backed up to: {dst}")
        else:
            logging.error(
                f"Source {src_path} is neither a file nor a directory: {src_path}"
            )
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


def create_table_from_dict(conn: Connection, table: dict):
    """
    create named table if it does not exist

    :param conn: an sqlite connection object
    :param table: a dictionary containing the table name, fields, and primary key
        the fields are a list of dictionaries with the following keys with string values:
        Field, Type, NOT NULL, UNIQUE
    """
    cursor = conn.cursor()
    table_name = table["name"]
    fields = ", ".join(
        [" ".join([val for val in field.values()]) for field in table["fields"]]
    )
    primary_key = table["PRIMARY KEY"]
    print(f"CREATE TABLE {table_name} ({fields}) PRIMARY KEY ({primary_key}) ")
    cursor.execute(f"CREATE TABLE {table_name} ({fields})")
    conn.commit()


def create_table_from_dataclass(dataclass: BaseModel, table_name=None):
    """
    create a table in the database from a pydantic dataclass
    :param conn: an sqlite connection object
    :param dataclass: a pydantic dataclass
        id field is expected to exist in the dataclass is set to primary key
    :param table_name: (optional) the name of the table to create
    """
    conn = get_or_create_database(database_location)
    cursor = conn.cursor()
    if table_name is None:
        table_name = (dataclass.__name__ + "s").lower()
    # map pydantic data types to sqlite data types
    type_map = {
        "str": "TEXT",
        "int": "INTEGER",
        "float": "REAL",
        "bool": "INTEGER",
        "datetime": "TEXT",
    }
    fields = ", ".join(
        [
            f"{field} {type_map.get(dataclass.model_fields[field].annotation.__name__, 'TEXT')}"
            for field in dataclass.model_fields
            if field != "id"
        ]
    )
    query = f"CREATE TABLE {table_name} (id TEXT NOT NULL UNIQUE, {fields}, PRIMARY KEY (id))"
    print(query)
    cursor.execute(query)
    conn.commit()
    conn.close()
    logging.info(f"created table {table_name}")


# use table descriptions from src/sqlite/users_db.yaml to create the tables
def create_tables_from_dicts(conn, tables):
    for table in tables:
        create_table_from_dict(conn, table)


# use dataclasses to create the tables
def create_tables_from_dataclasses(dataclasses: list[BaseModel]):
    for dataclass in dataclasses:
        create_table_from_dataclass(dataclass)


def delete_table(table_name):
    conn = get_or_create_database(database_location)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE {table_name};")
    conn.commit()


def delete_tables(table_names: list[str]):
    """deletes the tables in the list table_names from the database"""
    # prompt user to confirm deletion of tables
    print(f"Are you sure you want to delete {table_names}?")
    response = input("Enter 'y' to confirm: ")
    if response != "y":
        return None
    for table in table_names:
        try:
            delete_table(table)
        #  capture exception and continue
        except Exception as e:
            print(f"Error deleting table {table}: {e}")
            pass


def reset_table_for_dataclass(dataclass: BaseModel):
    """reset a table for a dataclass"""
    table_name = (dataclass.__name__ + "s").lower()
    delete_table(table_name)
    create_table_from_dataclass(dataclass)


# get tables in the database
def get_table_names(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = [t[0] for t in cursor.fetchall()]
    return table_names


def get_table_columns(table_name: str) -> list:
    """get the columns of a table"""
    query = f"PRAGMA table_info({table_name})"
    columns = execute_query(query)
    return [column[1] for column in columns]


def migrate_table(from_table: str, to_table: str):
    """
    copy the contents of from_table to to_table
    the tables do not have to have the same schema
    only common columns are copied
    """
    query = f"""
    INSERT INTO {to_table} ({', '.join(get_table_columns(from_table))})
    SELECT {', '.join(get_table_columns(from_table))} FROM {from_table}
    """
    execute_query(query)


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


def initialize_database_from_dataclasses(dataclasses: list[BaseModel] = data_classes):
    """
    creates the main database for managing users, assistants, and sources
    backs up existing main database and vector database if any. After which existing vector database is deleted
    """
    # backup existing database if any
    backup([database_location, vector_db_location])
    delete_vector_db(vector_db_location)

    conn = get_or_create_database(database_location)  # create the database
    try:
        # check if database already exists
        table_names = get_table_names(conn)
        if len(table_names) > 0:
            delete_tables(table_names)

        for dataclass in dataclasses:
            create_table_from_dataclass(dataclass)
        conn.close()
    except Exception as e:
        print(e)
        conn.close()
        return


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


# data management functions


def insert_row(
    dataobject: Assistant | User | Source | LLM | GlobalSetting, table_name=None
):
    """
    given an object intialized from a pydantic dataclass,
    insert the row into the corresponding table
    the table must first be created from the dataclass using create_table_from_dataclass
    """
    conn = get_or_create_database(database_location)
    cursor = conn.cursor()
    if table_name is None:
        table_name = (type(dataobject).__name__ + "s").lower()
    fields = ", ".join(dataobject.model_fields.keys())
    values = dataobject.model_dump().values()
    # escape single quotes in values by replacing ' with ''
    values = [v.replace("'", "''") if isinstance(v, str) else v for v in values]
    values = ", ".join([f"'{v}'" for v in values])
    query = f"INSERT INTO {table_name} ({fields}) VALUES ({values})"
    cursor.execute(query)
    conn.commit()
    conn.close()
    logging.info(f"inserted row with id: {dataobject.id} into {table_name} table")


def add_or_update_row(
    dataobject: Assistant | User | Source | LLM | GlobalSetting, table_name=None
):
    """
    given an object intialized from a pydantic dataclass,
    insert the row into the corresponding table
    the table must first be created from the dataclass using create_table_from_dataclass
    """
    conn = get_or_create_database(database_location)
    cursor = conn.cursor()
    if table_name is None:
        table_name = (type(dataobject).__name__ + "s").lower()
    fields = ", ".join(dataobject.model_fields.keys())
    values = dataobject.model_dump().values()
    # escape single quotes in values by replacing ' with ''
    values = [v.replace("'", "''") if isinstance(v, str) else v for v in values]
    values = ", ".join([f"'{v}'" for v in values])
    query = f"REPLACE INTO {table_name} ({fields}) VALUES ({values})"
    cursor.execute(query)
    conn.commit()
    conn.close()
    logging.info(
        f"inserted or updated row with id: {dataobject.id} into {table_name} table"
    )


def get_row(id: str, table_name: str):
    """get a row from the given table with the given id"""
    query = f"SELECT * FROM {table_name} WHERE id='{id}';"
    result = execute_query(query)
    return result


def get_rows(table_name: str):
    """get all rows from the given table"""
    query = f"SELECT * FROM {table_name};"
    result = execute_query(query)
    return result


def results_to_data_objects(results: list, dataclass):
    """convert a result from a query to a data object"""
    objects = [dataclass(**dict(r)) for r in results]
    return objects


def delete_row(dataobject_or_id: object | str, table_name: str = None):
    """
    delete a row corresponding to a dataobject from the database
    dataclass must have an id field
    a table must exist for the dataclass
    """
    if isinstance(dataobject_or_id, str):
        id = dataobject_or_id
        if table_name is None:
            raise ValueError("table_name must be provided when id is provided")
    else:
        if table_name is None:
            # infer table name from dataclass
            table_name = (type(dataobject_or_id).__name__ + "s").lower()
        id = dataobject_or_id.id
    conn = get_or_create_database(database_location)
    cursor = conn.cursor()
    query = f"DELETE FROM {table_name} WHERE id='{id}';"
    cursor.execute(query)
    conn.commit()
    conn.close()
    logging.info(f"deleted row-id {id} from {table_name} table")


# testing


# def test_functions():
#     temp_db_location = Path("data/db/temp.db")
#     conn = get_or_create_database(temp_db_location)  # create the database
#     print(f"db successfully created at {temp_db_location}")
#     # test the functions

#     # read the database configuration from yaml file
#     db_config = yaml.safe_load(open("src/sqlite/users_db.yaml"))
#     tables = db_config["tables"]
#     test_table = tables[0]
#     print(test_table["name"])
#     create_table_from_dict(conn, test_table)
#     assert test_table["name"] in get_table_names(conn)
#     delete_table(test_table["name"])
#     assert test_table["name"] not in get_table_names(conn)

#     # create a table from a dataclass
#     create_table_from_dataclass(LLM)
#     assert "llms" in get_table_names(conn)
#     delete_table("llms")
#     assert "llms" not in get_table_names(conn)

#     # close the connection
#     conn.close()
#     # delete temp db
#     temp_db_location.unlink(missing_ok=True)


if __name__ == "__main__":
    print("")
    # test_functions()
    # initialize_database_from_dataclasses(data_classes)
    # initialize_database_from_yaml()  # automatically backs up existing database
    # bkp = backup([database_location, vector_db_location])
    # print(bkp)
    # recreate_db_from_backup("2024_01_12")
    # no_bkp = backup_directory / "myGPTs_does_not_exist.bak"
    # recreate_db_from_backup(no_bkp)
    # initialize_database_from_yaml()
    # # bkp = "backup/db/myGPTs_2024_01_09_16_50.bak"
    # recreate_db_from_backup(bkp)

    # create_table_from_dataclass(LLM)
    # create_table_from_dataclass(conn, Source, "sources_2")
    # # copy the contents of the sources table to the sources_2 table
    # migrate_table("sources", "sources_2")
    # # delete the sources table and rename the sources_2 table to sources
    # delete_table( "sources")
    # execute_query("ALTER TABLE sources_2 RENAME TO sources")

    # conn = get_or_create_database(database_location)
    # delete_table( "globalsettings")
    # create_table_from_dataclass(GlobalSetting)
