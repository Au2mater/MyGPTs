""" Utility functions for using OpenAI API."""
import os
from openai import AzureOpenAI, OpenAI
from src.basic_data_classes import LLM

def format_docs(docs):
    "takes a list of documents and returns a string of the page content of each document."
    return "\n\n".join(doc.page_content for doc in docs)

def prepare_request(question, system_prompt=None, messages=None, retriever=None):
    """return a messages reuest for the chat model.
    If retriever is provided, use the retiriever to get relevant documents.
    Otherwise, just pass on messages."""
    # initialize system prompt if not provided, depending on retriever
    if not system_prompt:
        print("no system prompt provided, using default")
        if retriever:
            system_prompt = (
                "Du er en assistent der hjælper med spørgsmål og svar."
                " Brug de følgende stykker af indhentet kontekst til at besvare spørgsmålet."
                " Hvis du ikke kender svaret, så sig bare, at du ikke ved det."
                " Hvis du har brug for mere kontekst, så spørg brugeren."
                " Brug maksimalt tre sætninger og hold svaret kortfattet."
            )
        else:
            system_prompt = (
                "Du er en hjælpsom dansktalende assistent."
                " Du hjælper medarbejdere og borgere i Gladsaxe Kommune."
            )

    # innitialize messages if not provided
    if not messages:
        print("no messages provided, starting new conversation")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": "Hej, hvordan kan jeg hjælpe dig?"},
        ]

    # if retriever is provided, get relevant documents and add them to request
    if retriever:
        retrieved_docs = retriever.get_relevant_documents(question, top_k=5)
        context = format_docs(retrieved_docs)
        request_messages = messages + [
            {"role": "user", "content": "context: " + context}
        ]
    else:
        request_messages = messages

    return request_messages


# Function for generating LLM response
def generate_response(
    prompt_input,
    llm: str,
    messages=[],
    api_version="2023-07-01-preview",
    max_tokens=1000,
    temperature=0.7,
):
    api_type = llm.api_type
    if api_type == "azure":
        client = AzureOpenAI(
            api_key=llm.api_key,
            api_version=api_version,
            azure_endpoint=llm.enpoint_or_base_url,
        )
    else:
        client = OpenAI(
            api_key=llm.api_key,
            base_url=llm.enpoint_or_base_url,
        )
    response = client.chat.completions.create(
        model=llm.deployment,
        messages=messages + [{"role": "user", "content": prompt_input}],
        max_tokens=max_tokens,
        temperature=temperature,
    )

    return response.choices[0].message.content


def _test_llm_api(llm):
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


if __name__ == "__main__":
    model = {
        "name": "GPT",
        "api_type": "azure",
        "deployment": "gpt-4",
        "enpoint_or_base_url": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_key": os.getenv("AZURE_OPENAI_KEY"),
        "description": "test model",
    }
    llm = LLM(**model)
    print(llm.model_dump())
    # test llm
    _test_llm_api(llm)
    # test non existing deployment
    model = {
        "name": "GPT",
        "api_type": "azure",
        "deployment": "gpt-35-turbo",
        "enpoint_or_base_url": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_key": "abc123",  # FAKE KEY
        "description": "test model",
    }
    llm = LLM(**model)
    print(llm.model_dump())
    # test llm
    _test_llm_api(llm)
 