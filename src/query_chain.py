""" chain for generating queries | retrieving results | adding context to prompt | generating response"""

from src.openai_utils import (
    generate_response,
    connect_to_client,
)
from src.sqlite.db_utils import get_assistant, get_llm, get_active_llms
from src.chroma_utils import start_chroma_server, get_or_create_retriever
import json
from jinja2 import Template
import copy

# Define the query building template with placeholders
template_string = (
    '[{"role": "system","content": "Du er en hjælpsom assistent, der hjælper med:\\n '
    "1- Kort at forklare en enkelt besked eller henvendelse i en samtale.\\n"
    "2- Kort at forklare hvilke information der er behov for at indhente for at besvare henvendelsen.\\n"
    "3- Generér tre forskellige søgeforespørgsler for at indhente denne information.\\n\\n"
    "Dine svar er altid i valid JSON format:\\n\\n"
    "{'forklaring': '<brugerens hensigt med beskeden>',\\n"
    "'nødvendig information':'<nødvendig information>',\\n"
    "'søgeforespørgsler': ['<forespørgsel 1>', '<forespørgsel 2>', '<forespørgsel 3>']}\\n\\n"
    'Sørg for at forespørgslerne er forskelligartede.\\nHusk at resultatet skal være i JSON."},'
    '{"role": "user",'
    '"content": "Samtale:\\n{{format_messages(messages)}}\\n'
    "Betragt sidste brugerbesked i ovenstående samtale.\\n"
    "1- Forklar brugerens hensigt med beskeden.\\n"
    "2- Afdæk hvilke information der kræves for at besvare forespørgslen.\\n"
    "3- Generér tre forskellige søgeforespørgsler der kan hjælpe med at indhente relevant viden."
    '"}]'
)

agent = {
    "temperature": 1.0,  # higher temperature to generate more diverse queries
    "max_tokens": 2500,
    # from the list of active llms use the llm the was first created
    "llm": get_active_llms()[0],
}

# Create a Template object
template = Template(template_string)


def format_messages(messages: list):
    # copy the messages list so we don't mutate the original
    msgs = copy.deepcopy(messages)
    # replace role user with bruger
    for msg in msgs:
        if msg["role"] == "user":
            msg["role"] = "bruger"
        if msg["role"] == "assistant":
            msg["role"] = "assistent"
    return "\\n\\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in msgs if msg["role"] != "system"]
    )


def append_user_input(messages, user_input):
    return messages + [{"role": "user", "content": user_input}]


def prepare_prompt_for_agent(messages):
    # Render the template with variables
    rendered_string = template.render(
        messages=messages, format_messages=format_messages
    )  # ; print(rendered_string)
    rendered_dict = json.loads(rendered_string)  # ;  print(rendered_dict)
    return rendered_dict


def generate_search_queries(prompt_input: str, messages: list):
    """
    takes a prompt input and a list of messages and generates a list of search queries
    the prompt input is the prompt for the query maker assistant
    the messages list is the conversation between the user and the main assistant
    """
    msgs = copy.deepcopy(messages)
    conversation = append_user_input(
        messages=msgs, user_input=prompt_input
    )  # ; print(conversation)
    agent_messages = prepare_prompt_for_agent(conversation)  # ; print(agent_messages)
    # prepend qm system message to qm prompt
    # drop main_assistants system message from messages and append prompt user message
    client = connect_to_client(llm=agent["llm"])
    response = client.chat.completions.create(
        model=agent["llm"].deployment,
        messages=agent_messages,
        max_tokens=agent["max_tokens"],
        temperature=agent["temperature"],
    )
    qm_response_str = response.choices[0].message.content
    print(qm_response_str)

    # the query makers response should be a json string
    # remove anything before the first { and after the last }
    qm_response_str = qm_response_str[
        qm_response_str.find("{") : qm_response_str.rfind("}") + 1
    ]  # ; print(qm_response_str)
    # evaluate if the response is a valid json string
    try:
        qm_response_dict = json.loads(qm_response_str)
        queries = qm_response_dict["søgeforespørgsler"]  # ; print(queries)
    
    except Exception as e:
        print(f"An error occurred while parsing the response: {e}")
        # fail safe, return the prompt input as a query
        queries = [prompt_input]
    return queries


def retrieve_results(assistant, queries: list, top_k: int = 4):
    """
    retireves unique results from main assistants retriever
    sorted by result.metadata['chunk_id']
    """
    retriever = get_or_create_retriever(assistant.id, k=top_k)
    results = []
    for query in queries:
        query_results = retriever.get_relevant_documents(query=query)
        print(f"{len(query_results)} results retrieved")
        results = results + query_results
    # dedeuplicate results based on result.metadata['chunk_id']
    unique_results = list(
        {result.metadata["chunk_id"]: result for result in results}.values()
    )  # ; print(f'{len(unique_results)} unique results')
    # sort results by result.metadata['chunk_id']
    unique_results.sort(key=lambda result: result.metadata["chunk_id"])
    return unique_results


