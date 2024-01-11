status = "prod" # "dev" or "prod"
import streamlit as st
from random import randint
from streamlit_tags import st_tags
from uuid import uuid4
import re
import os
import sys
if (
    path := os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
) not in sys.path:
    sys.path.append(path)
# add root directory to path for relative import
from src.sqlite.db_utils import (
    Assistant,
    add_or_get_user,
    get_user_assistants,
    get_assistant,
    add_or_update_assistant,
    get_assistant_sources,
    delete_assistant,
    add_source,
    delete_source,
)
from src.streamlit_utils import get_remote_ip, init, get, set_to, append
from src.openai.openai_utils import get_LLM_descriptions, generate_response
from src.chroma.chroma_utils import start_chroma_server, create_source, add_context

# ------------------------
# functions


def go_to_edit_assistant_page(assistant: Assistant = None):
    set_to("page", "create assistant")
    if assistant is None:
        assistant = Assistant(
            name=(
                "Din Assistent "
                + str(int(len(get_user_assistants(get("username")))) + 1)
            ),
            owner_id=get("username"),
            id=uuid4().hex,
        )
    set_to("current_assistant", assistant)
    set_to("indexed_sources", get_assistant_sources(assistant.id))
    set_to("session_sources", get_assistant_sources(assistant.id))
    set_to("sources_to_add", [])
    set_to("sources_to_delete", [])


def show_assistant_share_link(assistant):
    link = f"http://win10-ahmaba.intern.gladsaxe.dk:8501/myGPT/?shared_assistant_id={assistant.id}"
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


# edit assistant functions
def read_text_from_files(assistant_id: str):
    """add uploaded files to sources_to_add and reset file uploader"""
    uploaded_files = get(get("temp_file_key", "2"))
    for file in uploaded_files:
        # st.session_state.sources_to_add.append(Source(file))
        source = create_source(file, assistant_id)
        append("sources_to_add", source)
        append("session_sources", source)

    # reset uploader
    st.session_state.temp_file_key = str(randint(1, 1000000))

def display_source(s):
    return f"{s.name} ({s.creation_time.strftime('%d/%m %H:%M')})"

def add_urls():
    for source in displayed_sources:
        # if the string does not end in  (dd/dd dd:dd):
        if re.search(r"\(\d{2}/\d{2}\s\d{2}:\d{2}\)$", source) is None:
            with st.spinner("Indlæser tekst fra link..."):
                try:
                    new_source = create_source(source, get("current_assistant").id)
                    # remove from displayed sources
                    append("session_sources", new_source)
                    append("sources_to_add", new_source)
                except:
                    st.error(f"Kunne ikke indlæse {source}")


def validate_config(assistant):
    # test if mandatory fields are filled out
    if len(assistant.name) < 1:
        st.toast(
            "🚨 :red[Du skal give assistantens et navn.]",
        )
        return False
    if len(assistant.system_prompt) < 10:
        st.toast("🚨 :red[Du skal angive assistantens grundvilkår udførligt.]")
        return False
    if len(assistant.welcome_message) < 1:
        st.toast("🚨 :red[Du skal angive en velkomstbesked.]")
        return False
    return True


def go_back():
    """discard changes and go back to my assistants page"""
    set_to("session_sources", [])
    set_to("sources_to_add", [])
    set_to("page", "my assistants")


def save_assistant(assistant):
    if validate_config(assistant):
        with st.spinner("Gemmer assistent..."):
            add_or_update_assistant(assistant=assistant)
            for source in get("sources_to_add"):
                add_source(source)
            for source in get("sources_to_delete"):
                delete_source(source)
        go_to_edit_assistant_page(assistant)


# chat functions


# ------------------------
# Page header
st.set_page_config(
    page_title="Min GPT",
    page_icon=":left_speech_bubble:",
    initial_sidebar_state="expanded",
)

# initialize session
if get("username") is None:
    # start chroma server  for indexing assistant knwoledge base documents
    start_chroma_server()
    # user is initialized by ip address
    print("initializing user")
    init("username", add_or_get_user(get_remote_ip()))
    # set start page to my assistants
    init("page", "my assistants")
    if status == "prod" or get("username") == "::1":
        set_to("online", True)

