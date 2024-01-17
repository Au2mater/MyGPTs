""" create and http chroma client and test creating and deleting an collections using langchain """
from src.chroma_utils import (
    start_chroma_server,
    start_chroma_client,
    get_or_create_collection,
)
from langchain.docstore.document import Document


def test_server():
    start_chroma_server()
    assert start_chroma_client(), "chroma http client could not reached/created"


def test_collection():
    client = start_chroma_client()  # if the server is not running, this will fail
    assert client, "chroma http client could not reached/created"
    assert get_or_create_collection("testCollection"), "collection could not be created"
    assert "testCollection" in [
        col.name for col in client.list_collections()
    ], "collection could not be created"
    assert client.get_collection(name="testCollection")



def test_indexing():
    collection = get_or_create_collection("testCollection")
    doc = Document(page_content="this is a test document")
    assert collection.add_documents([doc]), "document could not be added to collection"


def test_deletion():
    client = start_chroma_client()  # if the server is not running, this will fail
    client.delete_collection(name="testCollection")
    assert "testCollection" not in [
        col.name for col in client.list_collections()
    ], "collection could not be deleted"


if __name__ == "__main__":
    test_server()
    test_collection()
    test_indexing()
    test_deletion()