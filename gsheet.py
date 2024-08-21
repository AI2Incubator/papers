import os
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from google.cloud import service_usage_v1
from googleapiclient.errors import HttpError

PROJECT_ID = 'paper-review-harmonious'

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE = 'google_oauth_credentials.json'
TOKEN_FILE = 'token.json'
SERVICE_ACCOUNT_FILE = 'service_account.json'


# cmdline: gcloud services enable sheets.googleapis.com
def enable_sheets_api(project_id):
    client = service_usage_v1.ServiceUsageClient()
    service_name = f"projects/{project_id}/services/sheets.googleapis.com"
    request = service_usage_v1.EnableServiceRequest(
        dict(name=service_name)
    )

    operation = client.enable_service(request=request)

    print("Waiting for operation to complete...")
    response = operation.result()

    print(f"Service {service_name} enabled successfully")
    return response


class GSheet:
    def __init__(self, papers, spreadsheet_name):
        self.abstracts = [paper['abstract'] for paper in papers]
        for paper in papers:
            del paper['abstract']

        self.papers = papers
        self.spreadsheet_name = spreadsheet_name
        self.creds = self.authenticate()
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.spreadsheet_id = None
        self.column_names = list(papers[0].keys())
        self.paper_values = [list(paper.values()) for paper in papers]
        self.titles = [paper['title'] for paper in papers]
        self.pdf_urls = [paper['arXivPdf'] for paper in papers]

    @staticmethod
    def authenticate():
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        return creds

    def create_spreadsheet(self, sheet_title="Sheet1"):
        spreadsheet = self.service.spreadsheets().create(body={
            'properties': {'title': self.spreadsheet_name}
        }).execute()

        spreadsheet_id = spreadsheet['spreadsheetId']
        self.spreadsheet_id = spreadsheet_id

        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=sheet_title,
            valueInputOption='RAW',
            body={'values': ([self.column_names] + self.paper_values)}
        ).execute()

        return spreadsheet_id

    def insert_clickable_urls(self, titles, urls, sheet_id=0, column_index=1):
        """Assume: Sheet1 is the only sheet, and inserting into the second column (index = 1)"""
        requests = []
        for i, (title, url) in enumerate(zip(titles, urls)):
            requests.append({
                'updateCells': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': i + 1,
                        'endRowIndex': i + 2,
                        'startColumnIndex': column_index,
                        'endColumnIndex': column_index + 1
                    },
                    'rows': [{
                        'values': [{
                            'userEnteredValue': {'formulaValue': f'=HYPERLINK("{url}", "{title}")'}
                        }]
                    }],
                    'fields': 'userEnteredValue'
                }
            })

        body = {'requests': requests}
        self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()

    def wrap_text_in_columns(self, columns_to_wrap, strategy, sheet_id=0):
        num_rows = len(self.papers)

        requests = []
        for col in columns_to_wrap:
            col_index = self.column_names.index(col)
            print(f"Wrapping text in {col} with index {col_index}")
            requests.append({
                "updateCells": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": num_rows + 1,
                        "startColumnIndex": col_index,
                        "endColumnIndex": col_index + 1
                    },
                    "rows": [{"values": [{"userEnteredFormat": {"wrapStrategy": f"{strategy}"}}]} for _ in
                             range(num_rows)],
                    "fields": "userEnteredFormat.wrapStrategy"
                }
            })

        body = {
            'requests': requests
        }

        self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()

    def set_cell_dims(self, column_list, pixels_list, dim, sheet_id=0):
        requests = []
        for column, pixels in zip(column_list, pixels_list):
            col_index = self.column_names.index(column)
            print(f"Setting dimension {dim} for column {column}, index {col_index} to {pixels} pixels")
            requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': sheet_id,
                        'dimension': dim,
                        'startIndex': col_index,
                        'endIndex': col_index + 1
                    },
                    'properties': {
                        'pixelSize': pixels
                    },
                    'fields': 'pixelSize'
                }
            })

        body = {
            'requests': requests
        }

        self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()

    def insert_notes(self, notes, col):
        requests = []
        col_index = self.column_names.index(col)
        for i, note in enumerate(notes):
            requests.append({
                'updateCells': {
                    'range': {
                        'sheetId': 0,  # Adjust if using a different sheet
                        'startRowIndex': i + 1,
                        'endRowIndex': i + 2,
                        'startColumnIndex': col_index,
                        'endColumnIndex': col_index + 1
                    },
                    'rows': [
                        {
                            'values': [
                                {
                                    'note': note
                                }
                            ]
                        }
                    ],
                    'fields': 'note'
                }
            })

        body = {
            'requests': requests
        }

        self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()

    # does not work yet
    def make_sheet_public(self):
        creds = service_account.Credentials.from_service_account_file(
            'service_account.json', scopes=['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets'])

        drive_service = build('drive', 'v3', credentials=creds)
        permission = {
            'type': 'anyone',
            'role': 'reader',
        }

        permissions = drive_service.permissions().list(fileId=self.spreadsheet_id, supportsAllDrives=True).execute()
        for permission in permissions.get('permissions', []):
            print(f"Permission ID: {permission['id']}")
            print(f"Type: {permission['type']}")
            print(f"Role: {permission['role']}")
            if 'emailAddress' in permission:
                print(f"Email: {permission['emailAddress']}")

        try:
            # First, check if the file exists and is accessible
            file = drive_service.files().get(fileId=self.spreadsheet_id).execute()
            print(f"File found: {file['name']}")

            # If file exists, proceed with changing permissions
            drive_service.permissions().create(
                fileId=self.spreadsheet_id,
                body=permission,
                fields='id'
            ).execute()
            print(f"Spreadsheet is now viewable by anyone: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}")
        except HttpError as error:
            if error.resp.status == 404:
                print(
                    f"Error: File with ID {self.spreadsheet_id} not found. Please check the ID and make sure the service account has access to the file.")
            else:
                print(f"An error occurred: {error}")

# %%