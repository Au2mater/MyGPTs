from pathlib import Path
import yaml
import os
import shutil
from datetime import datetime
import re
from langchain.document_loaders import WebBaseLoader
from streamlit.runtime.uploaded_file_manager import UploadedFile
import gc

# ---------------------------
# core functions


def distinguish_string(input_string):
    """distinguish between url, file path and unknown string"""
    url_pattern = re.compile(
        r"^(http://www\.|https://www\.|http://|https://)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(/.*)?$"
    )
    path_pattern = re.compile(r"[\\/]")

    if url_pattern.match(input_string):
        return "URL"
    elif path_pattern.search(input_string):
        return "File Path"
    else:
        return "Unknown"


# there are two types og sources: urls and streamlit fileuploader files and file paths
# files fetched through streamlits fileupoader are "UploadedFile()" objects
# urls are added through the ui as strings
# the Source class unifies the different types of sources resulting  in a Source object with a name, id and a getvalue() method
# the name of the source is the url itself
class Source:
    def __init__(self, source):
        if isinstance(source, UploadedFile):
            self._from = "fileuploader"
            self.file_object = source
            self.name = source.name
            self.type = source.name.split(".")[-1]
            self.id = name_to_id(self.name) + "." + self.type
            self.filetype = self.type

        elif isinstance(source, str):
            if distinguish_string(source) == "URL":
                self._from = "url"
                self.name = source
                self.type = "url"
                self.id = name_to_id(self.name) + ".txt"
                self.filetype = "txt"

            elif distinguish_string(source) == "File Path":
                self._from = "filepath"
                self.name = remove_path(source)
                self.type = Path(source).suffix[1:]
                self.id = name_to_id(self.name) + "." + self.type
                self.filetype = self.type
                self.frompath = source

            else:
                raise ValueError(f"source {source} is not a valid url or file path")

    def __repr__(self) -> str:
        return (
            "Source: " f"type: {self.type}, " f"name: {self.name}, " f"id: {self.id}."
        )

    def get_content(self):
        """return the content of the source as a string"""
        # for files the name and  getvalue() method are inhereted from the UploadedFile() object
        # for urls the get_value method triggers the load method in WebBaseLoader from langchain.document_loaders
        # WebBaseLoader(url).load()[0].page_content return a string with the page content

        if self._from == "url":
            return WebBaseLoader(self.name).load()[0].page_content
        elif self._from == "fileuploader":
            return self.file_object.getvalue()
        else:  # self._from == "filepath":
            with open(self.frompath, "rb") as f:
                return f.read()

    def save_to(self, directory: str):
        """save the source as a file at the given path"""

        self.filepath = os.path.join(directory, self.id)
        Path(directory).mkdir(exist_ok=True)
        if self._from == "url":
            # saved the url as a text file
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write(self.get_content())
        else:
            with open(self.filepath, "wb") as f:
                f.write(self.get_content())


def create_session_dir(prefix="s"):
    """Create a session directory and return the path to the config file
    knowledge base files , vector db and configuration will be saved in the session directory
    """
    config = {
        "assistant_name": "",
        "chat_model_name": "",
        "system_prompt": "",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    session_dir = Path(f"data/assistants/{name_to_id(str(prefix))}")
    session_dir.mkdir(exist_ok=True)
    config_path = os.path.join(session_dir, "config.yaml")
    with open(config_path, "w", encoding="ISO 8859-15") as f:
        yaml.dump(config, f, encoding="ISO 8859-15", allow_unicode=True)
    return session_dir


# add path to filename if it is a file
def add_path(filename: str, assistant_directory: str):
    """given a filename, add the path to the filename if it is a file"""
    path = os.path.join(assistant_directory, "files", filename)
    if Path(path).exists():
        return path
    else:
        return filename


def remove_path(path: str):
    """given a filename, remove the path to the filename if it is a file"""
    if Path(path).exists():
        filename = Path(path).name
        return filename
    else:
        return path


def file_exists(path: str, directory: str):
    """given a filename, return True if it is a file"""
    path = os.path.join(directory, "files", path)
    return Path(path).exists()


def name_to_id(assistant_name):
    """given an assistant name, create a path legal name for the assistant that is unique"""
    # if the provided assistant already ends with _{datetime.strftime('%Y-%m-%d_%H-%M-%S-%f')}
    # then start by removing this

    if re.search(
        r"_[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{6}$",
        assistant_name,
    ):
        assistant_name = assistant_name[:-(27)]
    id = (
        "".join([c for c in assistant_name if c.isalpha() or c.isdigit() or c == " "])
        .strip()
        .replace(" ", "_")
    )
    id = f"{id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')}"
    return id


# create a legal name for the assistant and create a directory for the assistant
def create_assistant_dir(assistant_name):
    """given an assistant name, create a legal name for the assistant and create a directory for the assistant"""
    assistant_legal_name = name_to_id(assistant_name)
    with Path(f"data/assistants/{assistant_legal_name}") as assistant_dir:
        assistant_dir.mkdir(exist_ok=True)
    return assistant_dir


def zip_assistant_dir(directory, delete_directory=True):
    # zip the db directory and delete the directory
    with open(os.path.join(directory, "config.yaml"), "r") as f:
        assistant_name = yaml.load(f, Loader=yaml.FullLoader)["assistant_name"]
        f.close()
    archive_name = name_to_id(assistant_name)
    archive_path = os.path.join("data", "assistants", archive_name)
    print(f"zipping {directory} to {archive_path}.zip")
    shutil.make_archive(
        base_name=archive_path, format="zip", root_dir=directory
    )  # zip the db directory
    print(f"archive created at {archive_path}.zip")

    if delete_directory:
        print(f"deleting {directory}")
        shutil.rmtree(directory)  # delete the db directory
    # return path to zip file
    return archive_path + ".zip"


def unpack(uploaded_file, destination):
    """
    Given an assistent zip file, unpack the file
    """
    # save the zip file to disk
    with open(f"data/assistants/{uploaded_file.name}", "wb") as f:
        f.write(uploaded_file.read())
    # unzip the file
    if destination:
        shutil.unpack_archive(
            f"data/assistants/{uploaded_file.name}",
            extract_dir=destination,
            format="zip",
        )
        dir = destination
    else:
        new_name = name_to_id(uploaded_file.name[:-4])
        shutil.unpack_archive(
            f"data/assistants/{uploaded_file.name}",
            extract_dir=f"data/assistants/{new_name}",
            format="zip",
        )
        dir = f"data/assistants/{new_name}"

    # delete the zip file
    os.remove(f"data/assistants/{uploaded_file.name}")
    return dir
