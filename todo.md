# MyGPTs
🗺️ Roadmap for MyGPTs 

### To-do

- [ ] Add sign-in: ability to sign in as a user,
  - [ ] adding better control over app access and API user budget
- [ ] Add assistant-user memmory: ability to auto index conversations into knowledge base and retrieve later on.
- [ ] Add sample starter templates for assistant configurations
- [ ] Add edit: option to edit a single user message in conversation.  
- [ ] Add functionality to show references for sources being used in the conversation.
- [ ] Add optional web search integration.
- [ ] Add token/price counter for Azure OpenAi API  
- [ ] Add English language to user interface
- [ ] Add profile picture: ability to add profile picture to assistant

### In-progress
- [ ] Add Docker documentation
- [ ] Add ability to suggest prompts to the user in the chat UI
- [ ] Governance: See and delete user, assistants, and sources
- [ ] Governance: Monitor API usage
- [ ] Chat: Add history: ability to and see delete previous conversations 
- [ ] Backend: Simplify and better structure streamlit app code 
- [ ] Backend: Update tests

### Completed ✓
- [x] Upgrade to python 3.11
- [x] Dockerize app
- [x] Privacy: deactivate anonymzied telemetry for chromaDB
- [x] Add governance module
    - [x] Setting up and make LLMs available to assistants
- [x] Add simple temperature parameter control in Assistant Builder
- [x] Add custom introductive assistant message (previously deafulted to: 'Hej jeg <navn>, Hvordan kan jeg hjælpe dig?'). 
- [x] Add reset conversation button to the chat UI
- [x] Resolve knowledge base changes from config file, not chromaDB, for faster updates.
- [x] Validate urls with typing module
- [x] Ensure files and urls can be replaced by new files and urls with same name 
- [x] elminiating the need to download and upload the assistant archive files
- [x] WebURLs saved as txt in files directory. 
- [x] Edit previously created assistants  
- [x] Add support for GPT 4  
- [x] Add support for OpenAi API  
- [x] Add support for a local open-source LLM (Mixtral 8 7B)  