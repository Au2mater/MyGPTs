from src.basic_data_classes import Assistant, User, Source
from src.sqlite.db_utils import (
    add_or_get_user,
    delete_user,
    update_user,
    add_or_update_assistant,
    get_assistant,
    get_user_assistants,
    delete_assistant,
    add_source,
    delete_source,
)
from src.chroma.chroma_utils import start_chroma_server
from src.sqlite.db_creation import get_row, delete_row, execute_query


# for each data class we are going to test the following:
# 1 - add a row
# 2 - get a row
# 3 - get all rows
# 4 - update a row
# 5 - delete a row

cache = {}
# ------------------------
# 1 - user level operations


def test_user_creation():
    # delete all user ids ids starting with test_
    execute_query("DELETE FROM users WHERE id LIKE 'test_%';")
    cache["test_user"] = User(username="test_user", id="test_user_id")
    delete_user(cache["test_user"])
    assert add_or_get_user(cache["test_user"]) == cache["test_user"]


def test_user_update():
    cache["test_user"].username = "test_user_updated"
    update_user(cache["test_user"])
    assert add_or_get_user(cache["test_user"]) == cache["test_user"]


def test_user_deletion():
    delete_user(cache["test_user"])
    assert get_row(cache["test_user"].id, "users") == []


# ------------------------
# 1 - assistant level operations
def test_assistant_creation():
    cache["test_assistant"] = Assistant(
        name="test assistant",
        owner_id=cache["test_user"].id,
        chat_model_name="test_chat_model_name",
        system_prompt="test_system_prompt",
        welcome_message="test_welcome_message",
    )
    delete_row(cache["test_assistant"], "assistants")
    start_chroma_server()  # necessary for the assistant to be created
    add_or_update_assistant(cache["test_assistant"])
    assert get_assistant(cache["test_assistant"].id) == cache["test_assistant"]


def test_update_assistant():
    cache["test_assistant"].name = "test_assistant_updated"
    add_or_update_assistant(cache["test_assistant"])
    assert get_assistant(cache["test_assistant"].id) == cache["test_assistant"]


def test_get_assistant_from_user():
    assert get_user_assistants(cache["test_user"]) == [cache["test_assistant"]]


def test_assistant_deletion():
    delete_assistant(cache["test_assistant"].id)
    assert get_assistant(cache["test_assistant"].id) is None


# ------------------------
# 1 - source level operations
def test_source_creation():
    start_chroma_server()  # necessary for the source to be created
    cache["test_source"] = Source(
        name="test_source",
        source_type="url",
        content="test_content",
        content_type="txt",
        collection_name_and_assistant_id="test_collection_name_and_assistant_id",
    )
    add_source(cache["test_source"])
    assert (
        Source(**get_row(cache["test_source"].id, "sources")[0]) == cache["test_source"]
    )


def test_source_deletion():
    delete_source(cache["test_source"])
    assert get_row(cache["test_source"].id, "sources") == []


# ------------------------
