""" utilties for sqlite """
from datetime import datetime
from src.sqlite.db_creation import execute_query
from src.chroma.chroma_utils import (
    start_chroma_client,
    get_or_create_collection,
    delete_collection,
    Source,
    create_source,
    index_source,
    remove_source,
)
from pydantic import BaseModel, Field
import yaml
from uuid import uuid4


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
    columns = ", ".join(k for k in src.model_dump().keys())
    # string values where single quotes and backslashes are removed
    values = "', '".join(
        [str(v).replace("'", "").replace("\\", "") for k, v in src.model_dump().items()]
    )
    # print(query)
    execute_query(
        f"""
        REPLACE INTO sources ({columns})
        VALUES ('{values}');
    """
    )


def delete_source(source):
    """remove source from chroma and delete from sources table"""
    # remove source from chroma
    remove_source(source)
    # delete source from sources table
    source_id = source.id
    execute_query(f"DELETE FROM sources WHERE id='{source_id}';")


def delete_all_sources():
    """delete all sources from the sources table"""
    execute_query("DELETE FROM sources;")


# ------------------------
# 1- assistant level operations
# each assistant has one owner indicated in the owner_id field
# create an assistant data class that correponds to a row in the assistants table
class Assistant(BaseModel):
    """data class for an assistant"""

    id: str = Field(default_factory=lambda: uuid4().hex)
    # is also the name of the assistant's collection in chroma
    name: str = Field(min_length=1, max_length=30)
    # must correspond to one of the models in config/LLMS.yaml
    # this ensures that each assistant has a one unique collection
    _LLM_config = yaml.safe_load(open("config/LLMs.yaml", encoding="utf-8"))
    chat_model_name: str = Field(
        min_length=1,
        default=list(_LLM_config["models"].keys())[0],
    )
    system_prompt: str = Field(
        min_length=15,
        default=_LLM_config["global_settings"]["default_system_prompt"],
    )
    welcome_message: str = Field(
        min_length=3,
        default=_LLM_config["global_settings"]["default_welcome_message"],
    )
    creation_time: datetime = datetime.now()
    last_updated: datetime = datetime.now()
    owner_id: str = Field(min_length=1, max_length=30)


# a function to add an assistant to the database
def add_or_update_assistant(assistant: Assistant):
    """add an assistant to the database or update if it already exists
    this also creates a collection for the assistant if it does not exist
    """
    # update the assistant
    assistant.last_updated = datetime.now()
    columns = ", ".join(k for k in assistant.model_dump().keys())
    values = ", ".join([f"'{v}'" for k, v in assistant.model_dump().items()])
    execute_query(
        f"""
        REPLACE INTO assistants ({columns})
        VALUES ({values});
    """
    )
    # create the collection
    get_or_create_collection(assistant.id)
    print(f"Updated assistant {assistant.id}")


def get_assistant(assistant_id):
    """get an assistant from the database"""
    assistant = execute_query(f"SELECT * FROM assistants WHERE id='{assistant_id}';")
    assistant = Assistant(
        **dict(zip(list(Assistant.model_fields.keys()), assistant[0]))
    )
    return assistant


def get_assistant_sources(assistant_id):
    """get all sources for an assistant"""
    sources = execute_query(
        f"SELECT * FROM sources WHERE collection_name_and_assistant_id='{assistant_id}';"
    )
    sources = [
        Source(**dict(zip(list(Source.model_fields.keys()), s))) for s in sources
    ]
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


def add_or_get_user(user_id):
    """add a user to the database if it does not exist"""

    creation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_query(
        f" INSERT OR IGNORE INTO users (id, creation_datetime) VALUES ('{user_id}', '{creation_time}');",
        fetchall=False,
    )
    print(f"User {user_id} initialized")
    return user_id


def delete_user(user_id, and_assistants=True):
    """delete a user from the database"""
    if and_assistants:
        assistants = get_user_assistants(user_id)
        for assistant in assistants:
            delete_assistant(assistant.id)
    # delete the user
    execute_query(f"DELETE FROM users WHERE id='{user_id}';")


def get_user_assistants(user_id):
    """get all assistants for a user"""
    assistants = execute_query(f"SELECT * FROM assistants WHERE owner_id='{user_id}';")
    assistants = [
        Assistant(**dict(zip(list(Assistant.model_fields.keys()), a)))
        for a in assistants
    ]
    return assistants


# ------------------------
# test the functions

if __name__ == "__main__":
    # test the function
    username = "test_user"
    delete_user(username)
    add_or_get_user(username)
    assert "test_user" in [u[0] for u in execute_query("SELECT id FROM users;")]
    a = Assistant(name="Jazzmin", owner_id=username)
    print(a)
    add_or_update_assistant(assistant=a)
    a.name = "Jazzmin2"
    add_or_update_assistant(assistant=a)
    assert "Jazzmin2" in [a.name for a in get_user_assistants(username)]
    b = get_user_assistants(username)[0]
    b.name = "Jazzmin3"
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
