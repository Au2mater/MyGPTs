# MyGPTs :left_speech_bubble: 
_A simple user interface for easily creating, sharing and chatting with assistants based on GPT models._

The goal of this app is to allow everyone in an organization to create their own personalized GPT Chat Assistants with custom "rules" and knowledge sources (RAG), using a simple graphic user interface and without any coding.
<br>Setting up the app requires a developer or an IT-technician. If you already have access to an OpenAi API, Azure OpenAi API or have LM Studio running locally, this can be done in a few minutes. 
<br>When the app is launched, everyone with access to the app can create and chat with their own assistants.
<br>
<br>
<img src="images/oprah.jpg" alt="Oprah meme: You get a GPT! You get a GPT! Everyone gets a GPT!" width="500"/>

## Table of contents
- [Features](#features)
- [Installation](#installation)
    - [Prerequisites](#prerequisites)
    - [Setup](#setup)
- [Version](#prototype-in-beta)
- [Screenshots](#screenshots)


## Features

__Assistants__
- Allow anyone to create and edit their own GPT Chat Assistants
- Add documents and websites to the assistant's knowledge base (Drag and drop RAG).
- No coding required


__Models__
<br>APIs currently supported:
 - Azure OpenAi
 - OpenAi
 - Local models served using LM Studio

__Privacy__
<br> This app runs locally on your server.
<br> Besides the optional OpenAi or Azure API calls, no data is collected.
<br> The only external data transfer happens when using OpenAi and Azure OpenAi APIs.
<br> If you want full privacy, use an open-source local model through LM Studio. In this case everything should run on-premise and no data will leave your organisation.
<br> Knowledge sources are indexed in a local vector database using a locally downloaded open-source embeddings model.

__Languages__
<br>User interface languages currently supported:
- Danish

__Knowledge base sources currently supported__
<br>PDF, DOC, DOCX, MD, TXT, and web URLs

# Installation
## Prerequisites

Before you can run this application, you need to have the following installed on your server or local machine:
- [Python 3.10](https://www.python.org/downloads/)
- [Pipenv](https://pipenv.pypa.io/en/latest/installation.html) 
```sh
pixi install pipenv
```
- An [Azure OpenAi](https://learn.microsoft.com/en-us/azure/ai-services/openai/) API key, an OpenAi API key or a local LLM running using [LM Studio](https://lmstudio.ai/)
- Your API key and endpoint must be set as environment variables in your terminal:

<br>_Here's an example for Windows with Azure API:_
```sh 
setx AZURE_OPENAI_ENDPOINT "https://<endpoint>.openai.azure.com/"
setx AZURE_OPENAI_KEY "<your Azure OpenAI API key>"
```
<br>_Here's an example for Windows with LM Studio:_
```sh
setx LOCAL_LLM_ENDPOINT "http://localhost:1234/v1"
setx LOCAL_LLM_KEY "not-needed"
```

## Setup
1. Clone the repository to your local machine or download as a zip file and extract it.
2. In a terminal: Navigate to the project directory in your terminal, the folder named 'MYGPTS'.
_For windows:_
```sh
cd <path to project directory>/MYGPTS
```
3. Install the project dependencies using Pipenv by running the following command:
```sh
pipenv install
```
4. Activate the virtual environment:
```sh
pipenv shell
```
5. With the environment still activated, run the following command to setup the databases:
```sh
python scripts\setup.py
```
4. In the project directory, open _config/LLMs.yaml_ and add the necessary details for the APIs that you want to use.

Congrats! :tada: You're ready to run the app.

5. With the environment activated, run the application using the following command:
```sh
streamlit run app\MyGPTs.py
```
A server should start up on port _8501_ and a browser tab should open with the app interface. Start building and sharing your GPTs.

## Prototype in Beta
Please note that this app is currently in beta and is still a prototype. Breaking changes may occur as I continue to improve and refine the functionality. I appreciate your understanding and feedback as I work towards a stable release.

Version: 0.3.1


_Built using [Streamlit](https://streamlit.io/), [LangChain](https://www.langchain.com/) and [ChromaDB](https://www.trychroma.com/)._


## Screenshots
![Screenshot of assistant builder. ](<images/ss_myassistants_240109.jpg>)
____
![Screenshot of assistant builder. ](<images/ss_edit_240109.jpg>)
___
![Screenshot of chat interface. ](<images/ss_chat_240111.jpg>)
