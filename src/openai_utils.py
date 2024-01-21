""" Utility functions for using OpenAI API."""
from openai import AzureOpenAI, OpenAI
from src.basic_data_classes import LLM, Assistant
from src.sqlite.db_utils import get_llm


def connect_to_client(llm: LLM):
    """Connect to OpenAI API and return client."""
    api_type = llm.api_type
    if api_type == "azure":
        client = AzureOpenAI(
            api_key=llm.api_key,
            api_version="2023-07-01-preview",
            azure_endpoint=llm.enpoint_or_base_url,
        )
    else:
        client = OpenAI(
            api_key=llm.api_key,
            base_url=llm.enpoint_or_base_url,
        )
    # if successful, log and return client
    return client


# Function for generating LLM response
def generate_response(
    prompt_input: str,
    llm: LLM,
    messages=[],
    max_tokens=1000,
    temperature=0.7,
):
    """Generate response from LLM model."""
    client = connect_to_client(llm=llm)
    response = client.chat.completions.create(
        model=llm.deployment,
        messages=messages + [{"role": "user", "content": prompt_input}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content


def get_response_from_assistant(
    prompt_input: str,
    assistant: Assistant,
    messages=[],
    max_tokens=1000,
):
    """Generate response from LLM model."""
    llm = get_llm(assistant.chat_model_name)
    client = connect_to_client(llm=llm)
    response = client.chat.completions.create(
        model=llm.deployment,
        messages=messages + [{"role": "user", "content": prompt_input}],
        max_tokens=max_tokens,
        temperature=assistant.temperature,
    )
    return response.choices[0].message.content


def llm_api_test(llm):
    """test the LLM model by generating a response to a prompt."""
    prompt_input = "repeat after me: 'All systems go!'"
    try:
        generate_response(prompt_input, llm=llm)
        return True, "All systems go! Modellen virker som den skal."
    # if exception is similar to Error code: 404 - {'error': {'code': 'DeploymentNotFound', 'message': 'The API deployment for this resource does not exist. If you created the deployment within the last 5 minutes, please wait a moment and try again.'}}
    # then return a message that the deployment does not exist
    except Exception as e:
        if "DeploymentNotFound" in str(e):
            return False, "DeploymentNotFound: " + str(e)
        elif "Connection error" in str(e):
            return (
                False,
                "Der kan ikke oprettes forbindelse til APIet. Tjek at du har indtastet den rigtige URL.",
            )
        elif "Unauthorized" in str(e):
            return (
                False,
                "API nøglen er ikke korrekt. Tjek at du har indtastet den rigtige nøgle.",
            )
        else:
            return False, "Der problem med at få respons fra modellen. Fejl:" + str(e)
