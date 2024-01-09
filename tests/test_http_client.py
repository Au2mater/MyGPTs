""" create and http chroma client and test creating and deleting an collections using langchain """
import chromadb
from langchain.vectorstores.chroma import Chroma
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.document_loaders import TextLoader
import os
import subprocess
import requests
import yaml


def get_db_config():
    """read the chroma port, embeddings_model, and host from config/vector_db.yaml"""
    with open("config/vector_db.yaml", "r") as f:
        db_config = yaml.load(f, Loader=yaml.FullLoader)
        f.close()
    return db_config


def start_chroma_server():
    # run command chroma run --path data/db --port 8000
    db_path = os.path.join("data", "db")
    db_config = get_db_config()
    port = db_config["port"]
    # test if server is already running
    try:
        response = requests.get(f"http://localhost:{port}/api/v1")
        if response.status_code == 200:
            print("chroma server is already running")
            return
    except:
        pass
    # Define the command you want to run in the new terminal
    command = ["chroma", "run", "--path", db_path, "--port", port]
    # Open a new terminal and run the command
    subprocess.Popen(command)


def start_chroma_client():
    db_condig = get_db_config()
    client = chromadb.HttpClient(host=db_condig["host"], port=db_condig["port"])
    return client


def get_or_create_collection(collection_name, client):
    # create a collection
    model_name = get_db_config()["embeddings_model"]
    embedding_function = SentenceTransformerEmbeddings(model_name=model_name)
    print(f"embeddings model {model_name} loaded")
    collection = Chroma(
        collection_name=collection_name,
        client=client,
        embedding_function=embedding_function,
    )
    return collection


start_chroma_server()
client = start_chroma_client()
collection = get_or_create_collection("test_collection", client)
client.list_collections()
collection._client.get_collection(name="test_collection")._embedding_function
collection.as_retriever(search_type="similarity", search_kwargs={"k": 6})

# add a document to the collection

collection.add_documents(documents=["this is a test document"])
