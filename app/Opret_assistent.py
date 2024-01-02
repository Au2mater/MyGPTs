# test_streamlit_fileupload.py
# streamlit run tests/test_streamlit_fileupload.py
""" create custom assistant """
import os
import sys
from pathlib import Path
import streamlit as st
from streamlit_tags import st_tags
from random import randint

# add root directory to path for relative import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config_assistant import load_assistant_config, save_assistant_config
from src.chroma.chroma_utils import zipupdate_directory_with_sources
from src.path_urls.path_url_utilities import create_assistant_dir, unpack
from src.openai.openai_utils import  get_LLM_descriptions

# # write type of each session state variable
# st.write({k: (type(v) ,v) for k, v in st.session_state.items()})


# Page header
st.set_page_config(
    page_title="Min GPT:Create",
    page_icon=":left_speech_bubble:",
    initial_sidebar_state="expanded",
)


st.title("Min GPT")
st.markdown(
    "<small>Opret din egen chat assistent ved at selv at definere samtalens grundvilkår og evt. videnskilder. \n"
    "Du kan også indlæse en eksisterende konfiguration.\n"
    "Når du er færdig, klik på 'Gem Min assistant' og download konfigurationen.</small>",
    unsafe_allow_html=True,
)

# Form: Upload existing assistant configuration
with st.container(border=False):
    # eksisterende konfiguration
    with st.expander(label="Indlæs eksisterende konfiguration", expanded=False):
        st.markdown(
            body="<small>Hvis du tidligere har oprettet og downloadet en konfiguration,\
                     kan du indlæse den her.</small>",
            unsafe_allow_html=True,
        )

        uploaded_config = st.file_uploader(
            "pre-configuration",
            type=["zip"],
            accept_multiple_files=False,
            label_visibility="hidden",
            key=st.session_state.get("upg_key"),
        )
        if uploaded_config:
            with st.spinner("Indlæser..."):
                pre_dir = unpack(uploaded_config)
                pre_config = load_assistant_config(pre_dir)
            st.session_state.assistant_name = pre_config["assistant_name"]
            st.session_state.system_prompt = pre_config["system_prompt"]
            st.session_state.pre_sources = pre_config["sources"]
            st.session_state.sources = pre_config["sources"]
            st.session_state.pre_dir = Path(pre_dir)
            st.session_state.upg_key = str(randint(1, 1000000))

# Form: Configure Assistant
with st.container(border=True):
    c1, c2 = st.columns([1, 1])

    # assistant name input
    c1.text_input(
        label="Assitentens navn*",
        value=f"",
        help="Giv assistanten et passende navn.",
        key="assistant_name",
        kwargs={"height": 50, "margin": 0},
    )
    # chat model input
    c2.selectbox(
        label="Chat model",
        options=get_LLM_descriptions().keys(),
        help=(
            "\n".join(f"- __{name}__: {description}" 
                      for name, description in get_LLM_descriptions().items())               
        ),
        key="chat_model_name",
        index=0,
    )
    # system prompt input
    st.text_area(
        label="Assitentens grundvilkår*",
        value=(
            "Du er en  hjælpsom assistent der hjælper med spørgsmål og svar. \n"
            "Brug de følgende stykker af indhentet kontekst til at besvare spørgsmålet. \n"
            "Hvis du ikke kender svaret, så sig bare, at du ikke ved det. \n"
            "Brug maksimalt tre sætninger og hold svaret kortfattet."
        ),
        help="Hvem skal assistanten hjælpe, hvordan skal den svare og hvad skal den være særligt opmærksom på?",
        key="system_prompt",
        height=150,
    )

    # sources input
    with st.expander(label="Evt. Videnskilder", expanded=True):
        # write markdown in a small itlaic font
        st.markdown(
            "<small>_Tilføj evt. hjemmesider og filer, \
                    som assistanten skal bruge til at formulere svaret._</small>",
            unsafe_allow_html=True,
            help="Dette er ikke påkrævet.",
        )

        # files
        uploaded_files = st.file_uploader(
            "Filer",
            type=["csv", "docx", "md", "pdf", "txt"],
            accept_multiple_files=True,
            key="files",
        )
        if uploaded_files:
            st.session_state.sources = list(
                set(
                    [file.name for file in st.session_state.files]
                    + st.session_state.get("sources", [])
                )
            )

        # all sources
        sources = st_tags(
            label="Kilder",
            text="Tilføj links her",
            value=st.session_state.get("sources", []),
            suggestions=["https://www.", "www."],
            maxtags=10,
        )

    submit_button = st.button(label="Gem min assistent", key="save_assistant")


# # if the form is submitted, save the configuration to a yaml file
if submit_button:
    # test if mandatory fields are filled out
    if not st.session_state.assistant_name:
        st.error("Du skal give assistanten et navn.")
        st.stop()
    if not st.session_state.system_prompt:
        st.error("Du skal give assistanten et grundvilkår.")
        st.stop()

    # create a temporary directory for the assistant under data/assistants
    # folder is named after the assistant and the current date and time
    # if a previous configuration was used as a template, use the same directory
    if st.session_state.get("pre_dir"):
        assistant_dir = st.session_state.pre_dir
    else:
        assistant_dir = create_assistant_dir(st.session_state.assistant_name)

    st.session_state.sources = list(set(sources))
    # save the configuration above to a config.yaml in the assistant directory
    config = save_assistant_config(
        assistant_name=st.session_state.assistant_name,
        chat_model_name=st.session_state.chat_model_name,
        system_prompt=st.session_state.system_prompt,
        sources=st.session_state.sources,
        assistant_dir=assistant_dir,
    )

    # save new uploaded files to the files directory
    filesdir = assistant_dir / "files"
    filesdir.mkdir(exist_ok=True)
    for file in st.session_state.files:
        filepath = os.path.join(filesdir, file.name)
        with open(filepath, "wb") as f:
            f.write(file.getvalue())

    # zip and delete the assistant directory
    with st.spinner("Opdaterer vidensbase..."):
        report = zipupdate_directory_with_sources(
            directory=str(assistant_dir),
            sources=st.session_state.sources,
            delete_directory=True,
        )
        st.session_state.zip_path = report["zip_path"]
        if len(report["remove_sources"]) > 0:
            st.warning(
                f"Fjernede følgende kilder fra vidensbasen: {report['remove_sources']}"
            )
        if len(report["add_sources"]) > 0:
            st.success(
                f"Tilføjede følgende kilder til vidensbasen: {report['add_sources']}"
            )

        download = st.download_button(
            label="Download assistant konfiguration",
            data=open(st.session_state.zip_path, "rb").read(),
            file_name=str(Path(st.session_state.zip_path).name),
            mime="text/yaml",
            key="download",
            help=None,
        )


if st.session_state.get("download"):
    os.remove(st.session_state.zip_path)
    st.success("Assistanten er gemt og klar til brug.")
