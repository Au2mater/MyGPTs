""" utility functions for indexing and retrieval of documents using chroma"""
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
from langchain.document_loaders import (
    TextLoader,
    UnstructuredMarkdownLoader,
    PyPDFLoader,
    CSVLoader,
    WebBaseLoader,
    UnstructuredWordDocumentLoader,
)
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
import multiprocessing
import shutil
import streamlit as st  # for caching
from pathlib import Path
import os
from src.path_urls.path_url_utilities import add_path, remove_path, zip_assistant_dir
import yaml

# ---------------------------
# core functions


def load_document(source: str):
    """given a source path or url, load the source using the appropiate loader and return a Document object
    Accepts: web url, file path to .txt, .csv, .md , .pdf or .docx file
    """
    # map file types to loaders
    loaders = [
        UnstructuredMarkdownLoader,
        TextLoader,
        CSVLoader,
        PyPDFLoader,
        UnstructuredWordDocumentLoader,
        UnstructuredWordDocumentLoader,
    ]
    supported_file_types = ["md", "txt", "csv", "pdf", "docx", "doc"]
    loader_dict = dict(zip(supported_file_types, loaders))

    # 1- determine the type of source
    type = source.split(".")[-1]
    # pdf doesnt take an encoding argument
    if type == "pdf":
        loader = PyPDFLoader(source)
    elif type in supported_file_types:
        loader = loader_dict[type](source, encoding="utf-8")
    else:
        loader = WebBaseLoader(source)
    document = loader.load()
    document[0].metadata["source"] = remove_path(source)
    return document


def split_document(
    document: object, emb_model_name="intfloat/multilingual-e5-base"
) -> list:
    """given a document, split the document into a list of sentences"""
    splitter = SentenceTransformersTokenTextSplitter(model_name=emb_model_name)
    chunks = splitter.split_documents(document)
    return chunks


def create_or_get_db(model_name: str, directory: str = None) -> object:
    """creates Chroma client, with the given model_name
    if directory is None, creates an inmemory client
    if directory is not None, creates a persistent client
    if directory is not None and the directory exists, loads the persistent client
    """
    # loads embeddingsmodel
    embeddings = SentenceTransformerEmbeddings(model_name=model_name)
    # Initialize a ChromaDB client
    if directory:
        db = Chroma(
            persist_directory=directory,
            embedding_function=embeddings,
            collection_name=model_name.replace("/", "_"),
        )
    else:
        db = Chroma(
            embedding_function=embeddings, collection_name=model_name.replace("/", "_")
        )
    return db


def create_retriever(
    model_name: str, collection_name: str, directory: str = None
) -> object:
    """create a retriever with the given model_name and type"""
    db = create_or_get_db(
        model_name=model_name, collection_name=collection_name, directory=directory
    )
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 6})
    return retriever


def index_documents(documents: list, model_name: str, directory: str = None) -> object:
    """given a list of documents, index the documents in a chroma inmemory or persistent client"""
    db = create_or_get_db(model_name=model_name, directory=directory)
    # remove paths from document sources
    for document in documents:
        document.metadata["source"] = remove_path(document.metadata["source"])
    db.add_documents(documents)
    return db


def db_to_retriever(db: object) -> object:
    """given a db, create a retriever"""
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 6})
    return retriever


def get_db_sources(db: object):
    """given a directory, load the db and get the sources from the metadata"""
    metadatas = db.get()["metadatas"]
    sources = list(set([metadata["source"] for metadata in metadatas]))
    return sources


def compare_sources(sources_in: list, sources_out: list):
    """given two lists of sources, return the sources to add and remove"""
    add_sources = list(set(sources_in) - set(sources_out))
    remove_sources = list(set(sources_out) - set(sources_in))
    return add_sources, remove_sources


def delete_source(db: object, source: str):
    """given a db and a source, delete the documents with that source"""
    where = {"source": source}
    remove_ids = db.get(where=where)["ids"]
    try:
        db.delete(remove_ids)
    except:
        print(f"{source} not found")
    # delete from files directory if it's db._persist_directory / files
    files_dir = Path(db._persist_directory) / "files"
    # if the files directory exists, delete the file
    if os.path.exists(files_dir):
        os.remove(files_dir / Path(source).name)


