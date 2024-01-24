""" test coverting an inputs to document chunks ready for indexing"""
from src.chroma_utils import (
    create_source,
    source_to_document,
    split_document,
    Source,
    Document,
)

cache = {}
cache["inputs"] = [
    "https://jazzobserver.com/the-origins-of-jazz/",
    "data/test_documents/the_origins_of_jazz.md",
    "data/test_documents/the_origins_of_jazz.txt",
    "data/test_documents/jazz.csv",
    "data/test_documents/influence of jazz on blues.pdf",
    "data/test_documents/popular-song-blues-jazz-and-big-band-topic-exploration-pack.docx",
    "data/test_documents/Barnets lov.docx"
]
test_collection_assistant_id = "test_collection_assistant_id"


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


def test_split_document_1():
    cache["doc_chunks"] = []
    for doc in cache["docs"]:
        chunks = split_document(document=doc)
        assert len(chunks) > 0 , f"{doc.metadata['name']} not split"
        cache["doc_chunks"].append(chunks)

def test_split_document_2():
    for doc in cache["docs"]:
        chunks = split_document(document=doc)
        assert len(chunks)  == len(set([c.page_content for c in chunks])) , f"{doc.metadata['name']} not split into unique chunks"

def test_chain_chunks():
    for chunks in cache["doc_chunks"]:
        for chunk in chunks:
            assert chunk.page_content in chunk.metadata['chained_content'] , f"chunk {chunk.metadata['chunk_id']} not in chained content"


if __name__ == "__main__":
    test_source_creation()
    test_source_to_document()
    test_split_document_1()
    test_split_document_2()
    test_chain_chunks()
    print("all tests passed")

