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
from streamlit.runtime.uploaded_file_manager import UploadedFile
import os
from pydantic import BaseModel, Field, ConfigDict
from pydantic.types import Literal, FilePath
from pydantic.networks import AnyHttpUrl
from pathlib import Path, WindowsPath
from typing import Union
from pydantic_core import Url
from streamlit.runtime.uploaded_file_manager import UploadedFile
from datetime import datetime
from uuid import uuid4

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
    except:
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
    retrieved_docs = retriever.get_relevant_documents(prompt, top_k=top_k)
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


# input to source
class Source(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str = Field(min_length=1, max_length=1000)
    source_type: Literal["url", "file path", "uploaded file"]
    creation_time: datetime = Field(default_factory=datetime.now)
    content_type: Literal["txt", "pdf", "csv", "docx", "doc", "md", "url"] = "txt"
    content: str = Field(min_length=1, max_length=500000)
    collection_name_and_assistant_id: str = Field(min_length=1, max_length=100)


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
    # convert creation time to string
    src.creation_time = src.creation_time.strftime("%Y-%m-%d %H:%M:%S")
    document = Document(page_content=src.content, metadata=src.model_dump())
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
    collection.add_documents(
        chunks,
    )
    print(f"{source.name} indexed into {len(chunks)} chunks")


def remove_source(source: Source):
    """given a source, remove the source chunks from the named collection using a chroma http client"""
    where = {"id": source.id}
    collection = get_collection(collection_name=source.collection_name_and_assistant_id)
    remove_ids = collection.get(where=where)["ids"]
    try:
        collection.delete(remove_ids)
    except:
        print(f"{source.name} not found")


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


# ----------------------------
# legacy functions
# ----------------------------
# wrapper functions

# def db_to_retriever(db: object) -> object:
#     """given a db, create a retriever"""
#     retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 6})
#     return retriever


# def index_source(source : Source):
#     """given a source, load the source, split the source,
#     and index the source in the named collection using a chroma http client"""
#     # load the document
#     document = load_document(source)
#     # split the document
#     chunks = split_document(document)
#     # index the document
#     collection = get_or_create_collection(collection_name=collection_name)
#     collection.add_documents(
#         chunks,
#     )
#     print(f"{len(chunks)} chunks indexed")


# def remove_sources(
#     directory: str,
#     sources_to_remove: list,
#     emb_model_name: str = "intfloat/multilingual-e5-base",
# ):
#     """given a directory and a list of sources, delete the sources from the directory"""
#     db = create_or_get_db(model_name=emb_model_name, directory=directory)
#     for source in sources_to_remove:
#         delete_source(db, source)


# def update_index(
#     sources_to_add: list = [],  # list of Source objects
#     sources_to_remove: list = [],  # list of source ids (str)
#     emb_model_name: str = "intfloat/multilingual-e5-base",
#     directory: str = None,
#     db=None,
# ) -> None:
#     """given a list of Source objects,load as documents, split and index the document in a chroma persistent client"""
#     directory = str(directory)  # convert path to string
#     if len(sources_to_add) > 0:
#         docs = [load_document(source) for source in sources_to_add]
#         print(f"{len(docs)} documents loaded")

#         chunks = [chunk for doc in docs for chunk in split_document(document=doc)]
#         print(f"{len(chunks)} chunks created")

#         index_documents(chunks, model_name=emb_model_name, directory=directory)
#         p = multiprocessing.Process(
#             target=index_documents,
#             kwargs={
#                 "documents": chunks,
#                 "model_name": emb_model_name,
#                 "directory": directory,
#             },
#         )
#         p.start()  # start the process
#         p.join()  # wait for process to finish
#         print(f"{len(chunks)} chunks indexed")

#     if len(sources_to_remove) > 0:
#         # db = create_or_get_db(model_name=emb_model_name, directory=directory)
#         # for source in sources_to_remove:
#         #     delete_source(db, source)
#         p = multiprocessing.Process(
#             target=remove_sources,
#             kwargs={
#                 "directory": directory,
#                 "sources_to_remove": sources_to_remove,
#                 "emb_model_name": emb_model_name,
#             },
#         )
#         p.start()  # start the process
#         p.join()  # wait for process to finish
#         print(f"{len(sources_to_remove)} sources removed")


# def update_sources(
#     sources_in,
#     directory,
#     emb_model_name="intfloat/multilingual-e5-base",
#     queue=None,
#     verbose=False,
# ):
#     """
#     given a list of sources, update the db with the sources
#     unmentioned sources will be deleted
#     existing sources will be ignored
#     """
#     db = create_or_get_db(model_name=emb_model_name, directory=directory)
#     print(f"{db._client._count(0)} chunks found in db")
#     sources_in = [remove_path(source) for source in sources_in]
#     if verbose:
#         print(f"{len(sources_in)} sources provided: {sources_in}")
#     sources_out = get_db_sources(db)  # return empty list if db is new or empty
#     sources_out = [remove_path(source) for source in sources_out]
#     print(f"{len(sources_out)} sources found in db: {sources_out}")
#     add_sources, remove_sources = compare_sources(
#         sources_in=sources_in, sources_out=sources_out
#     )
#     if len(remove_sources) > 0:
#         print(f"deleting {len(remove_sources)} sources")
#         for source in remove_sources:
#             delete_source(db, source)
#     remove_sources = [remove_path(source) for source in remove_sources]
#     # index new sources
#     if len(add_sources) > 0:
#         print(f"indexing {len(add_sources)} sources: {add_sources}")
#         add_sources = [add_path(source, directory) for source in add_sources]

#         docs = [load_document(source) for source in add_sources]
#         print(f"{len(docs)} documents loaded")

#         chunks = [chunk for doc in docs for chunk in split_document(document=doc)]
#         print(f"{len(chunks)} chunks created")

#         db = index_documents(chunks, model_name=emb_model_name, directory=directory)
#         print(f"{len(chunks)} chunks indexed")
#         add_sources = [remove_path(source) for source in add_sources]
#     if queue:
#         queue.put((add_sources, remove_sources))
#     return add_sources, remove_sources


# @st.cache_resource(show_spinner=False)
# def retriever_from_sources(
#     sources: list,
#     emb_model_name: str = "intfloat/multilingual-e5-base",
#     directory: str = None,
# ) -> object:
#     """given a url, load the document, split the document, and index the document in a chroma inmemory client retirever"""
#     if len(sources) == 0:
#         return None
#     docs = [load_document(source) for source in sources]
#     print(f"{len(docs)} documents loaded")

#     chunks = [chunk for doc in docs for chunk in split_document(document=doc)]
#     print(f"{len(chunks)} chunks created")

#     db = index_documents(chunks, model_name=emb_model_name, directory=directory)
#     print(f"{len(chunks)} chunks indexed")
#     retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 6})
#     return retriever


# def db_from_sources(
#     sources: list,
#     emb_model_name: str = "intfloat/multilingual-e5-base",
#     directory: str = None,
# ) -> object:
#     """given a url, load the document, split the document, and index the document in a chroma inmemory client retirever"""
#     if len(sources) == 0:
#         return None
#     docs = [load_document(source) for source in sources]
#     print(f"{len(docs)} documents loaded")

#     chunks = [chunk for doc in docs for chunk in split_document(document=doc)]
#     print(f"{len(chunks)} chunks created")

#     db = index_documents(chunks, model_name=emb_model_name, directory=directory)
#     print(f"{len(chunks)} chunks indexed")
#     return db


# def zipdb_from_sources(sources: list, directory: str, delete_directory: bool = True):
#     """create a zipped chroma db from a list of sources
#     input:
#     sources: list of urls or file paths of type .txt, .csv, .md , .pdf or .docx
#     directory: path to directory where the db will be stored
#     if directory is existing, it's contents will be added to the archive
#     returns: path to zip file
#     """
#     if directory is None:
#         print("no directory provided!")
#     if len(sources) > 0:
#         p = multiprocessing.Process(
#             target=db_from_sources, args=(sources,), kwargs={"directory": directory}
#         )
#         p.start()  # start the process
#         p.join()  # wait for process to finish
#     shutil.make_archive(directory, "zip", directory)  # zip the db directory
#     if delete_directory:
#         shutil.rmtree(directory)  # delete the db directory
#     # return path to zip file
#     return f"{str(directory)}.zip"


# @st.cache_resource(show_spinner=False)
# def retriever_from_zipdb(zipdb_path: str):
#     """given a path to a zipped chroma db, load the db and create a retriever"""
#     # unzip the db archive to a folder named after the archive
#     zippath = Path(zipdb_path)
#     directory = f"data/assistants/{zippath.name}"
#     shutil.unpack_archive(zipdb_path, extract_dir=directory, format="zip")
#     db = create_or_get_db(
#         model_name="intfloat/multilingual-e5-base", directory=directory
#     )
#     # create retriever
#     retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 5})
#     # delete the archive file
#     # os.remove(zipdb_path)
#     return retriever


# @st.cache_resource(show_spinner=False)
# def retriever_from_directory(directory: str):
#     """given a path to a chroma db directory, load the db and create a retriever"""
#     db = create_or_get_db(
#         model_name="intfloat/multilingual-e5-base", directory=directory
#     )
#     # create retriever
#     retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 5})
#     return retriever


# update directory with new sources
# given a directory and a list of sources do the following
# 1 - check to see if a chroma instance exists in the directory
# 2 - if not, zipdb from sources
# 3 - if it does, load the db and check existing sources
# 4 - index new docs , delete absent docs, ignore existing docs in both source list and database
# zip, delete and return the zip path


# def zipupdate_directory_with_sources(
#     directory: str, sources: list, delete_directory: bool = True
# ):
#     """given a directory and a list of sources, update the directory with the sources"""
#     if directory is None:
#         print("no directory provided!")
#         return None
#     # update the db with the sources
#     queue = multiprocessing.Queue()
#     p = multiprocessing.Process(
#         target=update_sources,
#         kwargs={"sources_in": sources, "directory": directory, "queue": queue},
#     )
#     p.start()  # start the process
#     p.join()  # wait for process to finish
#     result = queue.get()  # get the result
#     add_sources, remove_sources = result
#     # zip the db directory and delete the directory
#     zip_path = zip_assistant_dir(
#         Path(directory),
#         delete_directory=delete_directory,
#     )
#     report = {
#         "add_sources": add_sources,
#         "remove_sources": remove_sources,
#         "zip_path": zip_path,
#     }
#     return report


# def create_or_get_db(model_name: str, directory: str = None) -> object:
#     """creates Chroma client, with the given model_name
#     if directory is None, creates an inmemory client
#     if directory is not None, creates a persistent client
#     if directory is not None and the directory exists, loads the persistent client
#     """
#     start_chroma_server()
#     client = start_chroma_client()
#     # loads embeddingsmodel
#     embeddings = SentenceTransformerEmbeddings(model_name=model_name)
#     print(f"embeddings model {model_name} loaded")
#     # Initialize a ChromaDB client
#     if directory:
#         db = Chroma(
#             persist_directory=directory,
#             embedding_function=embeddings,
#             collection_name=model_name.replace("/", "_"),
#         )
#     else:
#         db = Chroma(
#             embedding_function=embeddings, collection_name=model_name.replace("/", "_")
#         )
#     return db

# def load_document(source: Source):
#     """given a source path or url, load the source using the appropiate loader and return a Document object
#     Accepts: web url, file path to .txt, .csv, .md , .pdf or .docx file
#     """
#     # map file types to loaders
#     loaders = [
#         UnstructuredFileIOLoader,
#         WebBaseLoader,
#     ]
#     supported_file_types = ["md", "txt", "csv", "pdf", "docx", "doc"]
#     loader_dict = dict(zip(supported_file_types, loaders))
#     file_path = source.filepath
#     # 1- determine the type of source

#     # pdf doesnt take an encoding argument
#     if source.filetype == "pdf":
#         loader = PyPDFLoader(file_path)
#     elif source.filetype in supported_file_types:
#         loader = loader_dict[source.filetype](file_path, encoding="utf-8")
#     else:
#         loader = WebBaseLoader(file_path)
#     document = loader.load()[0]
#     document.metadata["source"] = remove_path(file_path)
#     document.metadata["id"] = source.id
#     return document

# def get_db_sources(db: object):
#     """given a directory, load the db and get the sources from the metadata"""
#     metadatas = db.get()["metadatas"]
#     sources = list(set([metadata["source"] for metadata in metadatas]))
#     return sources


# def compare_sources(sources_in: list, sources_out: list):
#     """given two lists of sources, return the sources to add and remove"""
#     add_sources = list(set(sources_in) - set(sources_out))
#     remove_sources = list(set(sources_out) - set(sources_in))
#     return add_sources, remove_sources


# def index_chunks(
#     documents: list, model_name: str, directory: str = None, db=None
# ) -> object:
#     """given a list of documents, index the documents in a chroma inmemory or persistent client"""
#     print("loading database...")
#     if db is None:
#         db = create_or_get_db(model_name=model_name, directory=directory)
#         print("database loaded successlfully")
#     # remove paths from document sources
#     for document in documents:
#         document.metadata["source"] = remove_path(document.metadata["source"])
#     db.add_documents(documents)
#     return db
