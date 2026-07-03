import base64
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class ReportSender:
    def __init__(self):
        self.creds = None
        self._authenticate()

    def _authenticate(self):
        token_path = os.path.join(BASE_DIR, 'token.json')
        creds_path = os.path.join(BASE_DIR, 'credentials.json')
        
        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open(token_path, 'w') as token:
                token.write(self.creds.to_json())

    def send_report(self, report_data: dict, recipient="rmisegal+uoh26b@gmail.com"):
        service = build('gmail', 'v1', credentials=self.creds)
        
        # Format report data as JSON
        json_report = json.dumps(report_data, indent=2)
        
        message_text = f"Subject: HW6 Auto Report JSON\n\n{json_report}"
        message = base64.urlsafe_b64encode(message_text.encode("utf-8")).decode("utf-8")
        
        try:
            message_body = {'raw': message}
            send_message = service.users().messages().send(userId="me", body=message_body).execute()
            print(f"Message Id: {send_message['id']} successfully sent to {recipient}")
        except Exception as error:
            print(f"An error occurred: {error}")

if __name__ == "__main__":
    # Test report structure based on internal game JSON format
    test_report = {
        "group_name": "Team-Alpha",
        "students": [],
        "github_repo": "https://github.com/amaraqusai/HW6.git",
        "cop_mcp_url": "http://localhost:5000",
        "thief_mcp_url": "http://localhost:5001",
        "timezone": "Asia/Jerusalem",
        "sub_games": [],
        "totals": {
            "cop": 90,
            "thief": 40
        }
    }
    
    # Needs credentials.json to actually send
    creds_path = os.path.join(BASE_DIR, 'credentials.json')
    if os.path.exists(creds_path):
        sender = ReportSender()
        sender.send_report(test_report)
    else:
        print("credentials.json not found. Save it to test sending emails.")
