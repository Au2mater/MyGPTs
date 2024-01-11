""" create and http chroma client and test creating and deleting an collections using langchain """
from src.chroma.chroma_utils import start_chroma_server, start_chroma_client, get_or_create_collection
from langchain.docstore.document import Document
start_chroma_server()
assert start_chroma_client() , "chroma http client could not reached/created"
client = start_chroma_client() # if the server is not running, this will fail
assert client , "chroma http client could not reached/created"
assert get_or_create_collection("test_collection") , "collection could not be created"
collection = get_or_create_collection("test_collection")
assert "test_collection" in [col.name for col in client.list_collections()] , "collection could not be created"
assert client.get_collection(name="test_collection")
doc = Document(page_content="this is a test document")
assert collection.add_documents([doc]) , "document could not be added to collection"
client.delete_collection(name="test_collection")

