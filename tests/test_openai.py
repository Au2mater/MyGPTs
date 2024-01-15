import os
from openai import AzureOpenAI, OpenAI
from src.openai.openai_utils import test_llm, generate_response
from src.basic_data_classes import LLM
import subprocess
# {'id': FieldInfo(annotation=str, required=False, default_factory=<lambda>), 'name': FieldInfo(annotation=str, required=True), 'api_type': FieldInfo(annotation=Literal['azure', 'openai', 'localhost'], required=True), 'deployment': FieldInfo(annotation=str, required=False, default=''), 'enpoint_or_base_url': FieldInfo(annotation=str, required=True), 'api_key': FieldInfo(annotation=str, required=False, default='not-needed'), 'description': FieldInfo(annotation=str, required=False, default=''), 'is_active': FieldInfo(annotation=bool, required=False, default=True), 'created_at': FieldInfo(annotation=datetime, required=False, default_factory=builtin_function_or_method), 'updated_at': FieldInfo(annotation=datetime, required=False, default_factory=builtin_function_or_method)}

host = '10.10.1.13'
port = '8123'

def start_mockup_api():
    command = ['uvicorn', 'src.mock_api:app', '--host', host , '--port', port]
    p = subprocess.Popen(command)
    return p

def create_test_model():
    model = {
            'name': 'test_GPT',
            'api_type': 'openai',
            'enpoint_or_base_url': f'http://{host}:{port}',
            'api_key': 'not-relevant',
            'description': 'test model',
            'deployment': 'gpt-3.5-turbo',
            'is_active': True,
        }
    llm = LLM(**model)
    return llm

p = start_mockup_api()
llm = create_test_model()
# generate_response(prompt_input='test', llm=llm, max_tokens=10, temperature=0.5)
# test llm
test_llm(llm)
# NOW KILL THE SUBPROCESS
subprocess.Popen.kill(p)
