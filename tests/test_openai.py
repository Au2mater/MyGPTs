import os
from openai import AzureOpenAI, OpenAI
from src.openai.openai_utils import _test_llm_api, generate_response
from src.basic_data_classes import LLM
from src.sqlite.gov_db_utils import deploy_llm, delete_llm
from src.mock_api import _start_mockup_api, _test_llm
import subprocess
# {'id': FieldInfo(annotation=str, required=False, default_factory=<lambda>), 'name': FieldInfo(annotation=str, required=True), 'api_type': FieldInfo(annotation=Literal['azure', 'openai', 'localhost'], required=True), 'deployment': FieldInfo(annotation=str, required=False, default=''), 'enpoint_or_base_url': FieldInfo(annotation=str, required=True), 'api_key': FieldInfo(annotation=str, required=False, default='not-needed'), 'description': FieldInfo(annotation=str, required=False, default=''), 'is_active': FieldInfo(annotation=bool, required=False, default=True), 'created_at': FieldInfo(annotation=datetime, required=False, default_factory=builtin_function_or_method), 'updated_at': FieldInfo(annotation=datetime, required=False, default_factory=builtin_function_or_method)}




def test_test_model():
    p = _start_mockup_api()
    result, _ = _test_llm_api(_test_llm)
    subprocess.Popen.kill(p)
    assert result


