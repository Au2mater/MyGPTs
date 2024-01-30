from src.openai_utils import llm_api_test , generate_response
from src.mock_api import _start_mockup_api, _test_llm
import subprocess
import pytest
# {'id': FieldInfo(annotation=str, required=False, default_factory=<lambda>), 'name': FieldInfo(annotation=str, required=True), 'api_type': FieldInfo(annotation=Literal['azure', 'openai', 'localhost'], required=True), 'deployment': FieldInfo(annotation=str, required=False, default=''), 'enpoint_or_base_url': FieldInfo(annotation=str, required=True), 'api_key': FieldInfo(annotation=str, required=False, default='not-needed'), 'description': FieldInfo(annotation=str, required=False, default=''), 'is_active': FieldInfo(annotation=bool, required=False, default=True), 'created_at': FieldInfo(annotation=datetime, required=False, default_factory=builtin_function_or_method), 'updated_at': FieldInfo(annotation=datetime, required=False, default_factory=builtin_function_or_method)}

@pytest.fixture(scope="module", autouse=True)
def testLLM():
    p = _start_mockup_api()

    yield _test_llm

    subprocess.Popen.kill(p)



def test_test_model(testLLM):
    """test connecting to the mockup API and generating a response."""
    result, _ = llm_api_test(testLLM)
    assert result

def test_special_characters_prompt(testLLM):
    """test making a request with special characters in the prompt."""
    prompt = """
    - test 1
    - test 2
    """
    result = generate_response(prompt_input=prompt, llm=testLLM)
    assert result
