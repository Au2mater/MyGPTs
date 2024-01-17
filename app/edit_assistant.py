import streamlit as st
from streamlit_tags import st_tags
from random import randint
import re
from src.sqlite.db_utils import (
    get_user_assistants,
    add_or_update_assistant,
    get_assistant_sources,
    delete_assistant,
    add_source,
    delete_source,
    get_active_llms,
    get_base_url,
)
from src.streamlit_utils import get, set_to, append
from src.chroma_utils import create_source
from src.basic_data_classes import Assistant
from src.sqlite.gov_db_utils import get_global_setting


# UTILITY FUNCTIONS
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


def add_urls(displayed_sources):
    for source in displayed_sources:
        # if the string does not end in  (dd/dd dd:dd):
        if re.search(r"\(\d{2}/\d{2}\s\d{2}:\d{2}\)$", source) is None:
            with st.spinner("Indlæser tekst fra link..."):
                try:
                    new_source = create_source(source, get("current_assistant").id)
                    # remove from displayed sources
                    append("session_sources", new_source)
                    append("sources_to_add", new_source)
                except Exception:
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


# UI


def edit_assistant_page():
    active_llms = get_active_llms()
    llm_ids = [llm.id for llm in active_llms]
    # cancel button
    st.button(
        label="← Mine Assistenter",
        key="cancel",
        on_click=go_back,
        use_container_width=True,
    )
    if len(active_llms) == 0:
        st.error(
            "Der er ingen chat modeller tilgængelige. Kontakt en administrator for at få hjælp."
        )
        st.stop()
    # Form 2: Configure Assistant
    # t1, t2 = st.tabs(["Konfigurer assistent", "Tilføj videnskilder"])
    # with t1:
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
            options=llm_ids,
            format_func=lambda llm_id: [
                llm.name for llm in active_llms if llm.id == llm_id
            ][0],
            help=(
                "\n".join(f"- __{llm.name}__: {llm.description}" for llm in active_llms)
            ),
            key="chat_model_name",
            # get the index of the current model
            index=(
                llm_ids.index(current_assistant.chat_model_name)
                if current_assistant.chat_model_name in llm_ids
                else 0
            ),
        )
        # system prompt input
        st.text_area(
            label="Assitentens grundvilkår*",
            value=current_assistant.system_prompt,
            help="Hvem skal assistanten hjælpe, hvordan skal den svare og hvad skal den være særligt opmærksom på?",
            key="system_prompt",
            height=150,
        )
        options_dict = {
            "Faktuel, logisk": 0.2,
            "Afbalanceret, relevant": 0.7,
            "Kreativ, mangfoldig": 1.1,
        }
        t = [k for k, v in options_dict.items() if v == current_assistant.temperature]
        st.select_slider(
            label="Kreativitet*",
            options=options_dict.keys(),
            value=t[0] if len(t) > 0 else "Afbalanceret, relevant",
            help=(
                "- __Faktuel, logisk__: god til f.eks. resuméer, korrektur og faktuelle svar. \n"
                "- __Afbalanceret, relevant__: god til f.eks. diskussioner, formidling af komplekse emner og præsentation af velovervejede argumenter.\n"
                "- __Kreativ, mangfoldig__: god til f.eks. historiefortælling, sangskrivning, spil og jokes."
            ),
            key="temperature",
        )

        # welcome message input
        st.text_input(
            label="Assitentens velkomstbesked*",
            value=current_assistant.welcome_message,
            help="Hvad skal assistanten sige til brugeren, når samtalen starter?",
            key="welcome_message",
        )

    # sources input
    with st.expander(label="Evt. Videnskilder", expanded=True):
        # with t2:
        st.markdown(
            "<small>_Tilføj evt. hjemmesider og filer,"
            "som assistanten skal bruge til at formulere svaret._</small>",
            unsafe_allow_html=True,
            help="Dette er ikke påkrævet.",
        )

        if st.file_uploader(
            label="Filer",
            type=["csv", "doc", "docx", "pdf", "txt", "md"],
            accept_multiple_files=True,
            key=get("temp_file_key", "2"),
        ):
            with st.spinner("Indlæser tekst fra uploadet fil ..."):
                read_text_from_files(current_assistant.id)

        # all sources
        displayed_sources = st_tags(
            label="Kilder",
            text="Tilføj links her",
            value=[display_source(s) for s in get("session_sources", [])],
            suggestions=["https://www.", "http://", "https://"],
            maxtags=10,
        )
        add_urls(displayed_sources)

    current_assistant.name = get("assistant_name", "")
    current_assistant.chat_model_name = get("chat_model_name")
    current_assistant.system_prompt = get("system_prompt", "")
    current_assistant.welcome_message = get("welcome_message", "")
    current_assistant.temperature = options_dict[get("temperature")]

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
    if st.button(
        label="Gem",
        key="save_assistant",
        # on_click=save_assistant,
        # args=(get("current_assistant"),),
        use_container_width=True,
    ):
        save_assistant(get("current_assistant"))
        st.success("Assistenten er gemt.")
        col1, col2 = st.columns([1, 1])
        col1.button(
            label=" :left_speech_bubble: Chat med assistenten",
            on_click=go_to_chat_assistant_page,
            args=(get("current_assistant"),),
            use_container_width=True,
        )
        col2.button(
            label=" ← Mine assistenter",
            on_click=go_back,
            use_container_width=True,
        )
    # deebbuging
    # set_to("num",get("num",0)+1)
    # st.write(get("num"))
