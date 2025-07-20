from __future__ import print_function
import os.path
import logging
import pickle
from flask_cors import CORS
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import BatchHttpRequest
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# -----------------------------------------------------------
# Configuration
# -----------------------------------------------------------
APP_HOST = '127.0.0.1'
APP_PORT = 5000
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_FILE = 'backend server\\credentials.json'
TOKEN_FILE = 'token.pickle'

# -----------------------------------------------------------
# Flask setup
# -----------------------------------------------------------
app = Flask(__name__)
# Allow CORS from any origin (so the Chrome extension can call localhost:5000)
CORS(app, origins=["*"])

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------
# Utility: build an authorized Gmail API service
# -----------------------------------------------------------
def get_gmail_service():
    
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
    return service


# -----------------------------------------------------------
# Endpoint: List user's drafts (ID + subject)
# -----------------------------------------------------------
@app.route('/list_drafts', methods=['GET'])
def list_drafts():
    """
    Returns JSON: { status: 'success', drafts: [ { id, subject }, ... ] }
    or on error: { status: 'error', error: '<message>' } with HTTP 500.
    """
    try:
        service = get_gmail_service()
        drafts_response = service.users().drafts().list(userId='me', maxResults=100).execute()
        drafts = drafts_response.get('drafts', [])

        results = []

        def callback(request_id, response, exception):
            if exception is not None:
                results.append({'id': request_id, 'subject': '(Error)'})
            else:
                headers = response.get('message', {}).get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
                results.append({'id': request_id, 'subject': subject})

        batch = service.new_batch_http_request(callback=callback)

        for draft in drafts:
            draft_id = draft['id']
            batch.add(
                service.users().drafts().get(userId='me', id=draft_id, format='metadata'),
                request_id=draft_id
            )

        batch.execute()

        # Sort the results to match the original order
        sorted_results = sorted(results, key=lambda x: next((i for i, d in enumerate(drafts) if d['id'] == x['id']), 0))

        return jsonify({'status': 'success', 'drafts': sorted_results})

    except HttpError as error:
        return jsonify({'status': 'error', 'error': f'An error occurred: {error}'}), 500

# -----------------------------------------------------------
# Endpoint: Duplicate a draft N times
# -----------------------------------------------------------
@app.route('/duplicate_draft', methods=['POST'])
def duplicate_draft():
    """
    Expects JSON body:
      {
        "draft_id": "<string>",
        "copies": <integer>
      }
    Returns JSON:
      { status: 'success', duplicated: <number> }
    or on error:
      { status: 'error', error: '<message>' } with HTTP 400 or 500.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'status': 'error', 'error': 'Invalid JSON body.'}), 400

    draft_id = data.get('draft_id')
    copies = data.get('copies')

    # 1) Validate inputs
    if not draft_id or not isinstance(draft_id, str):
        return jsonify({'status': 'error', 'error': 'draft_id is required and must be a string.'}), 400
    if copies is None:
        return jsonify({'status': 'error', 'error': 'copies is required.'}), 400
    try:
        copies = int(copies)
    except ValueError:
        return jsonify({'status': 'error', 'error': 'copies must be an integer.'}), 400
    if copies <= 0:
        return jsonify({'status': 'error', 'error': 'copies must be a positive integer.'}), 400

    try:
        service = get_gmail_service()
        # 2) Fetch the draft in 'raw' format so we get the base64-encoded MIME message
        draft_obj = service.users().drafts().get(
            userId='me',
            id=draft_id,
            format='raw'
        ).execute()

        raw_message = draft_obj.get('message', {}).get('raw')
        if not raw_message:
            raise ValueError("Draft has no 'raw' message field.")

        # 3) Loop and create new drafts
        # created = 0
        # for _ in range(copies):
        #     body = {
        #         'message': {
        #             'raw': raw_message
        #         }
        #     }
        #     service.users().drafts().create(userId='me', body=body).execute()
        #     created += 1
        
        ## using batch requests
        batch = service.new_batch_http_request()
        created = 0

        def callback(request_id, response, exception):
            nonlocal created
            if exception is None:
                created += 1
            else:
                print(f"Error creating draft {request_id}: {exception}")

        for i in range(copies):
            body = {'message': {'raw': raw_message}}
            batch.add(service.users().drafts().create(userId='me', body=body), request_id=str(i))

        batch.execute()


        return jsonify({'status': 'success', 'duplicated': created})

    except HttpError as e:
        logger.error(f"Gmail API error in /duplicate_draft: {e}")
        return jsonify({'status': 'error', 'error': f"Gmail API: {e}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in /duplicate_draft: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/status')
def status():
    return jsonify({"status": "Ok"})
# -----------------------------------------------------------
# Run the Flask app
# -----------------------------------------------------------
if __name__ == '__main__':
    logger.info(f"Starting Flask app at http://{APP_HOST}:{APP_PORT}")
    app.run(host=APP_HOST, port=APP_PORT, debug=True)