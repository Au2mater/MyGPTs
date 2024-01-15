from src.sqlite.db_creation import (
    database_location,
    backup_directory,
    get_or_create_database,
    create_table_from_dataclass, 
    get_table_names, 
    delete_table,
    insert_row,
    get_rows,
    recreate_db_from_backup,
    execute_query,
    )
from pydantic import BaseModel

conn = get_or_create_database(database_location)

def create_test_class():
    class TestClass(BaseModel):
        id : str
        name: str
        age: int
    return TestClass


def test_create_table_from_dataclass():
    # start with a clean slate, delete the table if it exists
    execute_query('DROP TABLE IF EXISTS testclasss')
    create_table_from_dataclass(create_test_class())
    table_names = get_table_names(conn)
    assert 'testclasss' in table_names

def test_insert_row():
    testobject = create_test_class()(id='test1', name='testname', age=12)
    insert_row(testobject)
    results = conn.execute('SELECT * FROM testclasss').fetchall()
    assert len(results) == 1

def test_delete_table():
    delete_table('testclasss', )
    table_names = get_table_names(conn)
    assert 'testclasss' not in table_names