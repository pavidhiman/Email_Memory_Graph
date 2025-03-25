import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email import message_from_bytes

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def get_emails(service, max_results=400):
    results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='raw').execute()
        raw_msg = base64.urlsafe_b64decode(msg_data['raw'].encode('ASCII'))
        mime_msg = message_from_bytes(raw_msg)
        emails.append({
            'subject': mime_msg['subject'],
            'from': mime_msg['from'],
            'date': mime_msg['date'],
            'body': mime_msg.get_payload()
        })
    return emails

if __name__ == "__main__":
    service = authenticate_gmail()
    emails = get_emails(service, max_results=5)
    for i, email in enumerate(emails):
        print(f"\n📬 Email {i+1}")
        print("Subject:", email['subject'])
        print("From:", email['from'])
        print("Date:", email['date'])
        print("Body:", email['body'][:300], '...')
