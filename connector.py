import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WorkflowAPIConnector:
    """
    A connector class to interact with the Gmail Automation API
    """
    
    def __init__(self, api_url=None):
        self.api_url = api_url or os.getenv("API_URL", "http://localhost:8000")
    
    def start_workflow(self, initial_state=None):
        """Start the workflow with an optional initial state"""
        if initial_state is None:
            initial_state = {
                "emails": [],
                "current_email": {
                    "id": "",
                    "threadId": "",
                    "messageId": "",
                    "references": "",
                    "sender": "",
                    "subject": "",
                    "body": ""
                },
                "email_category": "",
                "signatories_count": 0,
                "generated_email": "",
                "rag_queries": [],
                "retrieved_documents": "",
                "writer_messages": [],
                "sendable": False,
                "trials": 0
            }
        
        try:
            response = requests.post(
                f"{self.api_url}/invoke",
                json={"input": initial_state}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "timestamp": datetime.now()
                }
            else:
                return {
                    "success": False,
                    "error": f"API returned status code {response.status_code}",
                    "response": response.text,
                    "timestamp": datetime.now()
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now()
            }
    
    def stream_workflow(self, initial_state=None):
        """Stream the workflow execution with an optional initial state"""
        if initial_state is None:
            initial_state = {
                "emails": [],
                "current_email": {
                    "id": "",
                    "threadId": "",
                    "messageId": "",
                    "references": "",
                    "sender": "",
                    "subject": "",
                    "body": ""
                },
                "email_category": "",
                "signatories_count": 0,
                "generated_email": "",
                "rag_queries": [],
                "retrieved_documents": "",
                "writer_messages": [],
                "sendable": False,
                "trials": 0
            }
        
        try:
            response = requests.post(
                f"{self.api_url}/stream",
                json={"input": initial_state},
                stream=True
            )
            
            if response.status_code == 200:
                # Stream the responses
                for line in response.iter_lines():
                    if line:
                        try:
                            # Parse the SSE data format
                            line_text = line.decode('utf-8')
                            if line_text.startswith('data: '):
                                data_json = json.loads(line_text[6:])
                                yield {
                                    "success": True,
                                    "data": data_json,
                                    "timestamp": datetime.now()
                                }
                        except Exception as e:
                            yield {
                                "success": False,
                                "error": f"Error parsing stream data: {str(e)}",
                                "data": line.decode('utf-8') if line else None,
                                "timestamp": datetime.now()
                            }
            else:
                yield {
                    "success": False,
                    "error": f"API returned status code {response.status_code}",
                    "response": response.text,
                    "timestamp": datetime.now()
                }
        except Exception as e:
            yield {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now()
            }
    
    def get_workflow_status(self):
        """Get the current status of the workflow"""
        try:
            response = requests.get(f"{self.api_url}/status")
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "timestamp": datetime.now()
                }
            else:
                return {
                    "success": False,
                    "error": f"API returned status code {response.status_code}",
                    "response": response.text,
                    "timestamp": datetime.now()
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now()
            }
    
    def trigger_gmail_webhook(self):
        """Manually trigger the Gmail webhook to process new emails"""
        try:
            response = requests.post(f"{self.api_url}/gmail/webhook", json={
                "message": {
                    "data": "ewogICJlbWFpbFVwZGF0ZSI6IHRydWUKfQ=="  # Base64 encoded '{"emailUpdate": true}'
                }
            })
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "timestamp": datetime.now()
                }
            else:
                return {
                    "success": False,
                    "error": f"API returned status code {response.status_code}",
                    "response": response.text,
                    "timestamp": datetime.now()
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now()
            }