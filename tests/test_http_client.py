""" create and http chroma client and test creating and deleting an collections using langchain """
from src.chroma_utils import (
    start_chroma_server,
    start_chroma_client,
    get_or_create_collection,

)
from langchain.docstore.document import Document
from pathlib import Path
from src.logging_config import configure_logging

configure_logging()

test_collection_name = "testCollection"

# @pytest.fixture(scope="module", autouse=True)
def document():
    test_doc_dir = Path('data') / 'test_documents'
    # read first document
    with open(test_doc_dir / 'the_origins_of_jazz.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    return Document(page_content=text)

def test_server():
    start_chroma_server()
    assert start_chroma_client(), "chroma http client could not reached/created"


def test_collection():
    client = start_chroma_client()  # if the server is not running, this will fail
    assert client, "chroma http client could not reached/created"
    assert get_or_create_collection(test_collection_name), "collection could not be created"
    assert test_collection_name in [
        col.name for col in client.list_collections()
    ], "collection could not be created"
    assert client.get_collection(name=test_collection_name)


def test_indexing():
    collection = get_or_create_collection(test_collection_name)
    doc = document()
    assert collection.add_documents([doc]), "document could not be added to collection"

def test_deletion():
    client = start_chroma_client()  # if the server is not running, this will fail
    client.delete_collection(name=test_collection_name)
    assert test_collection_name not in [
        col.name for col in client.list_collections()
    ], "collection could not be deleted"


if __name__ == "__main__":
    test_server()
    test_collection()
    test_indexing(document())
    client = start_chroma_client()
    print([c for c in client.list_collections() if 'test' in c.name])
    test_deletion()
