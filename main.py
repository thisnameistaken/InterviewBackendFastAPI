from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import os
import uuid

load_dotenv()
google_API_key = os.getenv("API_KEY")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL"),
        os.getenv("PRODUCTION_URL"),
        os.getenv("TEST_FRONTEND_URL"),
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dictionary to store conversations, No need for a DB in this demo
conversations = {}

class SentMessage(BaseModel):
    text: str
    conversation_id: str

class EditMessage(BaseModel):
    text: str
    conversation_id: str
    message_id: int

class DeleteMessage(BaseModel):
    conversation_id: str
    message_id: int

def generate_bot_response(user_message: str) -> str:
    try:
        genai.configure(api_key=google_API_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            user_message,
            generation_config = genai.GenerationConfig(
                max_output_tokens=1000,
                temperature=0.1,
            )
        )
        return response.text
    except Exception as e:
        return str(e)

@app.post("/start_conversation")
async def start_conversation():
    conversation_id = str(uuid.uuid1()) 

    conversations[conversation_id] = []  # Initialize an empty conversation
    return {"status": "conversation started", "conversation_id": conversation_id}

@app.post("/send_message")
async def send_message(message: SentMessage):
    conversation_id = message.conversation_id

    # handle invalid conversation ids
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # create reply id
    id = len(conversations[conversation_id])

    # Save the user message
    user_message = {"id": id, "sender": "user", "text": message.text}
    conversations[conversation_id].append(user_message)
    
    # Generate bot response
    bot_response = generate_bot_response(message.text)

    bot_message = {"id": id + 1, "sender": "bot", "text": bot_response}
    conversations[conversation_id].append(bot_message)
    
    return {"status": "message sent", "response": conversations[conversation_id]}

@app.post("/update_message")
def update_message(update_message: EditMessage):
    conversation_id = update_message.conversation_id

    # handle invalid conversation ids
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = conversations[conversation_id]
    
    if update_message.message_id > len(conversation):
        raise HTTPException(status_code=404, detail="Invalid message id")
    
    # Reset the conversation to before this message, delete all messages after
    new_convo = conversation[0:update_message.message_id]
    new_convo.append({"id": len(new_convo), "sender": "user", "text": update_message.text})

    # Generate bot response to edited message
    bot_response = generate_bot_response(update_message.text)

    new_convo.append({"id": len(new_convo) + 1, "sender": "bot", "text": bot_response})
    conversations[conversation_id] = new_convo

    return {"status": "message updated", "response": conversations[conversation_id]}

@app.post("/delete_message")
def delete_message(message_to_delete: DeleteMessage):
    conversation_id = message_to_delete.conversation_id

    # handle invalid conversation ids
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]

    if message_to_delete.message_id > len(conversation):
        raise HTTPException(status_code=404, detail="Invalid message id")

    new_convo = conversation[0:message_to_delete.message_id]

    conversations[conversation_id] = new_convo

    return {"status": "message updated", "response": conversations[conversation_id]}