# ----------------------------
# wrapper functions


def update_sources(
    sources_in,
    directory,
    emb_model_name="intfloat/multilingual-e5-base",
    queue=None,
    verbose=False,
):
    """
    given a list of sources, update the db with the sources
    umentioned sources will be deleted
    existing sources will be ignored
    """
    db = create_or_get_db(model_name=emb_model_name, directory=directory)
    print(f"{db._client._count(0)} chunks found in db")
    sources_in = [remove_path(source) for source in sources_in]
    if verbose:
        print(f"{len(sources_in)} sources provided: {sources_in}")
    sources_out = get_db_sources(db)  # return empty list if db is new or empty
    sources_out = [remove_path(source) for source in sources_out]
    print(f"{len(sources_out)} sources found in db: {sources_out}")
    add_sources, remove_sources = compare_sources(
        sources_in=sources_in, sources_out=sources_out
    )
    if len(remove_sources) > 0:
        print(f"deleting {len(remove_sources)} sources")
        for source in remove_sources:
            delete_source(db, source)
    remove_sources = [remove_path(source) for source in remove_sources]
    # index new sources
    if len(add_sources) > 0:
        print(f"indexing {len(add_sources)} sources: {add_sources}")
        add_sources = [add_path(source, directory) for source in add_sources]

        docs = [load_document(source) for source in add_sources]
        print(f"{len(docs)} documents loaded")

        chunks = [chunk for doc in docs for chunk in split_document(document=doc)]
        print(f"{len(chunks)} chunks created")

        db = index_documents(chunks, model_name=emb_model_name, directory=directory)
        print(f"{len(chunks)} chunks indexed")
        add_sources = [remove_path(source) for source in add_sources]
    if queue:
        queue.put((add_sources, remove_sources))
    return add_sources, remove_sources


def update_sources_beta(
    sources_in,
    directory,
    emb_model_name="intfloat/multilingual-e5-base",
    queue=None,
    verbose=False,
):
    """
    given a list of sources, update the db with the sources
    umentioned sources will be deleted
    existing sources will be ignored
    instead of comaparing sources using the database, compare sources using the sources list from the config.yaml file in the directory
    """
    sources_in = [remove_path(source) for source in sources_in]
    if verbose:
        print(f"{len(sources_in)} sources provided: {sources_in}")
    # load the config.yaml file
    with open(os.path.join(directory, "config.yaml"), "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    sources_out = config["sources"]
    sources_out = [remove_path(source) for source in sources_out]
    print(f"{len(sources_out)} sources found in db: {sources_out}")
    add_sources, remove_sources = compare_sources(
        sources_in=sources_in, sources_out=sources_out
    )
    if max(len(add_sources), len(remove_sources)) == 0:
        print("no changes to sources")
        if queue:
            queue.put((add_sources, remove_sources))
        return add_sources, remove_sources
    else:
        db = create_or_get_db(model_name=emb_model_name, directory=directory)
    if len(remove_sources) > 0:
        print(f"deleting {len(remove_sources)} sources")
        for source in remove_sources:
            delete_source(db, source)
    remove_sources = [remove_path(source) for source in remove_sources]
    # index new sources
    if len(add_sources) > 0:
        print(f"indexing {len(add_sources)} sources: {add_sources}")
        add_sources = [add_path(source, directory) for source in add_sources]

        docs = [load_document(source) for source in add_sources]
        print(f"{len(docs)} documents loaded")

        chunks = [chunk for doc in docs for chunk in split_document(document=doc)]
        print(f"{len(chunks)} chunks created")

        db = index_documents(chunks, model_name=emb_model_name, directory=directory)
        print(f"{len(chunks)} chunks indexed")
        add_sources = [remove_path(source) for source in add_sources]
    if queue:
        queue.put((add_sources, remove_sources))
    return add_sources, remove_sources


@st.cache_resource(show_spinner=False)
def retriever_from_sources(
    sources: list,
    emb_model_name: str = "intfloat/multilingual-e5-base",
    directory: str = None,
) -> object:
    """given a url, load the document, split the document, and index the document in a chroma inmemory client retirever"""
    if len(sources) == 0:
        return None
    docs = [load_document(source) for source in sources]
    print(f"{len(docs)} documents loaded")

    chunks = [chunk for doc in docs for chunk in split_document(document=doc)]
    print(f"{len(chunks)} chunks created")

    db = index_documents(chunks, model_name=emb_model_name, directory=directory)
    print(f"{len(chunks)} chunks indexed")
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 6})
    return retriever


