# MyGPTs

The goal of this app, is to allow everyone in an organisation to create their own personlized GPT Chat Assistants with custom "rules" and knowledge sources, using a simple graphic user interface and without any coding.

![Screenshot of assistant builder. ](<images/Screenshot_2024-01-02_1.png>)

![Screenshot of chat interface. ](<images/Screenshot_2024-01-02 221402.png>)

## Features
__Assistants__
- Create and edit your own GPT Chat Assistants
- Create assistants from pre-configured templates
- Create assistants from scratch



__Models__
<br>APIs currently supported:
 - Azure OpenAi (GPT 3.5 Turbo)
 - Azure OpenAi (GPT 4)
 - Local models served using LM Studio

__Languages__
<br>User interface languages currently supported:
- Danish

__Knowledge base sources currently supported__
<br>PDF, DOC, DOCX, MD, TXT and web URLs

## Prerequisites

Before you can run this application, you need to have the following installed on your system:

- [Python 3.10](https://www.python.org/downloads/)
- Pipenv installed using [PIXI](https://pixijs.io/)
```sh
pixi install pipenv
```
- An [Azure OpenAi](https://learn.microsoft.com/en-us/azure/ai-services/openai/) API key, an OpenAi API key or a local LLM running using [LM Studio](https://lmstudio.ai/)
- Your API key and endpoint must be set as environment variables in your terminal:
<br>_Here's an example for Windows:_
```sh 
setx AZURE_OPENAI_ENDPOINT "https://<endpoint>.openai.azure.com/"
setx AZURE_OPENAI_KEY "Your Azure OpenAI API key"
```
## Usage
1.  Clone the repository to your local machine.

2. Navigate to the project directory in your terminal.
3. Install the project dependencies using Pipenv:
```sh
pipenv install
```
4. In the project directory, open _config/LLMs.yaml_ and add the APIs that you want to use.
5. Run the application:
```sh
pipenv run python app/Opret_assistent.py
```

_Built using [Streamlit](https://streamlit.io/), [LangChain](https://www.langchain.com/) and [ChromaDB](https://www.trychroma.com/)._
