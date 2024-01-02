import os
from src.openai.openai_utils import prepare_request, generate_response
from openai import AzureOpenAI, OpenAI
import yaml

# read LLM configurations
with open("config/LLMs.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    LLMs = config["models"]
    settings = config["global_settings"]
    # returns a dict of dictionaries where each dictionary is similar to this:
    # 'GPT 3.5 Turbo': {'api_type': 'azure', 'deployment': 'gpt-35-turbo', 'base_url': 'AZURE_OPENAI_ENDPOINT', 'api_key': 'AZURE_OPENAI_KEY'}

# check that environment variables for each LLM are set
for name, LLM in LLMs.items():
    assert (
        os.getenv(LLM["api_key"]) is not None
    ), f"environment variable {LLM['api_key']} not found"
    assert (
        os.getenv(LLM["base_url"]) is not None
    ), f"environment variable {LLM['base_url']} not found"
    print(f"environment variables for {name} all set")

# TEST gpt 3.5 turbo
model = LLMs["GPT 3.5 Turbo"]
client = AzureOpenAI(
    api_key=os.getenv(model["api_key"]),
    api_version="2023-07-01-preview",
    azure_endpoint=os.getenv(model["base_url"]),
)
deployment_name = model["deployment"]

assert client.chat.completions.create(
    model=deployment_name,
    messages=[{"role": "system", "content": "Du er en hjælpsom assistent."}],
    max_tokens=3,
), "Azure OpenAI API not working"

assert len(prepare_request("Hvad er en hund?")) >= 2, "prepare_request not working"
response = generate_response("Gentag, efter mig: Hej")
assert isinstance(response, str), "generate_response not working"
if response == "Hej":
    print("chatbot returning predictable response")
else:
    print(f"chatbot reponded: {response}")
# the last might not always work, as it is a chatbot and the response is not always the same


for name, LLM in LLMs.items():
    if LLM["api_type"] == "azure":
        client = AzureOpenAI(
            api_key=os.getenv(LLM["api_key"]),
            api_version="2023-07-01-preview",
            azure_endpoint=os.getenv(LLM["base_url"]),
        )
    else:
        client = OpenAI(
            api_key=os.getenv(LLM["api_key"]),
            base_url=os.getenv(LLM["base_url"]),
        )

    assert client.chat.completions.create(
        model=LLM["deployment"],
        messages=[
            {"role": "system", "content": "Du er en hjælpsom assistent."},
            {"role": "assistant", "content": "Hej, hvordan kan jeg hjælpe dig?"},
            {"role": "user", "content": "Hvad er en hund?"},
        ],
        max_tokens=3,
        temperature=settings["temperature"],
    ), f"{name} not working"
    print(f"{name} working")
