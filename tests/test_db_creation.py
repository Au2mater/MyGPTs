from src.sqlite.db_creation import (
    get_or_create_database,
    create_table_from_dataclass,
    get_table_names,
    delete_table,
    insert_row,
    execute_query
)
from pathlib import Path
from pydantic import BaseModel
import pytest
import os
import dotenv as de
import tempfile
import sqlite3

@pytest.fixture(scope="module", autouse=True)
def connection():
    """ create a test database and connect to it"""
    env_path = Path(".") / ".env"
    de.load_dotenv(dotenv_path=env_path)
    old_value = os.environ["MAIN_DATABASE_LOCATION"]

    # change main database location to a test database in temp folder (ensure it works on windows and linux)
    test_db_location = Path(tempfile.TemporaryDirectory().name) / "test.db"
    os.environ["MAIN_DATABASE_LOCATION"] = str(test_db_location)
    # create the database file
    test_db_location.parent.mkdir(parents=True, exist_ok=True)

    print(f"test db location: {test_db_location}")
    with sqlite3.connect(str(test_db_location)) as conn:
        conn.row_factory = sqlite3.Row
        yield conn  
        
    # reset the database location
    os.environ["MAIN_DATABASE_LOCATION"] = old_value



@pytest.fixture
def data_class():
    class TestClass(BaseModel):
        id: str
        name: str
        age: int

    return TestClass

def test_create_table_from_dataclass(connection, data_class):
    # start with a clean slate, delete the table if it exists
    execute_query("DROP TABLE IF EXISTS testclasss")
    create_table_from_dataclass(data_class)
    table_names = get_table_names(connection)
    print(table_names)
    assert "testclasss" in table_names


def test_insert_row(connection, data_class):
    testobject = data_class(id="test1", name="testname", age=12)
    insert_row(testobject)
    results = connection.execute("SELECT * FROM testclasss").fetchall()
    assert len(results) == 1


def test_delete_table(connection):
    delete_table(
        "testclasss",
    )
    table_names = get_table_names(connection)
    assert "testclasss" not in table_names

