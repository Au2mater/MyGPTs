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
    database_location = str(Path("data/db/myGPTs.db").resolve())
    vector_db_location = str(Path("data/vector_db").resolve())
    backup_directory = str(Path("backup/db").resolve())

    # Write the paths to the .env file
    de.set_key(
        dotenv_path=env_path,
        key_to_set="DATABASE_LOCATION",
        value_to_set=database_location,
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

    # Load the variables from the .env file into the environment
    de.load_dotenv(dotenv_path=env_path)
    # copy the .env file to the app_gov folder
    # shutil.copy(env_path, Path("app/.env").resolve())

    # backup any existing db and create a new main database in data/db/myGPTs.db and vector database in data/db/myGPTs_vectors.db
    initialize_database_from_dataclasses()

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
    }
    for k, v in global_settings.items():
        global_setting = GlobalSetting(
            id=k, value=str(v), default_value=str(v), type=type(v).__name__
        )
        insert_row(global_setting)
