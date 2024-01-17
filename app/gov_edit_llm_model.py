""" This module contains the streamlit page for editing a LLM model. """ ""
import streamlit as st
from src.streamlit_utils import get, set_to
from src.openai_utils import LLM, llm_api_test
from src.sqlite.gov_db_utils import deploy_llm


def reset_and_go_to_home():
    set_to("model", {})
    set_to("page", "admin_home")


def edit_llm_model_page():
    model = get("model", {})
    help_text = {
        "deployment": {
            "azure": 'Navnet på modellen i din azure deployment. F.eks. "gpt-35-turbo" eller "gpt-4".',
            "openai": 'Navn på openai model. F.eks. "gpt-3.5-turbo"',
            "lm studio": 'Navnet på modellen i din LM Studio localhost model. F.eks. "local-model".',
        },
        "base_url": {
            "azure": 'URL til din azure api endpoint. F.eks. "https://<endpoint>.openai.azure.com/"',
            "openai": 'URL til din openai api endpoint. F.eks. "https://api.openai.com/"',
            "lm studio": 'URL til din LM Studio localhost model. F.eks. "http://localhost:1234/v1"',
        },
    }
    labels = {
        "deployment": {
            "azure": "Deployment",
            "openai": "Model",
            "lm studio": "Model Navn",
        },
        "base_url": {
            "azure": "Azure Endpoint",
            "openai": "OpenAI Endpoint",
            "lm studio": "LM Studio Endpoint",
        },
    }
    placeholders = {
        "deployment": {
            "azure": "f.eks. gpt-35-turbo",
            "openai": "f.eks. gpt-3.5-turbo",
            "lm studio": "f.eks. local-model",
        },
        "base_url": {
            "azure": "https://<endpoint>.openai.azure.com/",
            "openai": "https://api.openai.com/",
            "lm studio": "http://localhost:1234/v1",
        },
    }

    with st.container():
        with st.container():
            st.button(
                "← Tilbage til forsiden",
                help="Gå tilbage til forsiden",
                key="back",
                on_click=reset_and_go_to_home,
                use_container_width=True,
            )

        with st.container(border=True):
            model["name"] = st.text_input(
                "Vist Navn*",
                help="Navnet på modellen som vil blive vist i brugergrænsefladen. F.eks. 'GPT 3.5 Turbo'",
                placeholder="Eksempler: GPT 3.5 Turbo , GPT 4.0, LLAMA 2, MIXTRAL 8, etc.",
                value=model.get("name", ""),
            )
            model["description"] = st.text_input(
                "Kort beskrivelse",
                help="En kort beskrivelse af modellen der vil blive vist i brugergrænsefladen. "
                "Dette hjælper brugere med at vælge den rigtige model.",
                placeholder="Eksempler: 'Hurtig model, god til fleste formål.' , 'Langsommere model, mere kreativ og præcis'. ",
                value=model.get("description", ""),
            )
        with st.container(border=True):
            api_options = ["azure", "openai", "lm studio"]
            model["api_type"] = st.selectbox(
                "API Type*",
                api_options,
                help="Hvilken type API skal modellen tilgås igennem?",
                index=api_options.index(model.get("api_type", "azure")),
            )

            if model["api_type"] != "openai":
                model["enpoint_or_base_url"] = st.text_input(
                    "Endpoint*",
                    help="URL til din API endpoint.",
                    placeholder=placeholders["base_url"][model["api_type"]],
                    value=model.get("enpoint_or_base_url", ""),
                )
            if model["api_type"] != "lm studio":
                model["api_key"] = st.text_input(
                    "API Key*",
                    help="API nøglen til din Azure API endpoint",
                    type="password",
                    value=model.get("api_key", ""),
                )
            model["deployment"] = st.text_input(
                labels["deployment"][model["api_type"]] + "*",
                help=help_text["deployment"][model["api_type"]],
                placeholder=placeholders["deployment"][model["api_type"]],
                value=model.get("deployment", ""),
            )
        submit = st.button("Test og tilføj")

        if submit:
            # test llm
            with st.spinner("Tester modellen..."):
                llm = LLM(**model)
                test_result, message = llm_api_test(llm)
            if test_result:
                # add to db
                st.success(message)
                deploy_llm(llm)
                set_to("model", {})
                set_to("page", "admin_home")
            else:
                st.error(message)
                # add to db
