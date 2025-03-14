import gradio as gr
import pandas as pd
import os
import json
from minecraft_assistant.dialogue_space.message_datastore import MessageDataStore
from minecraft_assistant.agents.deepseek import NLPModel, is_craft_query, display_crafting_table
from minecraft_assistant.agents.agent_utils import CraftResponse, GeneralResponse


# Simulate a database for storing chat history (using MessageDataStore)
class ChatDatabase:
    def __init__(self, filename="./logs/chat_history.json"):
        self.filename = filename
        self.chat_history = MessageDataStore()

    def add_message(self, message, response):
        self.chat_history.add_message(f"User: {message}")
        self.chat_history.add_message(f"Bot: {response}")
        self.save_chat_history()

    def get_chat_history(self):
        return self.chat_history.message_store

    def save_chat_history(self):
        # Save chat history to a JSON file
        with open(self.filename, "w") as f:
            json.dump(self.chat_history.message_store, f, indent=4)

    def load_chat_history(self):
        # Load chat history from a JSON file (if it exists)
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                messages = json.load(f)
                for message in messages:
                    self.chat_history.add_message(message)
        else:
            return []

    def display_chat_history(self):
        # Load chat history from a JSON file (if it exists)
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                messages = json.load(f)
                for message in messages:
                    print(message)
        else:
            return ModuleNotFoundError("Could not find the file")


# Initialize the in-memory database
chat_db = ChatDatabase()

# Loading the Recipe Dataset
recipes_dataset: pd.DataFrame = pd.read_csv('./assets/formatted_recipes.csv', header=None)
recipes_dataset.iloc[:, 0] = recipes_dataset.iloc[:, 0].str.lower()
recipes_items = set(recipes_dataset.iloc[:, 0].values)

# Initialise the AI Agent
model = 'deepseek-chat'
api_key = "sk-ee966d563dba4b84bff8b270c0cd267a"
url = 'https://api.deepseek.com'
chatbot = NLPModel(model, api_key, url)

# open source model (first ollama run model)
# chatbot = NLPModel('llama3.2:latest', 'http://localhost:11434')

# Adding the system prompts
system_prompt = pd.read_csv('./assets/init_prompt.csv')
for i in system_prompt.index:
    chatbot.init_prompt(system_prompt.iloc[i]['message'])

while True:
    user_input = input("You: ")
    if user_input.lower() in ["退出", "bye", "exit"]:
        print("AI: Bye！👋")
        break

    # Checking for a Crafting Query
    craft_item = is_craft_query(user_input)
    print(craft_item)
    if craft_item and (craft_item in recipes_items):
        recipe = recipes_dataset[recipes_dataset.iloc[:, 0] == craft_item].values[0]

        message = (
            f"{",".join(recipe[1:10])}. 3 by 3 2D array crafting table based on the above nine elements"
            f"from left to right and from top to bottom in sequence, 0 means empty output item is {craft_item}"
        )
    else:
        message = user_input
    result = chatbot.chat(user_input)

    print("AI:", end=" ", flush=True)
    if isinstance(result, CraftResponse):
        print(result.formula)
        display_crafting_table([i for row in result.recipe for i in row])
        # display_crafting_table(recipe[1:10])
        print(result.procedure)
    elif isinstance(result, GeneralResponse):
        print(result.response)

    # Taking logs of the message.
    chat_db.add_message(user_input, result)

else:
    chat_db.display_chat_history()


# # Create a Gradio chat interface
# def gradio_chatbot(message, chat_history):
#     response = chatbot_response(message, chat_history)
#     # Append new message and response to history (simulated as in the database)
#     return "", chat_db.get_chat_history()  # Get chat history from the "database"

# # Generate script to replay the chat history
# def generate_script():
#     chat_history = chat_db.get_chat_history()
#     script_lines = [
#         "import gradio as gr",
#         "import random",
#         "def chatbot_response(message):",
#         "    # Your response logic goes here...",
#         "    return \"This is a placeholder response.\"\n"
#     ]

#     # Add each chat message to the script
#     for message in chat_history:
#         script_lines.append(f'# {message}')

#     script_content = "\n".join(script_lines)
#     script_filename = os.path.join(os.getcwd(), "replay_chat_history.py")
#     with open(script_filename, "w") as script_file:
#         script_file.write(script_content)
    
#     print(f"Script generated and saved as {script_filename}")

# # Launch the chatbot with a Gradio interface
# with gr.Blocks() as demo:
#     gr.Markdown("### Minecraft Crafting Assistant 🏗️\nAsk about Minecraft crafting recipes!")
#     chat_history = gr.State()  # state for keeping track of chat
#     chatbot = gr.Chatbot()  # Instantiate Chatbot directly
#     textbox = gr.Textbox(placeholder="Ask me about a crafting recipe...", lines=1)
    
#     textbox.submit(gradio_chatbot, [textbox, chat_history], [chat_history, chatbot])
#     generate_script_button = gr.Button("Generate Script")
#     generate_script_button.click(generate_script)

# demo.launch()
