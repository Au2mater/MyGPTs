import logging
import os
from pathlib import Path
import dotenv as de

def configure_logging():
    # Load the variables from the .env file into the environment
    env_path = Path(".") / ".env"     # Define the .env file path 
    print(env_path)
    de.load_dotenv(dotenv_path=env_path)
    log_file = Path(os.environ.get("LOG_FILE")).resolve()
    print(log_file)
    logging.basicConfig(
        level=logging.INFO,
        filename=log_file,
        filemode="a",  # "a" stands for append, which means new log messages will be added to the end of the file instead of overwriting the existing content
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )