from moduls import RequestToGoogleSheets
from main_settings import col_names


def test_get_batch():
    google_api = RequestToGoogleSheets(
        '1mB5b850256wG8gcmzeJc1P2Zal_N7owj74DM2lMLVPg',
        'LISTINGS',
        r'C:\Users\Владимир\PycharmProjects\Ebay-Checker\credentials\test.json',
        col_names
    )
    print('Class was setting')
    data = google_api.get_batch(['LISTINGS!D1:D101'])
    print(data)


if __name__ == '__main__':
    test_get_batch()
