# MyGPTs :left_speech_bubble: 
_A simple user interface for easily creating, sharing and chatting with assistants based on GPT models._

Creating and sharing custom chatbots has never been easier!
The goal of this app is to allow everyone in an organization to create their own personalized GPT Chat Assistants with custom "rules" and knowledge sources (RAG), using a simple graphic user interface and without any coding.
<br>Setting up the app might require some technical knowledge. If you already have access to an OpenAi API, Azure OpenAi API or have LM Studio running locally, this can be done in a few minutes. 
<br>When the app is launched, everyone with access to the app can create, share and chat with their own custom made assistants.
<br>
<br>
<img src="images/oprah.jpg" alt="Oprah meme: You get a GPT! You get a GPT! Everyone gets a GPT!" width="500"/>

## Table of contents
- [Features](#features)
- [Installation](#installation)
    - [Prerequisites](#prerequisites)
    - [Setup](#setup)
- [Running the app](#running-the-app)
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
 - Any Chat API compatible with openai-python library

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
Congrats! :tada: You're ready to run the app.

# Running the app
1. In the scripts folder, run the the start_app.bat file.
A server should start up on port _8501_ and a browser tab should open with the app interface. 

2. You will now be presented with an admin interface where you can add your model APIs to the app.
<br>_This admin view is only visible from localhost_
<br>Click the '_Tilføj ny model_' button and fill out the form.
<br>To start creating and sharing assistants press the '_Mine assistenter_' button.

Start building and sharing your GPTs.

## Prototype in Beta
Please note that this app is currently in beta and is still a prototype. Breaking changes may occur as I continue to improve and refine the functionality. I appreciate your understanding and feedback as I work towards a stable release.

Version: 0.3.3


_Built using [Streamlit](https://streamlit.io/), [LangChain](https://www.langchain.com/) and [ChromaDB](https://www.trychroma.com/)._


## Screenshots
![Screenshot of assistant builder. ](<images/ss_myassistants_240109.jpg>)
____
![Screenshot of assistant builder. ](<images/ss_edit_240109.jpg>)
___
![Screenshot of chat interface. ](<images/ss_chat_240111.jpg>)

