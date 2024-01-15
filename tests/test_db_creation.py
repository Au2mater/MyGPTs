from src.sqlite.db_creation import (
    # database_location,
    # backup_directory,
    get_or_create_database,
    create_table_from_dataclass, 
    get_table_names, 
    delete_table,
    insert_row,
    get_rows,
    recreate_db_from_backup
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


time = '2024_01_15_14'
# bak_file_paths = list(backup_directory.glob(f"*{'vector_db'}_{time}*.bak")) 
recreate_db_from_backup(time)