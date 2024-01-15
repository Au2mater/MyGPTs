# Example: reuse your existing OpenAI setup
from openai import OpenAI

# this file will only be executed if you run it directly with the file open
if "__file__" not in globals() and __name__ == "__main__":
    # Point to the local server
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

    completion = client.chat.completions.create(
        model="local-model",  # this field is currently unused
        messages=[
            {"role": "system", "content": "Always answer in rhymes."},
            {"role": "user", "content": "Introduce yourself."},
        ],
        temperature=0.7,
    )

    print(completion.choices[0].message)
