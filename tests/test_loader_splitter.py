""" test coverting an inputs to document chunks ready for indexing"""
from src.chroma_utils import (
    start_chroma_server,
    create_source,
    source_to_document,
    split_document,
    get_or_create_collection,
    delete_collection,
    index_source,
    Source,
    Document,
)
from src.sqlite.db_utils import get_assistant_collection
from src.basic_data_classes import Assistant
from src.query_chain import add_context_from_queries
import re
import pytest

img_ref_text_file = 'data/test_documents/Brugervejledning-R0.9.txt'
test_collection_assistant_id = "test_collection_assistant_id"

@pytest.fixture(scope="module" , autouse=True)
def collection():
    try: 
        start_chroma_server()
        collection = get_or_create_collection(test_collection_assistant_id)
    except:
        print("chroma http client could not reached/created")
    
    yield collection
    # delete all test collection
    delete_collection(test_collection_assistant_id)
  


cache = {}
cache["inputs"] = [
    "https://jazzobserver.com/the-origins-of-jazz/",
    "data/test_documents/the_origins_of_jazz.md",
    "data/test_documents/the_origins_of_jazz.txt",
    "data/test_documents/jazz.csv",
    "data/test_documents/influence of jazz on blues.pdf",
    "data/test_documents/popular-song-blues-jazz-and-big-band-topic-exploration-pack.docx"
]


def test_source_creation():
    cache["sources"] = []
    for input in cache["inputs"]:
        source = create_source(input, test_collection_assistant_id)
        assert isinstance(source, Source) and len(source.content) > 10
        cache["sources"].append(source)


def test_source_to_document():
    cache["docs"] = []
    for source in cache["sources"]:
        doc = source_to_document(source)
        assert isinstance(doc, Document) and len(doc.page_content) > 10
        cache["docs"].append(doc)


def test_split_document_basic():
    cache["doc_chunks"] = []
    for doc in cache["docs"]:
        chunks = split_document(document=doc)
        assert len(chunks) > 0 , f"{doc.metadata['name']} not split"
        cache["doc_chunks"].append(chunks)

def test_split_document_uniqueness():
    for doc in cache["docs"]:
        chunks = split_document(document=doc)
        assert len(chunks)  == len(set([c.page_content for c in chunks])) , f"{doc.metadata['name']} not split into unique chunks"

def test_chain_chunks():
    for chunks in cache["doc_chunks"]:
        for chunk in chunks:
            assert chunk.page_content in chunk.metadata['chained_content'] , f"chunk {chunk.metadata['chunk_id']} not in chained content"

def test_img_ref_preservation():
    """ test if chunking and retrieving txt file containing image references preserves the image references"""
    # read file as text and file all references mathcing ![screenshot](<[^\s]+>)
    with open(img_ref_text_file, "r", encoding='utf-8') as f:
        text = f.read()

    image_regex = r"(?<=)(\[.*\]\(\<.*\>\))(?=)"
    images_refs = re.findall(image_regex, text) 
    assert len(images_refs) > 1, "no image references found"

    source = create_source(img_ref_text_file, test_collection_assistant_id)
    # check if all image references were preserved
    for image_ref in images_refs:
        assert image_ref in source.content, f"{image_ref} not found in source content"


def test_chunk_indexing():
    """ test if chunking and indexing of a document works"""
    sources = cache["sources"] 
    for source in sources:
        index_source(source)
    collection = get_assistant_collection(test_collection_assistant_id)
    all_items = collection.get()
    assert  len([c for d in  cache["doc_chunks"] for c in d]) == len(all_items['metadatas']), "not all chunks were indexed"
    keys = [k for k in all_items['metadatas'][0].keys()] 
    assert 'chunk_id' in keys , "chunk_id not in indexed chunks"


def test_add_context_from_queries(collection):
    queries = ["who invented jazz", "when was jazz invented", "what is jazz"]
    test_assistant = Assistant(
        id= test_collection_assistant_id,
        name="test_assistant",
        chat_model_name='local',
        system_prompt="You are a helpful assistant.",
        welcome_message="Hej, hvordan kan jeg hjælpe dig?",
        is_active=True,
        owner_id='testUser',
    )
    messages = [{"role": "assistant", "message": "hvordan kan jeg hjælpe dig?"}
                , {"role": "user", "message": "tell me about jazz"}]
    new_messages = add_context_from_queries(messages=messages, queries=queries, assistant=test_assistant)
    print(new_messages)
    assert len(new_messages) > len(messages), "context could not be added to messages"

def test_add_context_from_zero_queries(collection):
    queries = []
    test_assistant = Assistant(
        id= test_collection_assistant_id,
        name="test_assistant",
        chat_model_name='local',
        system_prompt="You are a helpful assistant.",
        welcome_message="Hej, hvordan kan jeg hjælpe dig?",
        is_active=True,
        owner_id='testUser',
    )
    messages = [{"role": "assistant", "message": "hvordan kan jeg hjælpe dig?"}
                , {"role": "user", "message": "tell me about jazz"}]
    assert add_context_from_queries(messages=messages, queries=queries, assistant=test_assistant)

# if __name__ == "__main__":
#     test_source_creation()
#     test_source_to_document()
#     test_split_document_basic()
#     test_split_document_uniqueness()
#     test_chain_chunks()
#     test_img_ref_preservation()
#     test_chunk_indexing()
    
#     col = get_assistant_collection(test_collection_assistant_id)
#     len(col.get()['metadatas'])

#     test_add_context_from_queries()

#     print("all tests passed")
#     col._client.delete_collection(test_collection_assistant_id)
#     col._client.list_collections()

