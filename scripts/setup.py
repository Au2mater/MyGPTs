import os
import sys
import shutil
from pathlib import Path

# ensure that the import below works when running python scripts\setup.py
if (
    path := os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
) not in sys.path:
    sys.path.append(path)
from src.basic_data_classes import GlobalSetting
from src.sqlite.db_creation import (
    initialize_database_from_dataclasses,
    insert_row,
    reset_table_for_dataclass,
)
import dotenv as de


# make sure the import above works when running python scripts\setup.py


if __name__ == "__main__":
    # set the environment variables to .env file
    # Define the .env file path
    env_path = Path(".") / ".env"

    # set environment variables
    data_directory = str(Path('..\MyGPTs_data').resolve())
    log_file = os.path.join(data_directory, 'logs', 'myGPTs.log')
    main_database_location = os.path.join(data_directory, 'main_db','myGPTs.db')
    vector_db_location = os.path.join(data_directory, 'vector_db') 
    backup_directory = os.path.join(data_directory, 'backup', 'db') 
    temp_file_location = os.path.join(data_directory, 'temp_files')

    # create the directories
    dirs = [data_directory
            , os.path.dirname(log_file)
            , os.path.dirname(main_database_location)
            , vector_db_location
            , backup_directory
            , temp_file_location]
    
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)

    # Write the paths to the .env file
    de.set_key(
        dotenv_path=env_path,
        key_to_set="DATABASE_LOCATION",
        value_to_set=main_database_location,
    )
    de.set_key(
        dotenv_path=env_path,
        key_to_set="VECTOR_DB_LOCATION",
        value_to_set=vector_db_location,
    )
    de.set_key(
        dotenv_path=env_path,
        key_to_set="BACKUP_DIRECTORY",
        value_to_set=backup_directory,
    )
    de.set_key(
        dotenv_path=env_path,
        key_to_set="LOG_FILE",
        value_to_set=log_file,
    )
    de.set_key(
        dotenv_path=env_path,
        key_to_set="TEMP_FILE_LOCATION",
        value_to_set=temp_file_location,
    )

    # Load the variables from the .env file into the environment
    de.load_dotenv(dotenv_path=env_path)

    # backup any existing db and create a new main database in data/db/myGPTs.db and vector database in data/db/myGPTs_vectors.db
    initialize_database_from_dataclasses()

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
    }
    for k, v in global_settings.items():
        global_setting = GlobalSetting(
            id=k, value=str(v), default_value=str(v), type=type(v).__name__
        )
        insert_row(global_setting)
