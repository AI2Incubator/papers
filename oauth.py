from google.oauth2 import service_account
from googleapiclient.discovery import build

PROJECT_ID = 'paper-review-harmonious'

credentials = service_account.Credentials.from_service_account_file(
    'path/to/service_account.json',
    scopes=['https://www.googleapis.com/auth/cloud-platform']
)

service = build('iam', 'v1', credentials=credentials)

client_id = service.projects().serviceAccounts().keys().create(
    name=f'projects/{PROJECT_ID}/serviceAccounts/{SERVICE_ACCOUNT_EMAIL}',
    body={}
).execute()