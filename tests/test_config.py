assistant_name = "Jazzmin"
chat_model_name = "gpt-35-turbo"
sources = [
    "https://jazzobserver.com/the-origins-of-jazz/",
    "https://americanhistory.si.edu/explore/projects/smithsonian-jazz/education/what-jazz",
    "data/test_documents/the_origins_of_jazz.txt",
    "data/test_documents/jazz.csv",
    "data/test_documents/influence of jazz on blues.pdf",
]

system_prompt = (
    f"Dit navn er {assistant_name}."
    " Du er en assistant til opgaver med spørgsmål og svar."
    " Brug de følgende stykker af indhentet kontekst til at besvare spørgsmålet."
    " Hvis du ikke kender svaret, så sig bare, at du ikke ved det."
    " Brug maksimalt tre sætninger og hold svaret kortfattet."
)
