import streamlit as st
from random import randint
from uuid import uuid4
import os
import sys

if (
    path := os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
) not in sys.path:
    sys.path.append(path)
# add root directory to path for relative import
from src.sqlite.db_utils import (
    get_user_assistants,
    get_assistant_sources,
    delete_assistant,
    get_active_llms,
    get_base_url,
)
from src.streamlit_utils import init, get, set_to
from src.basic_data_classes import Assistant, User
from src.sqlite.gov_db_utils import get_global_setting


def go_back():
    """discard changes and go back to my assistants page"""
    set_to("session_sources", [])
    set_to("sources_to_add", [])
    set_to("page", "my assistants")


def go_to_edit_assistant_page(assistant: Assistant = None):
    active_llms = get_active_llms()
    if len(active_llms) == 0:
        st.error(
            "Der er ingen chat modeller tilgængelige i øjeblikket. Kontakt en administrator for at få hjælp."
        )
        return
    set_to("page", "create assistant")
    if assistant is None:
        assistant = Assistant(
            name=(
                "Din Assistent " + str(int(len(get_user_assistants(get("user")))) + 1)
            ),
            owner_id=get("user").id,
            id=uuid4().hex,
            chat_model_name=active_llms[0].name,
            system_prompt=get_global_setting("default_system_prompt").value,
            welcome_message=get_global_setting("default_welcome_message").value,
        )

    set_to("current_assistant", assistant)
    set_to("indexed_sources", get_assistant_sources(assistant.id))
    set_to("session_sources", get_assistant_sources(assistant.id))
    set_to("sources_to_add", [])
    set_to("sources_to_delete", [])


def show_assistant_share_link(assistant):
    link = f"{get_base_url()}:8501/myGPT/?shared_assistant_id={assistant.id}"
    st.success(
        f"Alle kan nu chatte med __{assistant.name}__ på dette  [__link__]({link}) "
    )


def confirm_and_delete_assistant(assistant):
    st.error(
        f"Er du sikker på, at du vil slette {assistant.name}? Denne handling kan ikke fortrydes."
    )
    with st.container():
        c1, c2, _ = st.columns([1, 1, 1])
        c1.button(
            "Ja, slet assistenten",
            key="confirm_delete",
            on_click=delete_assistant,
            args=(assistant.id,),
            use_container_width=True,
        )
        c2.button(
            "Nej, behold assistenten",
            key="cancel_delete",
            on_click=go_back,
            use_container_width=True,
        )


def go_to_chat_assistant_page(assistant: Assistant):
    set_to("page", "chat")
    set_to("current_assistant", assistant)
    set_to(
        "messages",
        [
            {"role": "system", "content": assistant.system_prompt},
            {"role": "assistant", "content": assistant.welcome_message},
        ],
    )
    set_to("number_of_sources", len(get_assistant_sources(assistant.id)))

# UI


def mine_assistenter_page():
    st.title("Mine Assistenter")
    if get("user").id == "::1":
        st.button('← Gå til admin side'
                , on_click=set_to
                , args=('page', 'admin_home')
                    )
    with st.container(border=True):
        # create assistant button
        st.button(
            label=":heavy_plus_sign: __Opret ny assistent__",
            use_container_width=True,
            key="create_assistant",
            on_click=go_to_edit_assistant_page,
            args=(None,),
        )
        # list user's assistants
        assistants = get_user_assistants(get("user"))
        containers = {}
        columns = {}
        for assistant in assistants:
            containers[assistant.id] = st.container()
            columns[assistant.id] = containers[assistant.id].columns([4, 1, 1, 1])
            with containers[assistant.id]:
                columns[assistant.id][0].button(
                    label=f" __{assistant.name}__ ",
                    help=f"Rediger {assistant.name}.  Sidst opdateret: {assistant.last_updated.strftime('%d-%m-%Y %H:%M')}",
                    key=assistant.id + "rediger",
                    use_container_width=True,
                    on_click=go_to_edit_assistant_page,
                    args=(assistant,),
                )
                columns[assistant.id][1].button(
                    label=":left_speech_bubble:",
                    help=f"Chat med {assistant.name}",
                    key=assistant.id + "chat",
                    use_container_width=True,
                    on_click=go_to_chat_assistant_page,
                    args=(assistant,),
                )
                columns[assistant.id][2].button(
                    # shared assistant link
                    label=":link:",
                    help=f"Del {assistant.name}",
                    key=assistant.id + "del",
                    use_container_width=True,
                )
                if get(assistant.id + "del"):
                    show_assistant_share_link(assistant)
                columns[assistant.id][3].button(
                    label=":wastebasket:",
                    help=f"Slet {assistant.name}",
                    key=assistant.id + "slet",
                    use_container_width=True,
                    # on_click=confirm_and_delete_assistant,
                    # args=(assistant,),
                )
                if get(assistant.id + "slet"):
                    confirm_and_delete_assistant(assistant)
