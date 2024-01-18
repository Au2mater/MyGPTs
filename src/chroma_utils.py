""" utility functions for indexing and retrieval of documents using chroma"""
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores.chroma import Chroma
import chromadb
import os
import subprocess
import requests
from langchain_community.document_loaders import (
    UnstructuredFileLoader,
    WebBaseLoader,
)
from langchain_core.documents import Document
from langchain.text_splitter import SentenceTransformersTokenTextSplitter, RecursiveCharacterTextSplitter
import streamlit as st  # for caching
from pydantic import BaseModel, ConfigDict
from pydantic.types import FilePath  # , Literal
from pydantic.networks import AnyHttpUrl
from pathlib import WindowsPath
from typing import Union
from pydantic_core import Url
from streamlit.runtime.uploaded_file_manager import UploadedFile
from uuid import uuid4
from src.basic_data_classes import Source
from pathlib import Path
import dotenv as de
from src.sqlite.gov_db_utils import get_global_setting
from chromadb.config import Settings
# ---------------------------

"""
create an http chroma client,
create and delete collections
convert various input types to sources
index and remove sources from collections
 """

# Define the .env file path
env_path = Path(".") / ".env"

# Load the variables from the .env file into the environment
de.load_dotenv(dotenv_path=env_path)
temp_file_location = os.getenv("TEMP_FILE_LOCATION")
chromadb_host = os.getenv("CHROMADB_HOST")
chromadb_port = int(os.getenv("CHROMADB_PORT"))

# ----------------------------
# chroma client operations


@st.cache_resource(show_spinner=False)
def start_chroma_server():
    """start chroma http server if it's not already running"""
    # run command chroma run --path data/db --port 8000
    db_path = os.path.join("data", "vector_db")
    port = str(chromadb_port)
    # test if server is already running
    try:
        response = requests.get(f"http://{chromadb_host}:{port}/api/v1")
        if response.status_code == 200:
            print("chroma server is already running")
            return
    except requests.exceptions.RequestException:
        pass
    # Define the command you want to run in the new terminal
    command = ["chroma", "run", "--path", db_path, "--port", port]
    # Open a new terminal and run the command
    subprocess.Popen(command)
    # we are using subprocess to keep the terminal open for more python code execution while server is running
    # check if subprocess is running


def start_chroma_client():
    client = chromadb.HttpClient(
        host=chromadb_host,
        port=chromadb_port,
        settings=Settings(anonymized_telemetry=False),
    )
    return client


# ----------------------------
# collection level operations

# a collection is unique for a given assistant
# a collection contain zero or more chunks of text from sources


def get_or_create_collection(collection_name):
    """create a collection with the given name and client"""
    # create a collection
    client = start_chroma_client()
    emb_model_name = get_global_setting("embeddings_model").value
    embedding_function = SentenceTransformerEmbeddings(model_name=emb_model_name)
    print(f"embeddings model {emb_model_name} loaded")
    collection = Chroma(
        collection_name=collection_name,
        client=client,
        embedding_function=embedding_function,
    )
    return collection


def get_collection(collection_name):
    """get a collection with the given name and client"""
    client = start_chroma_client()
    collection = client.get_collection(name=collection_name)
    return collection


def delete_collection(collection_name):
    """delete a collection with the given name and client"""
    # create a collection
    client = start_chroma_client()
    client.delete_collection(name=collection_name)


def delete_all_collections():
    """delete all collections with the given name and client"""
    # create a collection
    client = start_chroma_client()
    collections = client.list_collections()
    # prompt the user in the terminal to confirm deletion
    response = input(
        f"Are you sure you want to delete {len(collections)} collections? (y/n)"
    )
    if response == "y":
        for collection in collections:
            client.delete_collection(name=collection.name)


def get_or_create_retriever(
    collection_name: str,
) -> object:
    """create a retriever fromt the given collection"""
    collection = get_or_create_collection(collection_name=collection_name)
    retriever = collection.as_retriever(
        search_type="similarity", search_kwargs={"k": 6}
    )
    return retriever


def format_docs(docs):
    "takes a list of documents and returns a string of the page content of each document."
    return "\n\n---------".join(doc.metadata['chained_content'] for doc in docs)


def add_context(prompt: str, messages: list, assistant: object, top_k: int = 5):
    # if retriever is provided, get relevant documents and add them to request
    retriever = get_or_create_retriever(collection_name=assistant.id)
    retrieved_docs = retriever.get_relevant_documents(prompt, top_k=top_k)[:top_k]
    context = format_docs(retrieved_docs)
    request_messages = messages + [{"role": "user", "content": "context: " + context}]
    return request_messages


# ----------------------------
# source level operations

# files fetched through streamlits fileupoader are "UploadedFile()" objects, these need to be saved to disk before they can be loaded
# urls are added through the ui as strings, these can be loaded directly
# file paths are added through the ui as strings, these can be loaded directly


