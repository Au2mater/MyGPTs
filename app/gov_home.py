# GPTsGov.py
""" 
A governance module for MyGPTs.
This will help you:
    - add and remove models to your MyGPTs instance.
    - monitor and limit user activity.
    - backup and restore your MyGPTs instance.
"""
import streamlit as st
from random import randint
from src.streamlit_utils import init, get, set_to
from src.sqlite.gov_db_utils import (
    get_deployed_llms,
    activate_llm,
    deactivate_llm,
    delete_llm,
    get_global_setting_dicts,
    set_global_setting,
    reset_all_global_settings,
)

from src.sqlite.db_creation import (
    backup,
    get_backups,
)

# ------------------------
# UTILITY FUNCTIONS


# navigation
def go_to_editing_model(model):
    set_to("model", model)
    set_to("page", "editing_model")


def reset_and_go_to_home():
    set_to("model", {})
    set_to("page", "admin_home")


def go_to_my_assistants():
    set_to("page", "my assistants")


# llms
def confirm_and_delete_llm(llm):
    st.warning(
        f"Er du sikker på, at du vil slette {llm.name}? Denne handling kan ikke fortrydes."
    )
    with st.container():
        c1, c2, _ = st.columns([1, 1, 1])
        c1.button(
            "Ja, slet modellen",
            key="confirm_delete",
            on_click=delete_llm,
            args=(llm,),
            use_container_width=True,
        )
        c2.button(
            "Nej, behold modellen",
            key="cancel_delete",
            on_click=reset_and_go_to_home,
            use_container_width=True,
        )


# global settings
def reset_displayed_settings():
    global_settings = get_global_setting_dicts()
    set_to(
        "global_setting_keys",
        {key: f"{key}_{randint(100000, 999999)}" for key in global_settings.keys()},
    )
    set_to("settings_deafult", True)
    set_to("settings_unchanged", True)


def reset_global_settings():
    reset_all_global_settings()
    reset_displayed_settings()


def set_global_settings():
    keys = get("global_setting_keys")
    for setting in get_global_setting_dicts().values():
        setting["value"] = get(keys[setting["id"]])
        set_global_setting(setting)


# ------------------------


