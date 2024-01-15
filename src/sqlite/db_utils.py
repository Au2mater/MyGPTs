""" utilties for sqlite """
from datetime import datetime
from src.sqlite.db_creation import (
    execute_query,
    insert_row,
    delete_row,
    add_or_update_row,
    get_row,
    results_to_data_objects,
)
from src.chroma.chroma_utils import (
    start_chroma_client,
    get_or_create_collection,
    delete_collection,
    create_source,
    index_source,
    remove_source,
)
from src.basic_data_classes import Assistant, User, Source, LLM
import logging

logging.basicConfig(
    level=logging.INFO,
    filename="sqlite.log",
    filemode="a",  # "a" stands for append, which means new log messages will be added to the end of the file instead of overwriting the existing conten
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


# llm level operations
def get_active_llms():
    """get all llms from the database where is_active is True"""
    results = execute_query("SELECT * FROM llms WHERE is_active='True';")
    # sort results by name key
    results = sorted(results, key=lambda x: x["name"])
    llms = results_to_data_objects(results, LLM)
    return llms


def get_base_url():
    """get the base url for the llm"""
    return execute_query("SELECT * FROM globalsettings WHERE id='base_url';")[0][1]


# ------------------------
# 1 - source level operations
# each source belongs to one assistant indicated in the assistant_id field


def add_source(source):
    """index source to chroma and add sources table"""
    # index source to chroma
    index_source(source)
    # add source to sources table
    src = source.model_copy()
    src.content = src.content.strip()[:500]
    insert_row(src)


def delete_source(source):
    """remove source from chroma and delete from sources table"""
    # remove source from chroma
    remove_source(source)
    # delete source from sources table
    delete_row(source)


# ------------------------
# 1- assistant level operations
# a function to add an assistant to the database


def add_or_update_assistant(assistant: Assistant):
    """add an assistant to the database or update if it already exists
    this also creates a collection for the assistant if it does not exist
    """
    # update the assistant
    assistant.last_updated = datetime.now()
    add_or_update_row(assistant)
    # create the collection for the assistant in the vector database
    get_or_create_collection(assistant.id)
    print(f"Updated assistant {assistant.id}")


def get_assistant(assistant_id):
    """get an assistant from the database"""
    assistant_row = get_row(assistant_id, "assistants")
    assistant = results_to_data_objects(assistant_row, Assistant)
    if len(assistant) == 1:
        return assistant[0]


def get_assistant_sources(assistant_id):
    """get all sources for an assistant"""
    source_rows = execute_query(
        f"SELECT * FROM sources WHERE collection_name_and_assistant_id='{assistant_id}';"
    )
    sources = results_to_data_objects(source_rows, Source)
    return sources


def delete_assistant(assistant_id):
    """delete an assistant from the database"""
    execute_query(f"DELETE FROM assistants WHERE id='{assistant_id}';")
    # delete the collection
    delete_collection(assistant_id)
    # delete the sources using collection_name_and_assistant_id column in sources table
    execute_query(
        f"DELETE FROM sources WHERE collection_name_and_assistant_id='{assistant_id}';"
    )
    print(f"Deleted assistant {assistant_id}")


def get_assistant_collection(assistant_id):
    """get the collection for an assistant"""
    client = start_chroma_client()
    collection = client.get_collection(name=assistant_id)
    return collection


# ------------------------
# 1 - user operations


def add_or_get_user(user: User | dict):
    """add a user to the database if it does not exist"""

    if isinstance(user, dict):
        user = User(**user)
    elif not type(user) == User:
        raise ValueError("user must be a User class or a dict")
    found_user = execute_query(f"SELECT * FROM users WHERE id='{user.id}';")
    if len(found_user) == 1:
        print(f"User {found_user[0][0]} fetched")
        # currently user are missing email, username, and passwords
        # to avoid validation problems (e-mail), we will remove empty fields
        user_dict = {k: v for k, v in dict(found_user[0]).items() if v != ""}
        user = User(**user_dict)
        return user

    columns = ", ".join(k for k in user.model_dump().keys())
    values = ", ".join([f"'{v}'" for k, v in user.model_dump().items()])
    execute_query(
        f" INSERT OR IGNORE INTO users ({columns}) VALUES ({values});",
        fetchall=False,
    )
    print(f"User {user.id} created")
    return user


def update_user(user: User | dict):
    """update a user in the database"""
    if isinstance(user, dict):
        user = User(**user)
    elif not type(user) == User:
        raise ValueError("user must be a User class or a dict")
    add_or_update_row(user)


def delete_user(user: User | dict, and_assistants=True):
    """delete a user from the database"""
    if isinstance(user, dict):
        user = User(**user)
    elif not type(user) == User:
        raise ValueError("user must be a User class or a dict")
    if and_assistants:
        assistants = get_user_assistants(user)
        for assistant in assistants:
            delete_assistant(assistant.id)
    # delete the user
    execute_query(f"DELETE FROM users WHERE id='{user.id}';")


def get_user_assistants(user: User | dict):
    """get all assistants for a user"""
    if isinstance(user, dict):
        user = User(**user)
    elif not type(user) == User:
        raise ValueError("user must be a User class or a dict")
    assistants = execute_query(f"SELECT * FROM assistants WHERE owner_id='{user.id}';")
    assistants = [Assistant(**a) for a in assistants]
    # sort by creation_time
    assistants = sorted(assistants, key=lambda x: x.creation_time)
    return assistants


# ------------------------
# test the functions

if __name__ == "__main__":
    # test the function
    username = "test_user"
    test_user = User(id=username, username=username)
    test_user
    delete_user(test_user)
    add_or_get_user(test_user)
    assert "test_user" in [u[0] for u in execute_query("SELECT id FROM users;")]
    a = Assistant(name="Test", owner_id=username)
    print(a)
    add_or_update_assistant(assistant=a)
    a.name = "Test2"
    add_or_update_assistant(assistant=a)
    assert "Test2" in [a.name for a in get_user_assistants(username)]
    b = get_user_assistants(test_user)[0]
    b.name = "Test3"
    add_or_update_assistant(assistant=b)
    test_source = create_source(
        "https://jazznyt.blogspot.com"
        "/2024/01/sren-bebe-trio-here-now-from-out-here.html",
        c_a_id=b.id,
    )
    print(test_source)
    add_source(test_source)
    print(b)
    delete_assistant(b.id)
    delete_user(username, and_assistants=True)

    get_assistant("05e32b2dc80444aeab0032605423966b")

    get_assistant_sources("05e32b2dc80444aeab0032605423966b")
