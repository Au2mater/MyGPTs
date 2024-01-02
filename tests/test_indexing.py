from src.chroma.chroma_utils import (
    load_document,
    split_document,
    index_documents,
    retriever_from_sources,
)
from src.chroma.chroma_utils import db_from_sources, zipdb_from_sources
from pathlib import Path

sources = [
    "https://jazzobserver.com/the-origins-of-jazz/",
    "data/test_documents/the_origins_of_jazz.md",
    "data/test_documents/the_origins_of_jazz.txt",
]

sources = ["https://jazzobserver.com/the-origins-of-jazz/"]
directory = Path(r"data\assistants\j5_2023-12-21_00-48-51")
db = db_from_sources(sources, directory="data/assistants/J5_2023-12-21_00-34-29")
zippath = zipdb_from_sources(sources, directory=directory)
# test single steps
# 1- load document
docs = [load_document(source) for source in sources]
# 2- split document
chunks = [chunk for doc in docs for chunk in split_document(document=doc)]
print(f"{len(chunks)} chunks created")
print(chunks[0].metadata["source"])

# 3a- index document to inmmemory db
db = index_documents(chunks, model_name="intfloat/multilingual-e5-base")
# 4a- create retriever
retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})
# 5a- retrieve documents
query = "Hvem opfandt jazz?"
retrieved_docs = retriever.get_relevant_documents(query)
print(retrieved_docs)

# 3b- index document to persistent db
db = index_documents(
    chunks, model_name="intfloat/multilingual-e5-base", directory="data/chroma_db"
)
# 4b- create retriever
retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})
# 5b- retrieve documents
query = "Hvem opfandt jazz?"
retrieved_docs = retriever.get_relevant_documents(query)
print(retrieved_docs)


# test wrapper functions
# load, split, index, and create retriever at once
# A- inmemory
retriever = retriever_from_sources(sources)
query = "Hvem opfandt jazz?"

retrieved_docs = retriever.get_relevant_documents(query)
print(retrieved_docs)

# B- persistent
retriever = retriever_from_sources(sources, directory="data/chroma_db")
query = "Hvem opfandt jazz?"

retrieved_docs = retriever.get_relevant_documents(query)
print(retrieved_docs)

# archive the chroma db folder into a zip file
import shutil

shutil.make_archive("data/chroma_db", "zip", "data/chroma_db")
# delete the chroma db folder
shutil.rmtree("data/chroma_db")
