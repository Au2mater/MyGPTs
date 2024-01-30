from src.query_chain import prepare_prompt_for_agent, generate_search_queries, add_context_from_queries

messages = [
    {'role':'system','content':'You are a helpful assistant. You are helping a user find'}
    ,{'role':'assistant','content':'How can I help you?'}
    ,{'role':'user','content':
      '''I am looking for a document about:
      - jazz
      - blues
      - rock
      '''}
]

def test_prepare_prompt_for_agent():
    """test connecting to the mockup API and generating a response."""
    prompt = prepare_prompt_for_agent(messages=messages)
    assert len(prompt) > 0
