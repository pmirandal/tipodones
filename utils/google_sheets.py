import os
import json
import gspread

from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_NAME = "Seguimiento Materiales FAEST"


def conectar_google():

    credentials_info = json.loads(
        os.environ["GOOGLE_CREDENTIALS"]
    )

    credentials = Credentials.from_service_account_info(
        credentials_info,
        scopes=SCOPES
    )

    client = gspread.authorize(
        credentials
    )

    spreadsheet = client.open(
        SPREADSHEET_NAME
    )

    return spreadsheet
