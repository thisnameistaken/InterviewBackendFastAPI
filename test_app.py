from fastapi.testclient import TestClient
from main import app, conversations

# Run with python -m pytest test_app.py

client = TestClient(app)

# Make sure new conversations are being created properly
def test_create_new_conversation():
  response = client.post("/start_conversation")
  assert response.status_code == 200

  status = response.json().get("status")
  assert status == "conversation started"

  assert conversations[response.json().get("conversation_id")] == []

# Make sure we can add to the conversation
def test_add_response():
  response = client.post("/start_conversation")
  assert response.status_code == 200

  convo_id = response.json().get("conversation_id")

  payload = {
    "conversation_id": convo_id,
    "text": "tell me a random fact"
  }

  # Send the message request
  response = client.post("/send_message", json=payload)

  assert response.status_code == 200

  status = response.json().get("status")
  assert status == "message sent"

  assert len(conversations[convo_id]) > 0

# Make sure we can correctly delete items from the conversation
def test_delete_response():
  response = client.post("/start_conversation")
  assert response.status_code == 200

  convo_id = response.json().get("conversation_id")

  payload = {
    "conversation_id": convo_id,
    "text": "tell me a random fact"
  }

  # Send the message request
  response = client.post("/send_message", json=payload)
  assert response.status_code == 200

  payload = {
    "conversation_id": convo_id,
    "message_id": 0
  }

  # delete the message
  response = client.post("/delete_message", json=payload)
  assert response.status_code == 200

  assert len(conversations[convo_id]) == 0

# Make sure we can correctly edit messages in the conversation
def test_edit_message():
  response = client.post("/start_conversation")
  assert response.status_code == 200

  convo_id = response.json().get("conversation_id")

  payload = {
    "conversation_id": convo_id,
    "text": "tell me a random fact"
  }

  # Send the message request
  response = client.post("/send_message", json=payload)
  assert response.status_code == 200

  payload = {
    "conversation_id": convo_id,
    "message_id": 0,
    "text": "Something completely different"
  }

  # change the text of the message
  response = client.post("/update_message", json=payload)
  assert response.status_code == 200

  assert conversations[convo_id][0]["text"] == "Something completely different"





