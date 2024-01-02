""" create an assistant configuration package consisting of a systemprompt, an assistant name, and an optional list of resources."""
import yaml
from datetime import datetime
from pathlib import Path
import streamlit as st
import os

# from pydantic import BaseModel , field_validator, computed_field, property
# save the configuration above to a yaml file, named after the assistant and the current date and time
# use the data/assistants folder to store the configuration

emojis = [
    "🧑",
    "🧔",
    "🧒",
    "👱‍♀️",
    "👨‍🦰",
    "👨‍🦱",
    "👨‍🦲",
    "👩",
    "👩‍🦰",
    "👩‍🦱",
    "🧕",
    "🤵",
    "👨‍🦳",
    "👩‍🦳",
    "👧",
    "👲",
    "🧓",
    "👨",
    "👴",
    "👵",
    "🤹",
    "🙎",
    "🧝",
    "🧚‍♀️",
    "🧛‍♀️",
    "🧝‍♂️",
    "🧝‍♀️",
    "🧞‍♂️",
    "🧞‍♀️",
    "🧏‍♂️",
    "👮",
    "👩",
    "🧚‍♂️",
    "👨‍🎓",
    "👩‍🎓",
    "🧑",
    "👨‍🍳",
    "👩‍🍳",
    "🧑",
    "🕵️",
    "🦸",
    "🦹",
    "🧙",
    "🧙‍♀️",
    "🧚",
    "🙎‍♂️",
    "🙎‍♀️",
    "👨‍🏫",
    "👩‍🏫",
    "👨‍🌾",
    "👩‍🌾",
    "👨‍🎨",
    "👩‍🎨",
    "👨‍✈️",
    "👩‍✈️",
    "👨‍🚀",
    "👩‍🚀",
    "👨‍🚒",
    "👩‍🚒",
    "👷",
    "💆‍♂️",
    "💆‍♀️",
    "🦸‍♂️",
    "🦸‍♀️",
    "👨‍⚕️",
    "👩‍⚕️",
    "👨‍⚖️",
    "👩‍⚖️",
    "👨‍🏭",
    "👩‍🏭",
    "👨‍💼",
    "👩‍💼",
    "🤹‍♀️",
    "💁‍♂️",
    "💁‍♀️",
    "👨‍🔧",
    "👩‍🔧",
    "👨‍🔬",
    "👩‍🔬",
    "👷‍♀️",
    "🎅",
]

file_types = [".txt", ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv", ".md"]

# class KnowledgeSource(BaseModel):
#     """Text containing files to be indexed in the knowledge base"""
#     path: Path
#     created_at: datetime = datetime.now()

#     @computed_field
#     @property
#     def name(self) -> str:
#         return self.path.name

#     @computed_field
#     @property
#     def extension(self)-> str:
#         return self.path.suffix
#     # validate file extension

#     @field_validator('path')
#     def validate_extension(cls, v):
#         if v.suffix not in file_types:
#             raise ValueError(f"Invalid file extension: {v}")
#         return v


# class AssistantConfig(BaseModel):
#     assistant_name: str
#     assistant_avatar: str = '🕵️'
#     chat_model_name: str
#     system_prompt: str = "You are a helpful assistant."
#     sources: list[KnowledgeSource] = []
#     created_at: datetime = datetime.now()

#     @computed_field
#     @property
#     def id(self) -> str:
#         """given an assistant name, create a path legal name for the assistant that is unique"""
#         assistant_legal_name = "".join([c for c in self.assistant_name
#                                         if c.isalpha() or c.isdigit() or c==' ']).strip().replace(' ', '_')
#         assistant_legal_name = f"{assistant_legal_name}_{self.created_at.strftime('%Y-%m-%d_%H-%M-%S-%f')}"
#         return assistant_legal_name

# AssistantConfig(assistant_name="test", chat_model_name="test")


def save_assistant_config(
    assistant_name,
    chat_model_name,
    system_prompt,
    sources,
    assistant_dir,
    assistant_avatar=emojis[0],
):
    """given an assistant name, a chat model name, a system prompt, and a list of sources
    save the configuration to a yaml file, named after the assistant and the current date and time
    use the data/assistants folder to store the configuration"""

    # remove paths for files in sources, leave urls unchanged
    _sources = list(
        set(
            [
                str(Path(source).name) if Path(source).is_file() else source
                for source in sources
            ]
        )
    )

    config = {
        "assistant_name": assistant_name,
        "chat_model_name": chat_model_name,
        "system_prompt": system_prompt,
        "sources": _sources,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    save_path = Path(assistant_dir)
    save_path.mkdir(exist_ok=True)
    save_path = save_path / f"config.yaml"
    with open(save_path, "w", encoding="ISO 8859-15") as f:
        yaml.dump(config, f, encoding="ISO 8859-15", allow_unicode=True)

    return config


def load_assistant_config(assistant_dir):
    """given a save_path, load the configuration from the yaml file"""
    with open(os.path.join(assistant_dir, "config.yaml"), "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


def display_config(config):
    """given a configuration, display the configuration"""
    st.markdown(f"assistentens name: {config['assistant_name']}")
    st.markdown(f"model: {config['chat_model_name']}")
    st.markdown(f"grundvilkår: {config['system_prompt']}")
    st.markdown(f"kilder: {config['sources']}")
    st.markdown(f"oprettet: {config['created_at']}")


# path , config = save_assistant(assistant_name, chat_model_name, system_prompt, sources)

# load_assistant(path)
