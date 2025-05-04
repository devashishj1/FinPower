import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes
from src.graph import Workflow
from dotenv import load_dotenv
import os, base64, json
from src.tools.GmailTools import GmailToolsClass

# Load .env file
load_dotenv()


app = FastAPI(
    title="Gmail Automation",
    version="1.0",
    description="LangGraph backend for the AI Gmail automation workflow",
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

def get_runnable():
    return  Workflow().app

# Fetch LangGraph Automation runnable which generates the workouts
runnable = get_runnable()

# Create the Fast API route to invoke the runnable
add_routes(app, runnable)

@app.on_event("startup")
async def subscribe_gmail_push():
    # Subscribe to Gmail push notifications via Pub/Sub
    topic = os.environ.get("GMAIL_PUBSUB_TOPIC")
    if topic:
        GmailToolsClass().service.users().watch(
            userId="me",
            body={"labelIds": ["INBOX"], "topicName": topic}
        ).execute()

@app.post("/gmail/webhook")
async def gmail_webhook(request: Request):
    # Handle Pub/Sub push from Gmail
    envelope = await request.json()
    data = envelope.get("message", {}).get("data")
    if not data:
        return {"status": "no_message"}
    notif = json.loads(base64.urlsafe_b64decode(data).decode())
    # Fetch new emails and create drafts
    gtools = GmailToolsClass()
    new_emails = gtools.fetch_unanswered_emails()
    for email in new_emails:
        # auto-create draft with original body
        gtools.create_draft_reply(email, "")
    return {"status": "processed", "count": len(new_emails)}

def main():
    # Start the API
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()