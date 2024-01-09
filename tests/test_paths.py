import os
from pathlib import Path
from src.path_urls.path_url_utilities import (
    name_to_id,
    create_assistant_dir,
    zip_assistant_dir,
    create_session_dir,
    distinguish_string,
    Source,
)
from src.config_assistant import save_assistant_config


fake_assistant_name = "min/Assistent! 2"

unique_name1 = name_to_id(fake_assistant_name)
print(unique_name1)
assert unique_name1.split("_")[0] == "minAssistent"
unique_name2 = name_to_id(fake_assistant_name)
print(unique_name2)
# should return unique normalized names similar to minAssistent_2_2023-12-22_11-35-31-078619
assert unique_name1 != unique_name2
print("unique assistant name created successfully")

assisten_dir = create_assistant_dir(fake_assistant_name)
print(assisten_dir)
assert os.path.exists(assisten_dir)
print("assistant directory created successfully")

config = {
    "assistant_name": fake_assistant_name,
    "chat_model_name": "gpt",
    "system_prompt": "Du er en robot.",
    "sources": [],
}

save_assistant_config(**config, assistant_dir=assisten_dir)
assert os.path.exists(assisten_dir / "config.yaml")

zip_path = zip_assistant_dir(assisten_dir, delete_directory=True)
print(zip_path)
assert os.path.exists(zip_path)
print("zip file created successfully")

# ensure that the zip file name is not the same as the assistant directory
assert Path(zip_path[:-5]) != assisten_dir
os.remove(zip_path)

config = {
    "assistant_name": "Din assistent",
    "chat_model_name": "gpt",
    "system_prompt": "Du er en robot.",
    "sources": [],
}
save_assistant_config(**config, assistant_dir=assisten_dir)
zip_path = zip_assistant_dir(assisten_dir, delete_directory=True)
assert "Din_assistent" in str(zip_path)
os.remove(zip_path)


session_dir = create_session_dir()
assert os.path.exists(session_dir)
zip_path = zip_assistant_dir(session_dir, delete_directory=True)
os.remove(zip_path)

# Test the url path distinguisher
assert distinguish_string("https://www.example.com") == "URL"
assert distinguish_string("C:\\Users\\username\\Documents\\file.txt") == "File Path"
assert distinguish_string("/home/username/Documents/file.txt") == "File Path"
assert distinguish_string("example.com") == "URL"
assert distinguish_string("example") == "Unknown"

Source("https://www.example.com")
source = Source("data/test_documents/the_origins_of_jazz.txt")
source.getvalue()
