""" --- Server settings --- """
server_host = '91.209.226.51:3000'  # Server host

strategy = 'listings'
standard_stock = 37
transient_vice_for_threads = 50000

""" --- Amazon settings --- """
amz_creds = {
    "lwa_app_id": 'amzn1.application-oa2-client.a93ba3c1fc6c473093b4045304e34fba',
    "lwa_client_secret": 'amzn1.oa2-cs.v1.9191c3fae6cda6c615f40a0bb318dcb1cd391b16d3a21b84c7b08cd1caef3216',  # Amazon Creds
    "refresh_token": 'Atzr|IwEBIENECGtwyidHYfCw7zwZbdwIWODfIe71ZQ-bwR5qy69ijsLnpW58SbykXmzJO4KuwANAqPZGXss6dPhSErZUTQ_-W2ue_R-ms-qvX7XMMN8iKYGrrCB5Oy9A8cLsTzHS8O6VwW13_kKNd3Dkl71I3XZfdpsp_i3YmcxpExED5d3Svz3Ptw3gTzV_iZi1rOL9dRSdqqm4iPTLcTr_5MVFi8cKQB75S5RHfOtICoxswdtn3OVGZsgU9HYusfUySlDHqZuCHlFiy4YEO-ycCxfkDMla1rITC1imJFdoEHiZTovdxhhmaO3_p-DYQOZ2BgvoFuiNW85ctrBwmzJeAlBgkBp8',
}

seller_id = None  # Seller ID
shop_name = 'Donald'  # Shop name


""" --- Google settings --- """
google_creds_path = './credentials/google_creds.json'  # Google Creds
spreadsheet_id = '1aztiN2AU115Ed7o6At3iQIXgVd0Fl0qk5rj1lqpeH1w'  # Spreadsheet ID
main_worksheet = 'LISTINGS'  # Main worksheet name
exceptions_worksheet = 'Exceptions'  # Worksheet with exceptions
exceptions_repricer_worksheet = 'Exceptions for Repricer'  # Worksheet with exceptions for "Repricer.com"
col_names = {'asin': 'asin',
             'sku': 'sku',
             'url': 'supplier1',
             'price': 'price ebay',
             'shipping_price': 'shipping',
             'quantity': 'stock',
             'shipping_days': 'shipping days',
             'supplier': 'supplier name',
             'variations': 'variation',
             'handling_time': 'handling-time',
             'merchant_shipping_template': 'merchant_shipping_group_name',
             'amazon_price': 'price amazon',
             "part number": None,
             "item weight": None,
             "product dimensions": None,
             "color": None,
             "unit count": None,
             "material type": None,
             "power source": None,
             "voltage": None,
             "wattage": None,
             "included components": None,
             "speed": None,
             "number of boxes": None,
             "title": None,
             "description": None
             }


""" --- Repricer settings --- """
repricer_rule = None  # Repricer rule
repricer_api_key = 'Basic MDk4NjUzNzFsb2xAZ21haWwuY29tOlFhejExMXFhejExMSE='  # Repricer API key


""" --- What information need to parse --- """
what_need_to_parse = {
    "price": True,
    "shipping price": True,
    "quantity": True,
    "shipping days": True,
    "supplier name": True,
    "part number": False,
    "item weight": False,
    "product dimensions": False,
    "color": False,
    "unit count": False,
    "material type": False,
    "power source": False,
    "voltage": False,
    "wattage": False,
    "included components": False,
    "speed": False,
    "number of boxes": False,
    "title": True,
    "description": False
}



