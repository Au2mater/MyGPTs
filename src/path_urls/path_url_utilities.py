from pathlib import Path
import yaml
import os
import shutil
from datetime import datetime

# ---------------------------
# core functions


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


def unique_assistent_name(assistant_name):
    """given an assistant name, create a path legal name for the assistant that is unique"""
    # if the provided assistant already ends with _{datetime.strftime('%Y-%m-%d_%H-%M-%S-%f')}
    # then start by removing this
    import re

    if re.search(
        r"_[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{6}$",
        assistant_name,
    ):
        assistant_name = assistant_name[:-(27)]
    assistant_legal_name = (
        "".join([c for c in assistant_name if c.isalpha() or c.isdigit() or c == " "])
        .strip()
        .replace(" ", "_")
    )
    assistant_legal_name = (
        f"{assistant_legal_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')}"
    )
    return assistant_legal_name


# create a legal name for the assistant and create a directory for the assistant
def create_assistant_dir(assistant_name):
    """given an assistant name, create a legal name for the assistant and create a directory for the assistant"""
    assistant_legal_name = unique_assistent_name(assistant_name)
    assistent_dir = Path(f"data/assistants/{assistant_legal_name}")
    assistent_dir.mkdir(exist_ok=True)
    return assistent_dir


def zip_assistant_dir(directory, delete_directory=True):
    # zip the db directory and delete the directory
    with open(os.path.join(directory, "config.yaml"), "r") as f:
        assistant_name = yaml.load(f, Loader=yaml.FullLoader)["assistant_name"]
    archive_name = unique_assistent_name(assistant_name)
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


def unpack(uploaded_file):
    """
    Given an assistent zip file, unpack the file
    """
    # save the zip file to disk
    with open(f"data/assistants/{uploaded_file.name}", "wb") as f:
        f.write(uploaded_file.read())
    # unzip the file
    new_name = unique_assistent_name(uploaded_file.name[:-4])
    shutil.unpack_archive(
        f"data/assistants/{uploaded_file.name}",
        extract_dir=f"data/assistants/{new_name}",
        format="zip",
    )
    # delete the zip file
    os.remove(f"data/assistants/{uploaded_file.name}")
    # load the config file
    dir = f"data/assistants/{new_name}"
    return dir
