from src.chroma.chroma_utils import (
    create_or_get_db,
    get_db_sources,
    compare_sources,
    delete_source,
    update_sources,
    zipupdate_directory_with_sources,
)
from src.path_urls.path_url_utilities import add_path

sources_in = [
    "influence of jazz on blues.pdf",
    "https://jazzobserver.com/the-origins-of-jazz/",
]

# test with existing directory
assistant_dir = "data/assistants/g5_2023-12-21_10-52-35"
zipupdate_directory_with_sources(assistant_dir, sources_in, delete_directory=False)

db = create_or_get_db(
    model_name="intfloat/multilingual-e5-base", directory=assistant_dir
)
delete_source(db, "influence of jazz on blues copy.pdf")
# get all db object attributes

sources_out = get_db_sources(db)
add_sources, remove_sources = compare_sources(
    sources_in=sources_in, sources_out=sources_out
)
for source in remove_sources:
    delete_source(db, source)

# test with new directory
assistant_dir = "data/assistants/new_assistant"
db = create_or_get_db(
    model_name="intfloat/multilingual-e5-base", directory=assistant_dir
)
sources_out = get_db_sources(db)
add_sources, remove_sources = compare_sources(
    sources_in=sources_in, sources_out=sources_out
)
print(add_sources, remove_sources)
for source in remove_sources:
    delete_source(db, source)