def merge_overlapping_strings(strings: list):
    """
    takes two strings, evaluates if they overlap and stiches them together if they do
    string overlap if 1st string ends with the same words the 2nd string begins with
    """
    str1, str2 = strings
    str1_words = str1.split(" ")
    # drop the '...' prepended to the 2nd string
    str2_words = str2.split(" ")[1:]
    # find overlap
    overlap = []
    # chheck fo overlap of at least 4 words
    for i in range(max(len(str1_words) - 4, 0)):
        if str1_words[i:] == str2_words[: len(str1_words[i:])]:
            overlap = str1_words[i:]
            break
    # stich strings together
    if overlap:
        merged_string = " ".join(str1_words + str2_words[len(overlap) :])
    else:
        merged_string = None
    return merged_string


def merge_multiple_strings(chunks: list):
    """
    takes a list of strings (chunks) and merges them together if they overlap
    """
    contents = [chunk.metadata["chained_content"] for chunk in chunks]
    chunk_ids = [chunk.metadata["chunk_id"] for chunk in chunks]
    i = 0
    while i < len(chunk_ids):
        if i == len(chunk_ids) - 1:
            break
        else:
            ID1, ID2 = chunk_ids[i], chunk_ids[i + 1]
            # print("comparing chunks", ID1, ID2)
            if ID1 >= ID2 - 3:
                merged_content = merge_overlapping_strings(
                    [contents[i], contents[i + 1]]
                )
                # print(f"chunk ID {ID1} merged with {ID2}")
                if merged_content:
                    contents[i] = merged_content
                    _ = contents.pop(i + 1)
                    _ = chunk_ids.pop(i + 1)
                else:
                    i += 1
            else:
                i += 1
    return contents


def add_context_from_queries(
    messages: list, queries: list, assistant: object, top_k: int = 4
):
    """
    takes a list of queries, messages and an assistant
    retrieves results from main assistants retriever
    and adds the context from the results to the messages
    """
    # retrieve results from main assistants retriever
    unique_results = retrieve_results(assistant=assistant, queries=queries, top_k=top_k)
    # merge results
    contents = merge_multiple_strings(unique_results)
    context = "\n\n-----------".join(contents)
    # add context to prompt
    request_messages = messages + [{"role": "user", "content": "context: " + context}]
    return request_messages


# if __name__ == "__main__":

# Render the template with variables
# messages = [{'role':'system','content':'Du er en hjælpsom assistent'}
#             ,{'role':'assistant','content':'hej, hvordan kan jeg hjælpe dig?'}
#             ,{'role':'bruger','content':'Kan jeg slette billeder som jeg ikke selv har uploadet?'}]

# renedered_dict = prepare_prompt_for_agent(messages) ; print(renedered_dict)


if __name__ == "__main__":
    start_chroma_server()
    # initiate main assistant
    main_assistant_id = "55f18bb1c4ff4fdebb604d4df0eba5ac"
    main_assistant = get_assistant(main_assistant_id)

    # initiate conversation
    messages = [
        {"role": "system", "content": main_assistant.system_prompt},
        {"role": "assistant", "content": main_assistant.welcome_message},
    ]
    prompt_input = "Hvordan får jeg hjælp fra en person?"
    queries = generate_search_queries(prompt_input=prompt_input, messages=messages)

    request_messages = add_context_from_queries(
        messages=messages, queries=queries, assistant=main_assistant, top_k=4
    )  # ; print(len(request_messages))
    # messages
    # request_messages
    # generate response
    generate_response(
        prompt_input=prompt_input,
        llm=get_llm(main_assistant.chat_model_name),
        messages=request_messages,
        max_tokens=100,
        temperature=0.9,
    )
    # retrieve results from main assistants retriever
    unique_results = retrieve_results(
        assistant=main_assistant, queries=queries, top_k=4
    )
    print(len(unique_results))

    contents = merge_multiple_strings(unique_results)
    print(len(contents))

    chunk_ids = [result.metadata["chunk_id"] for result in unique_results]
    print(chunk_ids)
    # count number of words in each result.metadata['content']

    sum_chain = 0
    sum_page = 0
    for result in unique_results:
        sum_chain += len(result.metadata["chained_content"].split(" "))
        sum_page += len(result.page_content.split(" "))
    print(sum_chain, sum_page)

    sum_content = 0
    for c in contents:
        sum_content += len(c.split(" "))
    print(sum_content)

    class Result:
        def __init__(self, metadata: dict):
            self.metadata = metadata

    # create a test list og three overlapping results
    results = [
        Result(metadata={"chunk_id": 1, "chained_content": "this is the first result"}),
        Result(
            metadata={"chunk_id": 2, "chained_content": "first result second result"}
        ),
        Result(
            metadata={"chunk_id": 3, "chained_content": "second result third result"}
        ),
    ]
    # set chained_content
    # merge the results
    merged_results = merge_multiple_strings(results)
    print(merged_results)