# a class for validating the initial input data types to be turned into sources
class Input(BaseModel):
    """there are three types of soruce inputs:
    urls, file paths and streamlit fileuploader files"""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    input: Union[UploadedFile, AnyHttpUrl, FilePath]


# this function takes an input and return a source object.
def create_source(input, c_a_id: str) -> Source:
    """
    input: a url, file path or streamlit fileuploader file
    c_a_id: a collection and assistant id
    returns an in memmory source object
    """
    validated_input = Input(input=input).input

    if isinstance(validated_input, UploadedFile):
        # save the file to temp directory data/temp
        path_url = os.path.join(temp_file_location, uuid4().hex + input.name)
        with open(path_url, "wb") as f:
            f.write(input.getvalue())
            f.close()
        loader = UnstructuredFileLoader(path_url, encoding="utf-8")
        source = Source(
            name=input.name,
            source_type="uploaded file",
            content_type=input.name.split(".")[-1],
            content=loader.load()[0].page_content,
            collection_name_and_assistant_id=c_a_id,
        )
        # delete the file from temp directory
        os.remove(path_url)

    elif isinstance(validated_input, Url):
        loader = WebBaseLoader(input)
        source = Source(
            name=input,
            source_type="url",
            content_type="url",
            content=loader.load()[0].page_content,
            collection_name_and_assistant_id=c_a_id,
        )
    elif isinstance(validated_input, WindowsPath):
        loader = UnstructuredFileLoader(input, encoding="utf-8")
        source = Source(
            name=validated_input.name,
            source_type="file path",
            content_type=validated_input.suffix[1:],
            content=loader.load()[0].page_content,
            collection_name_and_assistant_id=c_a_id,
        )

    else:
        raise ValueError(f"source {input} is not a valid url or file path")

    # clean up the source content, strip and remove duplicate spaces
    source.content = " ".join(source.content.split())
    return source


def source_to_document(source: Source) -> Document:
    """given a source object, convert the source to a langchain document"""
    # copy the source object
    src = source.model_copy()
    document = Document(page_content=src.content, metadata=src.model_dump())
    # convert any document metdata that is not str, int, float or bool to str
    for k, v in document.metadata.items():
        if not isinstance(v, (str, int, float, bool)):
            document.metadata[k] = str(v)
    return document


def add_chunk_id(chunks):
    for i, chunk in enumerate(chunks):
        chunk.metadata['chunk_id'] = i
        chunk.metadata['chunk_count'] = len(chunks)
    return chunks


def chain_chunks(chunks , chain_length=3):
    ''' add the content of the next chunk to the current chunk '''
    chunks = add_chunk_id(chunks)
    for i, chunk in enumerate(chunks):
        chunk.metadata['chained_content'] = ' '.join([chunk.page_content]  + [c.page_content for c in chunks[i+1:i+chain_length]])
        # add previous chunk content to current chunk
        if i > 0:
            chunk.metadata['chained_content'] = ' '.join(['...',chunks[i-1].page_content[:-200]] + [chunk.metadata['chained_content']])
    return chunks

# deprecated
# def split_document(document: object) -> list:
#     """given a langhchain document, split the document into chunks (list of sentences)"""
#     emb_model_name = get_global_setting("embeddings_model").value
#     splitter = SentenceTransformersTokenTextSplitter(model_name=emb_model_name)
#     chunks = splitter.split_documents([document])
#     return chunks

def split_document(document: object) -> list:
    """given a langhchain document, split the document into chunks (list of sentences)"""
    splitter = RecursiveCharacterTextSplitter( 
        chunk_size=600,
        chunk_overlap=0,
        separators=['\n','\\.','\\?']
        , is_separator_regex= True
        , keep_separator=True)
    chunks = splitter.split_documents([document])
    chunks_to_index = chain_chunks(chunks, chain_length=3)
    return chunks_to_index



def index_source(source: Source):
    """given a source, load the source, split the source,
    and index the source in the named collection using a chroma persistent client"""
    # convert to langchain document
    document = source_to_document(source)
    # split the document
    chunks = split_document(document)
    # index the document
    collection = get_or_create_collection(
        collection_name=source.collection_name_and_assistant_id
    )
    # add chunks in batches of 100
    for batch in range(0, len(chunks), 100):
        collection.add_documents(
            chunks[batch : batch + 100],
        )
    print(f"{source.name} indexed into {len(chunks)} chunks")


def remove_source(source: Source):
    """given a source, remove the source chunks from the named collection using a chroma http client"""
    where = {"id": source.id}
    collection = get_collection(collection_name=source.collection_name_and_assistant_id)
    remove_ids = collection.get(where=where)["ids"]
    try:
        collection.delete(remove_ids)
    except Exception:
        print(
            f"{source.name} not found in collection {source.collection_name_and_assistant_id}"
        )
