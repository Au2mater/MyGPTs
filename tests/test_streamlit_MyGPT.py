from streamlit.testing.v1 import AppTest
from src.basic_data_classes import User
from src.chroma.chroma_utils import start_chroma_server
from src.sqlite.db_utils import add_or_get_user, add_or_update_assistant
from src.sqlite.db_creation import execute_query


def clean_up():
    execute_query("DELETE FROM users WHERE id LIKE 'test_%';")


def init_MyGPT():
    at = AppTest.from_file("app/MyGPTs.py", default_timeout=30.0)
    # simulate session initialization
    start_chroma_server()
    at.session_state["user"] = add_or_get_user(
        User(id="test_user_id", username="test_user")
    )
    at.session_state["page"] = "my assistants"
    at.session_state["online"] = True
    return at


def test_MyGPT_startup():
    """Test that the app starts up correctly."""
    at = init_MyGPT()
    at = at.run()
    assert not at.exception
    clean_up()


def test_assistant_creation():
    at = init_MyGPT()
    at = at.run()
    bt = [bt for bt in at.get("button") if bt.key == "create_assistant"][0]
    bt.click().run()
    assert not at.exception
    clean_up()


def test_chat():
    # let's deploy a test assistant
    
    at = init_MyGPT()
    at = at.run()
    bt = [bt for bt in at.get("button") if bt.key == "create_assistant"][0]
    bt.click().run()
    bt = [bt for bt in at.get("button") if bt.key == "ny_samtale"][0]
    bt.click().run()
    assert not at.exception
    clean_up()

test_assistant_creation()

# test_MyGPT_startup()
