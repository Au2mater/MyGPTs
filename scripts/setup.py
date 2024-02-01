import os
import sys
from pathlib import Path
# ensure that the import below works when running python scripts\setup.py
import dotenv as de

if (
    path := os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
) not in sys.path:
    sys.path.append(path)
from src.basic_data_classes import GlobalSetting
from src.sqlite.db_creation import (
    initialize_database_from_dataclasses,
    insert_row,
    reset_table_for_dataclass,
    execute_query,
)
from src.logging_config import configure_logging


def populate_global_settings():
    # reset the GlobalSettings table
    reset_table_for_dataclass(GlobalSetting)
    # # add global settings to the GlobalSettings table
    global_settings = {
        "max_tokens": 1000,  # max number of tokens to generate
        # "temperature": 0.7,  # [min: 0.0, max: 2.0]
        # system prompt can be changed by the user in the UI
        "default_system_prompt": (
            "Du er en  hjælpsom assistent der hjælper med spørgsmål og svar. "
            "Brug følgende stykker af indhentet kontekst til at besvare spørgsmålet. "
            "Hvis du ikke kender svaret, så sig bare, at du ikke ved det. "
            "Brug maksimalt tre sætninger og hold svaret kortfattet."
        ),
        "default_welcome_message": "Hej, hvad kan jeg hjælpe dig med?",
        "base_url": f"{os.environ['COMPUTERNAME'] }.{os.environ['USERDNSDOMAIN']}",
        "embeddings_model": "intfloat/multilingual-e5-base",
        "online": True,
    }
    for k, v in global_settings.items():
        global_setting = GlobalSetting(
            id=k, value=str(v), default_value=str(v), type=type(v).__name__
        )
        insert_row(global_setting)


def create_views():
    query = """
    CREATE VIEW user_stats AS SELECT 
    users.id, 
    COUNT(assistants.id) AS "number of assistants", 
    MAX(assistants.last_updated) AS "last edit" 
    FROM users 
    LEFT JOIN assistants ON users.id = assistants.owner_id 
    GROUP BY users.id;"""
    execute_query(query)


def set_env_variables():
    env_path = Path(".") / ".env" 
    # set environment variables
    data_directory = Path(r"../MyGPTs_data").resolve()
    log_file = data_directory / "logs" / "myGPTs.log"
    main_database_location = data_directory / "main_db" / "myGPTs.db"
    vector_db_location = data_directory / "vector_db"
    backup_directory = data_directory / "backup" / "db"
    temp_file_location = data_directory / "temp_files"
    chromadb_host = "localhost"
    chromadb_port = 8051
    chromadb_telemetry = False

    # set the environment variables to .env file

    # Write the paths to the .env file
    de.set_key(
        dotenv_path=env_path,
        key_to_set="MAIN_DATABASE_LOCATION",
        value_to_set=str(main_database_location),
        
    )
    de.set_key(
        dotenv_path=env_path,
        key_to_set="VECTOR_DB_LOCATION",
        value_to_set=str(vector_db_location),
    )
    de.set_key(
        dotenv_path=env_path,
        key_to_set="BACKUP_DIRECTORY",
        value_to_set=str(backup_directory),
    )
    de.set_key(
        dotenv_path=env_path,
        key_to_set="LOG_FILE",
        value_to_set=str(log_file),
    )
    de.set_key(
        dotenv_path=env_path,
        key_to_set="TEMP_FILE_LOCATION",
        value_to_set=str(temp_file_location),
    )
    de.set_key(
        dotenv_path=env_path,
        key_to_set="CHROMADB_HOST",
        value_to_set=chromadb_host,
    )
    de.set_key(
        dotenv_path=env_path,
        key_to_set="CHROMADB_PORT",
        value_to_set=str(chromadb_port),
    )
    de.set_key(
        dotenv_path=env_path,
        key_to_set="ANONYMIZED_TELEMETRY",
        value_to_set=str(chromadb_telemetry),
    )

def create_data_directories():
    # load the environment variables from the .env file
    env_path = Path(".") / ".env"
    de.load_dotenv(dotenv_path=env_path)

    dirs = [
        os.environ["VECTOR_DB_LOCATION"],
        os.environ["BACKUP_DIRECTORY"],
    ]
    files = [
        os.environ["LOG_FILE"],
        os.environ["TEMP_FILE_LOCATION"],
        os.environ["MAIN_DATABASE_LOCATION"],
    ]

    for directory in dirs:
        # create the directory if it does not exist
        Path(directory).parent.mkdir(parents=True, exist_ok=True)
        Path(directory).mkdir(exist_ok=True)
    for file in files:
        Path(file).parent.mkdir(exist_ok=True)
        Path(file).touch(exist_ok=True)
        # if the path is a file create it, but do not overwrite it


if __name__ == "__main__":
    set_env_variables()
    create_data_directories()
    configure_logging()
    # backup any existing db and create a new main database in myGPTs.db
    # and vector database in data/db/myGPTs_vectors.db
    initialize_database_from_dataclasses()
    populate_global_settings()
    create_views()
