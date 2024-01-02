from src.openai.openai_utils import generate_response

chat_model_name = "gpt-35-turbo"
system_prompt = (
    "Du er en hjælpsom dansktalende assistent."
    " Du hjælper medarbejdere og borgere i Gladsaxe Kommune."
)

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "assistant", "content": "Hej, hvordan kan jeg hjælpe dig?"},
]

response = generate_response(
    prompt_input="Hvordan opretter jeg admin på en fælles postkasse?", messages=messages
)

print(response)
