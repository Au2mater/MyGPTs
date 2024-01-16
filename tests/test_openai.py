from src.openai.openai_utils import llm_api_test
from src.mock_api import _start_mockup_api, _test_llm
import subprocess
# {'id': FieldInfo(annotation=str, required=False, default_factory=<lambda>), 'name': FieldInfo(annotation=str, required=True), 'api_type': FieldInfo(annotation=Literal['azure', 'openai', 'localhost'], required=True), 'deployment': FieldInfo(annotation=str, required=False, default=''), 'enpoint_or_base_url': FieldInfo(annotation=str, required=True), 'api_key': FieldInfo(annotation=str, required=False, default='not-needed'), 'description': FieldInfo(annotation=str, required=False, default=''), 'is_active': FieldInfo(annotation=bool, required=False, default=True), 'created_at': FieldInfo(annotation=datetime, required=False, default_factory=builtin_function_or_method), 'updated_at': FieldInfo(annotation=datetime, required=False, default_factory=builtin_function_or_method)}


def test_test_model():
    p = _start_mockup_api()
    result, _ = llm_api_test(_test_llm)
    subprocess.Popen.kill(p)
    assert result
