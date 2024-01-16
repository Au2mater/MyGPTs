""" a mock rest api that accepts any request and returns a response with a 200 status code"""
# to start server:
# cd src
# uvicorn mock_api:app --reload --host 10.10.1.13 --port 8123
# to test externally:
# curl http://10.10.1.13:8123/
# curl http://10.10.1.13:8123/chat/completions
'''
curl http://10.10.1.13:8123/chat/completions ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer $OPENAI_API_KEY" ^
  -d '{^
     "model": "gpt-3.5-turbo",^
     "messages": [{"role": "user", "content": "Say this is a test!"}],^
     "temperature": 0.7,^
   }'
'''
from fastapi import FastAPI
from pydantic import BaseModel
from src.basic_data_classes import LLM
import subprocess
import uvicorn


# ---------------------
# UTILTIY FUNCTIONS
host = '10.10.1.13'
port = '8123'

def _start_mockup_api():
    command = ['uvicorn', 'src.mock_api:app', '--host', host , '--port', port]
    p = subprocess.Popen(command)
    return p

_test_llm = LLM(**{
            'name': 'test_GPT',
            'api_type': 'openai',
            'enpoint_or_base_url': f'http://{host}:{port}',
            'api_key': 'not-relevant',
            'description': 'test model',
            'deployment': 'gpt-3.5-turbo',
            'is_active': True,
        })

#----------------------



# Create the FastAPI app
app = FastAPI()

# this api will accept any request and return a the responsebelow  with a 200 status code
response = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1677858242,
    "model": "gpt-3.5-turbo-1106",
    "usage": {
        "prompt_tokens": 13,
        "completion_tokens": 7,
        "total_tokens": 20
    },
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "\n\nThis is a test!"
            },
            "logprobs": 'null',
            "finish_reason": "stop",
            "index": 0
        }
    ]
}

class Data(BaseModel):
    model: str
    messages: list
    temperature: float

# Define a root `/` endpoint
@app.get("/")
async def root():
    return response

@app.post("/chat/completions")
async def completions(Data: Data):
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="10.10.1.13", port=8123 ) 