def gov_home_page():
    # ------------------------
    # INITIALIZATION SCRIPT
    if get("initialized", False) is False:
        init("page", "admin_home")
        global_settings = get_global_setting_dicts()
        init(
            "global_setting_keys",
            {key: f"{key}_{randint(100000, 999999)}" for key in global_settings.keys()},
        )
        init("initialized", True)
    # ------------------------
    # UI
    st.title("MyGPTs: Setup & Governance")
    if get("page", "") == "admin_home":
        st.button(
            "Gå til Mine Assistenter →",
            on_click=go_to_my_assistants,
            use_container_width=True,
        )
        st.markdown(
            "<small>Denne side er kun synlig for localhost. </small>",
            unsafe_allow_html=True,
        )
        t1, t2, t3, t4 = st.tabs(
            [
                "__Modeller__",
                "__Indstillinger__",
                "__Statistik__",
                "__Backup & Restore__",
            ]
        )
        with t1:
            # with st.expander("__Modeller__", expanded=True):
            # create a form for adding a new model
            deployed_llms = get_deployed_llms()

            st.button(
                "Tilføj ny model",
                help="Tilføj en ny model til MyGPTs",
                on_click=set_to,
                args=["page", "editing_model"],
                use_container_width=True,
            )
            if len(deployed_llms) == 0:
                st.warning(
                    "Ingen modeller er tilføjet endnu. Tilføj mindst én model for at komme i gang."
                )

            # list models
            containers = {}
            columns = {}
            for model in deployed_llms:
                containers[model.id] = st.container()
                columns[model.id] = containers[model.id].columns([4, 1, 1])
                with containers[model.id]:
                    columns[model.id][0].button(
                        label=f"__{model.name}__ ",
                        help=f"Redigér {model.name}",
                        key=model.id + "edit",
                        use_container_width=True,
                        on_click=go_to_editing_model,
                        args=[model.model_dump()],
                    )
                    columns[model.id][1].button(
                        label=":wastebasket:",
                        help=f"Slet {model.name}",
                        key=model.id + "slet",
                        use_container_width=True,
                    )
                    if get(model.id + "slet"):
                        confirm_and_delete_llm(model)

                    columns[model.id][2].button(
                        label=":green[AKTIV]" if model.is_active else ":gray[INAKTIV]",
                        # label_visibility = 'hidden',
                        help=f"Slå {model.name} fra"
                        if model.is_active
                        else f"Slå {model.name} til",
                        key=model.id + "toggle",
                        on_click=deactivate_llm if model.is_active else activate_llm,
                        args=[model.id],
                        use_container_width=True,
                    )

        with t2:
            # with st.expander("__Standardindstillinger for oprettelse af assistenter__", expanded=True):
            global_settings = get_global_setting_dicts()

            # The maximum number of tokens that can be generated in the chat completion.
            # The total length of input tokens and generated tokens is limited by the model's context length.
            st.text_input(
                "Base URL",
                value=global_settings["base_url"]["value"],
                help="Denne URL bruges til at tilgå løsningen og dele assistenter i organisationen.",
                key=get("global_setting_keys")["base_url"],
            )
            st.slider(
                "Standard max tokens",
                min_value=1,
                max_value=5000,
                value=global_settings["max_tokens"]["value"],
                step=10,
                help=(
                    "Den maksimale længde af outputtet i tokens."
                    "Den samlede længde af input tokens og genererede tokens er begrænset af modellens kontekstlængde."
                    f"Standardværdi: {global_settings['max_tokens']['default_value']}"
                ),
                key=get("global_setting_keys")["max_tokens"],
            )
            st.text_input(
                "Sentece Embeddings model",
                value=global_settings["embeddings_model"]["value"],
                help="Navnet på den Sentence Embeddings model, der skal bruges til at indeksere kilder.",
                key=get("global_setting_keys")["embeddings_model"],
            )
            st.markdown(
                "<br> Nedenstående indstillinger kan ændres af brugeren for hver enkelt assistent.",
                unsafe_allow_html=True,
            )

            st.text_area(
                "Standard system prompt",
                value=global_settings["default_system_prompt"]["value"],
                key=get("global_setting_keys")["default_system_prompt"],
            )
            st.text_input(
                "Standard velkomstbesked",
                value=global_settings["default_welcome_message"]["value"],
                key=get("global_setting_keys")["default_welcome_message"],
            )

            with st.container():
                init("settings_deafult", True)
                init("settings_unchanged", True)
                for setting in global_settings.values():
                    if setting["value"] != setting["default_value"]:
                        set_to("settings_deafult", False)
                    if (setting["value"]) != (
                        get(get("global_setting_keys")[setting["id"]])
                    ):
                        set_to("settings_unchanged", False)

                col1, col2, col3 = st.columns([1, 1, 1])
                col1.button(
                    "Nulstil",
                    help="Nulstil standardindstillingerne",
                    disabled=get("settings_deafult"),
                    use_container_width=True,
                    on_click=reset_global_settings,
                )
                if col2.button(
                    "Gem ændringer",
                    help="Gem ændringer for standardindstillingerne",
                    disabled=get("settings_unchanged"),
                    use_container_width=True,
                    on_click=set_global_settings,
                ):
                    st.success("Standardindstillinger gemt")
                col3.button(
                    "Annuller ændringer",
                    help="Annuller ændringer for standardindstillingerne",
                    disabled=get("settings_unchanged"),
                    use_container_width=True,
                    on_click=reset_displayed_settings,
                )
    # ------------------------

    with t3:
        st.write("Kommer snart...")
        # stats = [dict(r) for r in  get_user_stats()] # stats is a list of sqlite3.Row objects
        # display stats in a table
        # st.table(stats)

    # ------------------------
    with t4:
        # backup and restore
        if st.button(
            "Opret Sikkerhedskopi",
            help="Skab en backup af MyGPTs databasen",
            use_container_width=True,
        ):
            with st.spinner("Vent venligst..."):
                time = backup()
                if time:
                    st.success(f"Sikkerhedskopi oprettet: {time}")

        # list backups
        backups = get_backups()
        for bkp in backups:
            st.markdown(f"Sikkerhedskopi oprettet: :green[{bkp}]")
