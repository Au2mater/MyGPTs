""" utility functions for indexing and retrieval of documents using chroma"""
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores.chroma import Chroma
import chromadb
import os
import subprocess
import requests
import yaml
from langchain_community.document_loaders import (
    UnstructuredFileLoader,
    WebBaseLoader,
)
from langchain_core.documents import Document
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
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

# ---------------------------

""" 
create an http chroma client,  
create and delete collections 
convert various input types to sources
index and remove sources from collections
 """

# ----------------------------
# chroma client operations


def get_db_config():
    """read the chroma port, embeddings_model, and host from config/vector_db.yaml"""
    with open("config/vector_db.yaml", "r") as f:
        db_config = yaml.load(f, Loader=yaml.FullLoader)
        f.close()
    return db_config


@st.cache_resource(show_spinner=False)
def start_chroma_server():
    """start chroma http server if it's not already running"""
    # run command chroma run --path data/db --port 8000
    db_config = get_db_config()
    db_path = os.path.join("data", "vector_db")
    port = str(db_config["port"])
    # test if server is already running
    try:
        response = requests.get(f"http://localhost:{port}/api/v1")
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
    db_config = get_db_config()
    client = chromadb.HttpClient(host=db_config["host"], port=db_config["port"])
    return client


# ----------------------------
# collection level operations

# a collection is unique for a given assistant
# a collection contain zero or more chunks of text from sources


def get_or_create_collection(collection_name):
    """create a collection with the given name and client"""
    # create a collection
    client = start_chroma_client()
    emb_model_name = get_db_config()["embeddings_model"]
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
    return "\n\n".join(doc.page_content for doc in docs)


def add_context(prompt: str, messages: list, assistant: object, top_k: int = 5):
    # if retriever is provided, get relevant documents and add them to request
    retriever = get_or_create_retriever(collection_name=assistant.id)
    retrieved_docs = retriever.get_relevant_documents(prompt, top_k=top_k)[:top_k]
    context = format_docs(retrieved_docs)
    request_messages = messages + [{"role": "user", "content": "context: " + context}]
    return request_messages


# if __name__ == "__main__":

# delete_all_collections()


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
        path_url = os.path.join("data", "temp", uuid4().hex + input.name)
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


def split_document(document: object) -> list:
    """given a langhchain document, split the document into chunks (list of sentences)"""
    emb_model_name = get_db_config()["embeddings_model"]
    splitter = SentenceTransformersTokenTextSplitter(model_name=emb_model_name)
    chunks = splitter.split_documents([document])
    return chunks


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


if __name__ == "__main__":
    input = "https://www.google.com"
    fake_id = uuid4().hex
    source = create_source(input=input, c_a_id=fake_id)
    print(source)
    document = source_to_document(source)
    print(document)
    index_source(source)
    collection_name = source.collection_name_and_assistant_id
    print(collection_name)
    remove_source(source)
    delete_collection(collection_name)
