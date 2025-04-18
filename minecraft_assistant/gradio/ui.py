import gradio as gr
import pandas as pd
import os
import json
import speech_recognition as sr
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
        return "\n".join(self.chat_history.message_store)

    def save_chat_history(self):
        with open(self.filename, "w") as f:
            json.dump(self.chat_history.message_store, f, indent=4)

    def load_chat_history(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                messages = json.load(f)
                for message in messages:
                    self.chat_history.add_message(message)


# Initialize the in-memory database
chat_db = ChatDatabase()
chat_db.load_chat_history()

# Loading the Recipe Dataset
recipes_dataset: pd.DataFrame = pd.read_csv('./assets/formatted_recipes.csv', header=None)
recipes_dataset.iloc[:, 0] = recipes_dataset.iloc[:, 0].str.lower()
recipes_items = set(recipes_dataset.iloc[:, 0].values)

# Initialise the AI Agent
model = 'deepseek-chat'
api_key = "sk-ee966d563dba4b84bff8b270c0cd267a"
url = 'https://api.deepseek.com'
chatbot = NLPModel(model, api_key, url)

# Load system prompts
system_prompt = pd.read_csv('./assets/init_prompt.csv')
for i in system_prompt.index:
    chatbot.init_prompt(system_prompt.iloc[i]['message'])


# Function to convert speech to text
def speech_to_text(audio):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio) as sources:
        audio_data = recognizer.record(sources)
        try:
            text = recognizer.recognize_google(audio_data)
            print(f"Converted text: {text}")  # Debugging
            return text
        except sr.UnknownValueError:
            return "Sorry, I could not understand the audio."
        except sr.RequestError:
            return "Sorry, there was an issue with the speech recognition service."


# Function to process user input and generate a response
def chat_with_ai(user_input, history):
    history = history or []
    
    # Exit condition
    if user_input.lower() in ["退出", "bye", "exit"]:
        response = "AI: Bye！👋"
        history.append((user_input, response))
        return history, history

    # Check if it's a crafting query
    craft_item = is_craft_query(user_input)
    if craft_item and (craft_item in recipes_items):
        recipe = recipes_dataset[recipes_dataset.iloc[:, 0] == craft_item].values[0]
        message = (
            f"{','.join(recipe[1:10])}. 3 by 3 2D array crafting table based on the above nine elements "
            f"from left to right and from top to bottom in sequence, 0 means empty. Output item is {craft_item}"
        )
    else:
        message = user_input

    # Get response from the chatbot
    result = chatbot.chat(message)

    if isinstance(result, CraftResponse):
        response = f"{result.formula}\n{result.procedure}"
    elif isinstance(result, GeneralResponse):
        response = result.response
    else:
        response = "I'm not sure how to respond to that."

    # Add to chat history
    chat_db.add_message(user_input, response)
    history.append((user_input, response))
    return history, history


# Function to handle audio input and automatically send to chatbot
def process_audio(audio):
    if audio is None:
        return "No audio file received."
    
    text = speech_to_text(audio)
    if text and text not in ["Sorry, I could not understand the audio.", "Sorry, there was an issue with the speech recognition service."]:
        # Pass the converted text to the chatbot
        history, _ = chat_with_ai(text, None)
        return history  # Return the updated chat history
    return "Sorry, I could not process the audio."


# Gradio Interface
block = gr.Blocks()

with block:
    gr.Markdown("""<h1><center>Minecraft Assistant Chatbot</center></h1>""")
    chatbot_ui = gr.Chatbot()
    message = gr.Textbox(placeholder="Type your message here...")  # Keep the textbox visible
    state = gr.State()

    # Add microphone button for voice input
    mic = gr.Audio(sources=["microphone"], type="filepath", label="Speak your message")
    mic.change(process_audio, inputs=mic, outputs=chatbot_ui)

    # Process input when pressing Enter (for text input)
    message.submit(chat_with_ai, inputs=[message, state], outputs=[chatbot_ui, state])

block.launch(debug=True)