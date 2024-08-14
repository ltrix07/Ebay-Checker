from moduls import RequestToGoogleSheets
from main_settings import col_names


def test_get_headers():
    google_api = RequestToGoogleSheets(
        '1mB5b850256wG8gcmzeJc1P2Zal_N7owj74DM2lMLVPg',
        'LISTINGS',
        r'C:\Users\Владимир\PycharmProjects\Ebay-Checker\credentials\google_creds.json',
        col_names
    )
    headers = google_api.get_headers()
    print(headers)


if __name__ == '__main__':
    test_get_headers()
