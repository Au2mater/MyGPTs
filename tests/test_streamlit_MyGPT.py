from streamlit.testing.v1 import AppTest
from src.basic_data_classes import User, Assistant
from src.chroma_utils import start_chroma_server
from src.sqlite.db_creation import execute_query
from src.sqlite.gov_db_utils import deploy_llm, delete_llm
from src.mock_api import _start_mockup_api, _test_llm


def clean_up():
    execute_query("DELETE FROM users WHERE id LIKE 'test_%';")


def init_myassistants():
    at = AppTest.from_file("app/MyGPTs.py", default_timeout=30.0)
    # simulate session initialization
    start_chroma_server()
    at.session_state["user"] = User(id="test_user_id", username="test_user")
    at.session_state["page"] = "my assistants"
    at.session_state["online"] = True
    return at


def test_MyGPT_startup():
    """Test that the app starts up correctly."""
    at = init_myassistants()
    at = at.run()
    assert not at.exception
    clean_up()


def test_assistant_creation():
    at = init_myassistants()
    at = at.run()
    bt = [bt for bt in at.get("button") if bt.key == "create_assistant"][0]
    bt.click().run()
    assert not at.exception
    clean_up()


def init_chat():
    at = AppTest.from_file("app/MyGPTs.py", default_timeout=30.0)
    # simulate session initialization
    start_chroma_server()
    test_user = User(id="test_user_id", username="test_user")
    test_assistant = Assistant(
        id="test_assistant_id",
        name="test_assistant",
        chat_model_name=_test_llm.id,
        system_prompt="You are a helpful assistant.",
        welcome_message="Hej, hvordan kan jeg hjælpe dig?",
        is_active=True,
        owner_id=test_user.id,
    )
    at.session_state["online"] = True
    at.session_state["user"] = test_user
    at.session_state["current_assistant"] = test_assistant
    at.session_state["page"] = "chat"
    at.session_state["messages"] = (
        [
            {"role": "system", "content": test_assistant.system_prompt},
            {"role": "assistant", "content": test_assistant.welcome_message},
        ],
    )
    at.session_state["number_of_sources"] = 0
    return at


def test_chat_startup():
    at = init_chat()
    at = at.run()
    assert not at.exception
    clean_up()


def test_chat():
    # # let's deploy a test assistant
    deploy_llm(_test_llm)
    # # let's start the mock api
    p = _start_mockup_api()
    # # let's start the app
    try:
        at = init_chat()
        at = at.run()
        # let's submit a message in chat_input
        print(at.get("chat_input"))
        at.get("chat_input")[0].set_value("This is a test!").run()
    except Exception as e:
        print(e)
        raise e
    finally:
        # let's clean up
        delete_llm(_test_llm)
        p.terminate()
        clean_up()