# ------------------------
# ui
if not get("online",False):
    st.markdown(
        """
        <div style="text-align:center">
        <h1>Vi er i gang med at opdatere Min GPT</h1>
        <h2>Vi er tilbage snarest</h2>
        <img src="https://media.giphy.com/media/yJwXlLESRVkFd6yQVr/giphy.gif" alt="GPT-3" width="300" height="300">
        
        </div>
        """,
        unsafe_allow_html=True,
    )        
if get("online",False):
    # chat with shared assistant
    if "shared_assistant_id" in (params := st.experimental_get_query_params()):
        shared_assistant_id = params["shared_assistant_id"][0]
        assistant = get_assistant(shared_assistant_id)
        set_to("shared_assistant_view", True)
        go_to_chat_assistant_page(assistant)


    # page 1: my assistants
    if get("page") == "my assistants":
        st.title("Mine Assistenter")
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
            assistants = get_user_assistants(get("username"))
            containers = {}
            columns = {}
            for assistant in assistants:
                containers[assistant.id] = st.container()
                columns[assistant.id] = containers[assistant.id].columns([4, 1, 1, 1])
                with containers[assistant.id]:
                    columns[assistant.id][0].button(
                        label=f":left_speech_bubble: __{assistant.name}__ ",
                        help=f"Chat med {assistant.name}",
                        key=assistant.id + "chat",
                        use_container_width=True,
                        on_click=go_to_chat_assistant_page,
                        args=(assistant,),
                    )
                    columns[assistant.id][1].button(
                        label=":pencil2:",
                        help=(
                            f"Rediger {assistant.name}.  Sidst opdateret: {assistant.last_updated.strftime('%d-%m-%Y %H:%M')}"
                        ),
                        key=assistant.id + "rediger",
                        use_container_width=True,
                        on_click=go_to_edit_assistant_page,
                        args=(assistant,),
                    )
                    columns[assistant.id][2].button(
                        label=":wastebasket:",
                        help=f"Slet {assistant.name}",
                        key=assistant.id + "slet",
                        use_container_width=True,
                        # on_click=confirm_and_delete_assistant,
                        # args=(assistant,),
                    )
                    if get(assistant.id + "slet"):
                        confirm_and_delete_assistant(assistant)
                    columns[assistant.id][3].button(
                        # shared assistant link
                        label=":link:",
                        help=f"Del {assistant.name}",
                        key=assistant.id + "del",
                        use_container_width=True,
                        # on_click=show_assistant_share_link,
                        # args=(assistant,),
                    )
                    if get(assistant.id + "del"):
                        show_assistant_share_link(assistant)

    # page 2: create and edit assistant
    if get("page") == "create assistant":
        # cancel button
        st.button(
            label="← Mine Assistenter",
            key="cancel",
            on_click=go_back,
            use_container_width=True,
        )
        # Form 2: Configure Assistant
        with st.container(border=True):
            current_assistant = get("current_assistant")
            c1, c2 = st.columns([1, 1])
            # assistant name input
            c1.text_input(
                label="Assitentens navn*",
                value=current_assistant.name,
                help="Giv assistanten et passende navn.",
                key="assistant_name",
                kwargs={"height": 50, "margin": 0},
            )
            # chat model input
            c2.selectbox(
                label="Chat model",
                options=get_LLM_descriptions().keys(),
                help=(
                    "\n".join(
                        f"- __{name}__: {description}"
                        for name, description in get_LLM_descriptions().items()
                    )
                ),
                key="chat_model_name",
                # get the index of the current model
                index=list(get_LLM_descriptions().keys()).index(
                    current_assistant.chat_model_name
                )
                if current_assistant.chat_model_name in get_LLM_descriptions().keys()
                else 0,
            )
            # system prompt input
            st.text_area(
                label="Assitentens grundvilkår*",
                value=current_assistant.system_prompt,
                help="Hvem skal assistanten hjælpe, hvordan skal den svare og hvad skal den være særligt opmærksom på?",
                key="system_prompt",
                height=150,
            )
            # welcome message input
            st.text_input(
                label="Assitentens velkomstbesked",
                value=current_assistant.welcome_message,
                help="Hvad skal assistanten sige til brugeren, når samtalen starter?",
                key="welcome_message",
            )

            # sources input
            with st.expander(label="Evt. Videnskilder", expanded=True):
                st.markdown(
                    "<small>_Tilføj evt. hjemmesider og filer,"
                    "som assistanten skal bruge til at formulere svaret._</small>",
                    unsafe_allow_html=True,
                    help="Dette er ikke påkrævet.",
                )

                if ( st.file_uploader(
                    label="Filer",
                    type=["csv", "doc", "docx", "pdf", "txt", "md"],
                    accept_multiple_files=True,
                    key=get("temp_file_key", "2"),
                    # on_change=read_text_from_files,
                    # kwargs={"assistant_id": current_assistant.id},
                )):
                    with st.spinner(f"Indlæser tekst fra uplaodet fil ..."):
                        read_text_from_files(current_assistant.id)     


                # all sources
                displayed_sources = st_tags(
                    label="Kilder",
                    text="Tilføj links her",
                    value=[display_source(s) for s in get("session_sources", [])],
                    suggestions=["https://www.", "http://", "https://"],
                    maxtags=10,
                )
                add_urls()

            current_assistant.name = get("assistant_name", "")
            current_assistant.chat_model_name = get("chat_model_name")
            current_assistant.system_prompt = get("system_prompt", "")
            current_assistant.welcome_message = get("welcome_message", "")

            # detect and handle sources removed
            # check if sources have been removed from sources is the list of sources still contains indexed sources
            # if not add the missing indexed sources to the list of sources to delete
            for source in get("indexed_sources"):
                if display_source(source) not in displayed_sources:
                    append("sources_to_delete", source)
                    # remove from session sources
                    set_to(
                        "session_sources",
                        [s for s in get("session_sources") if s != source],
                    )
            # when source is added to displayed sources, add it to sources to add
            # if it's name not in display name of indexed sources and not in sources to add
            # create a new source and add it to sources to add

            # save button
            st.button(
                label="Gem",
                key="save_assistant",
                # on_click=save_assistant,
                # args=(get("current_assistant"),),
                use_container_width=True,
            )
            if get("save_assistant"):
                save_assistant(get("current_assistant"))
                st.success("Assistenten er gemt.")
            # deebbuging
            # set_to("num",get("num",0)+1)
            # st.write(get("num"))


    # page 3: chat with assistant
    if get("page") == "chat":
        assistant = get("current_assistant")

        col1, col2, col3 = st.columns([1, 1, 1])
        with st.container():
            with col1:
                if not get("shared_assistant_view"):
                    st.button(
                        label="← Mine assistenter ",
                        key="my_assistants",
                        on_click=go_back,
                        use_container_width=True,
                    )

            with col3:
                st.button(
                    label=":sparkles: Ny samtale\n",
                    key="ny_samtale",
                    on_click=go_to_chat_assistant_page,
                    args=(assistant,),
                    use_container_width=True,
                )
        st.markdown(
            "__" + assistant.name + "__",
        )

        # # Display chat messages
        icons = {
            "assistant": "images/assistant_icon.png",
            "user": "images/user_icon.png",
        }
        names = {
            "assistant": "ai",
            "user": "human",
        }
        for message in get("messages")[1:]:  # we skip the first system message
            with st.chat_message(
                name=names[message["role"]],
                avatar=icons[message["role"]],
            ):
                st.write(message["content"])

        if prompt := st.chat_input():
            with st.chat_message(
                name=names["user"],
                avatar=icons["user"],
            ):
                st.write(prompt)
            with st.spinner("Søger..."):
                if get("number_of_sources") > 0:
                    request_messages = add_context(
                        prompt=prompt, messages=get("messages"), assistant=assistant
                    )
                else:
                    request_messages = get("messages")
            response = generate_response(
                prompt_input=prompt,
                chat_model=assistant.chat_model_name,
                messages=request_messages,
            )
            append("messages", {"role": "user", "content": prompt})
            append("messages", {"role": "assistant", "content": response})
            with st.chat_message(
                name=names["assistant"],
                avatar=icons["assistant"],
            ):
                st.write(response)