def db_from_sources(
    sources: list,
    emb_model_name: str = "intfloat/multilingual-e5-base",
    directory: str = None,
) -> object:
    """given a url, load the document, split the document, and index the document in a chroma inmemory client retirever"""
    if len(sources) == 0:
        return None
    docs = [load_document(source) for source in sources]
    print(f"{len(docs)} documents loaded")

    chunks = [chunk for doc in docs for chunk in split_document(document=doc)]
    print(f"{len(chunks)} chunks created")

    db = index_documents(chunks, model_name=emb_model_name, directory=directory)
    print(f"{len(chunks)} chunks indexed")
    return db


def zipdb_from_sources(sources: list, directory: str, delete_directory: bool = True):
    """create a zipped chroma db from a list of sources
    input:
    sources: list of urls or file paths of type .txt, .csv, .md , .pdf or .docx
    directory: path to directory where the db will be stored
    if directory is existing, it's contents will be added to the archive
    returns: path to zip file
    """
    if directory is None:
        print("no directory provided!")
    if len(sources) > 0:
        p = multiprocessing.Process(
            target=db_from_sources, args=(sources,), kwargs={"directory": directory}
        )
        p.start()  # start the process
        p.join()  # wait for process to finish
    shutil.make_archive(directory, "zip", directory)  # zip the db directory
    if delete_directory:
        shutil.rmtree(directory)  # delete the db directory
    # return path to zip file
    return f"{str(directory)}.zip"


@st.cache_resource(show_spinner=False)
def retriever_from_zipdb(zipdb_path: str):
    """given a path to a zipped chroma db, load the db and create a retriever"""
    # unzip the db archive to a folder named after the archive
    zippath = Path(zipdb_path)
    directory = f"data/assistants/{zippath.name}"
    shutil.unpack_archive(zipdb_path, extract_dir=directory, format="zip")
    db = create_or_get_db(
        model_name="intfloat/multilingual-e5-base", directory=directory
    )
    # create retriever
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    # delete the archive file
    # os.remove(zipdb_path)
    return retriever


@st.cache_resource(show_spinner=False)
def retriever_from_directory(directory: str):
    """given a path to a chroma db directory, load the db and create a retriever"""
    db = create_or_get_db(
        model_name="intfloat/multilingual-e5-base", directory=directory
    )
    # create retriever
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    return retriever


# update directory with new sources
# given a directory and a list of sources do the following
# 1 - check to see if a chroma instance exists in the directory
# 2 - if not, zipdb from sources
# 3 - if it does, load the db and check existing sources
# 4 - index new docs , delete absent docs, ignore existing docs in both source list and database
# zip, delete and return the zip path


def zipupdate_directory_with_sources(
    directory: str, sources: list, delete_directory: bool = True
):
    """given a directory and a list of sources, update the directory with the sources"""
    if directory is None:
        print("no directory provided!")
        return None
    # update the db with the sources
    queue = multiprocessing.Queue()
    p = multiprocessing.Process(
        target=update_sources,
        kwargs={"sources_in": sources, "directory": directory, "queue": queue},
    )
    p.start()  # start the process
    p.join()  # wait for process to finish
    result = queue.get()  # get the result
    add_sources, remove_sources = result
    # zip the db directory and delete the directory
    zip_path = zip_assistant_dir(
        Path(directory),
        delete_directory=delete_directory,
    )
    report = {
        "add_sources": add_sources,
        "remove_sources": remove_sources,
        "zip_path": zip_path,
    }
    return report
