import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying scopes, delete the token.pickle file
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'backend server\credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def list_drafts(service):
    results = service.users().drafts().list(userId='me').execute()
    return results.get('drafts', [])

import base64

def duplicate_draft(service, draft_id, times=3):
    original = service.users().drafts().get(userId='me', id=draft_id, format='raw').execute()
    raw_message = original['message']['raw']

    for i in range(times):
        draft_body = {
            'message': {
                'raw': raw_message
            }
        }
        service.users().drafts().create(userId='me', body=draft_body).execute()
    print(f"✅ Duplicated draft {times} times.")


if __name__ == '__main__':
    service = authenticate()
    drafts = list_drafts(service)

    if not drafts:
        print("No drafts found.")
    else:
        print("Available Drafts:")
        for i, d in enumerate(drafts):
            print(f"{i+1}. ID: {d['id']}")

        index = int(input("Select draft number to duplicate: ")) - 1
        count = int(input("How many copies? "))

        duplicate_draft(service, drafts[index]['id'], count)
