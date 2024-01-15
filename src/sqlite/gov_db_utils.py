"""gov utilties for sqlite """
from src.sqlite.db_creation import (
    execute_query,
    add_or_update_row,
    get_row,
    get_rows,
    delete_row,
    results_to_data_objects,
)
from src.basic_data_classes import LLM, GlobalSetting, Assistant
from datetime import datetime


# ------------------------
# 1 - LLM model level operations

# llm object schema:
# LLM = {
#     "name": str,
#     "api_type": str,
#     "deployment": str,
#     "base_url": str,
#     "api_key": str,
#     "description": str,
#     "is_active": bool,
#     "updated_at": datetime,
#     "created_at": datetime,
# }


def get_deployed_llms():
    """get all llms from the database"""
    results = get_rows("llms")
    # sort reults by name key
    results = sorted(results, key=lambda x: x["name"])
    llms = results_to_data_objects(results, LLM)
    return llms


def deploy_llm(llm: LLM):
    """add an llm to the database or update if it already exists"""
    # add llm to llms table
    add_or_update_row(llm)


def activate_llm(llm_id: str):
    """activate an llm"""
    llm = get_row(llm_id, "llms")
    if len(llm) == 1:
        llm = LLM(**llm[0])  # convert to LLM object
        llm.is_active = True
        add_or_update_row(llm)
    else:
        raise Exception("llm not found")


def deactivate_llm(llm_id: str):
    """deactivate an llm"""
    llm = get_row(llm_id, "llms")
    if len(llm) == 1:
        llm = LLM(**llm[0])
        llm.is_active = False
        add_or_update_row(llm)
    else:
        raise Exception("llm not found")


def delete_llm(llm_or_id: LLM | str):
    """remove llm from llms table"""
    delete_row(llm_or_id)


# ------------------------
# Global Settings level operations

# global setting object schema:
# GlobalSetting = {
#     "id": str,
#     "value": str,
#     "default_value": str,
#     "type": str,
#     "last_updated": datetime,
# }


def get_global_setting(setting_id: str) -> GlobalSetting:
    """get a global setting from the database"""
    result = get_row(setting_id, "globalsettings")
    setting = results_to_data_objects(result, GlobalSetting)[0]
    # using setting.type convert setting.value to proper type

    return setting


def get_global_settings() -> list[GlobalSetting]:
    """get all llms from the database"""
    result = get_rows("globalsettings")
    settings = results_to_data_objects(result, GlobalSetting)
    return settings


def get_global_setting_dicts() -> dict[dict]:
    # covert each setting to dict
    setting_dicts = [setting.model_dump() for setting in get_global_settings()]
    # convert setting.value to proper type based on setting.type, type is a string ['int', 'str', 'bool', 'float']
    for setting in setting_dicts:
        if setting["type"] == "int":
            setting["value"] = int(setting["value"])
            setting["default_value"] = int(setting["default_value"])
        elif setting["type"] == "float":
            setting["value"] = float(setting["value"])
            setting["default_value"] = float(setting["default_value"])
        elif setting["type"] == "bool":
            setting["value"] = bool(setting["value"])
            setting["default_value"] = bool(setting["default_value"])
    global_settings = {setting["id"]: setting for setting in setting_dicts}
    return global_settings


def set_global_setting(global_setting: GlobalSetting | dict):
    """update global settings"""
    if isinstance(global_setting, dict):
        global_setting = GlobalSetting(**global_setting)
    global_setting.last_updated = datetime.now()
    add_or_update_row(global_setting)


def reset_global_setting(setting_id: str):
    """reset global settings to default"""
    # set value to default_value
    setting = get_global_setting(setting_id)
    setting.value = setting.default_value
    set_global_setting(setting)
    return setting


def reset_all_global_settings():
    """reset all global settings to default"""
    query = "UPDATE globalsettings SET value=default_value;"
    execute_query(query)


# ------------------------
# 1 - assistant level operations
def get_all_assistants():
    """get all assistants from the database"""
    results = get_rows("assistants")
    assistants = results_to_data_objects(results, Assistant)
    return assistants
