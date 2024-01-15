from src.sqlite.gov_db_utils import (
    get_deployed_llms,
    deploy_llm,
    activate_llm,
    deactivate_llm,
    delete_llm,
)
from src.basic_data_classes import LLM
from src.sqlite.db_creation import execute_query, get_row
from src.sqlite.db_creation import add_or_update_row


cache = {}


def test_deploy_llm():
    """test that we can deploy an llm"""
    # delete all llms names test_llm or test_llm_updated
    execute_query("DELETE FROM llms WHERE name LIKE 'test_llm%';")
    # create an llm object
    cache["llm"] = LLM(
        name="test_llm",
        api_type="openai",
        deployment="local",
        enpoint_or_base_url="https://api.openai.com/v1/engines/davinci/completions",
        api_key="sk-12345",
        description="test llm",
    )
    # deploy the llm
    deploy_llm(cache["llm"])
    assert cache["llm"] in get_deployed_llms()


def test_update_llm():
    """test that we can update an llm"""
    # update the llm
    cache["llm"].name = "test_llm_updated"
    add_or_update_row(cache["llm"])
    assert cache["llm"] in get_deployed_llms()


def test_activate_llm():
    """test that we can activate an llm"""
    # activate the llm
    activate_llm(cache["llm"].id)
    assert get_row(cache["llm"].id, "llms")[0]["is_active"] == "True"


def test_deactivate_llm():
    """test that we can deactivate an llm"""
    # deactivate the llm
    deactivate_llm(cache["llm"].id)
    assert get_row(cache["llm"].id, "llms")[0]["is_active"] == "False"


def test_delete_llm():
    """test that we can delete an llm"""
    # delete the llm
    delete_llm(cache["llm"])
    assert cache["llm"] not in get_deployed_llms()
