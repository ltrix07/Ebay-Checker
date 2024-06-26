""" --- Server settings --- """
server_host = '91.209.226.51:3000'  # Server host

strategy = 'drop'
standard_stock = 33
transient_vice_for_threads = 50000

""" --- Amazon settings --- """
amz_creds = {
    "lwa_app_id": None,
    "lwa_client_secret": None,  # Amazon Creds
    "refresh_token": None,
}

seller_id = 'A1BK27H3YOSZ8C'  # Seller ID
shop_name = 'Sheva 1'  # Shop name


""" --- Google settings --- """
google_creds_path = './credentials/google_creds.json'  # Google Creds
spreadsheet_id = '13_zM7XdO7kvvsdic9Y6Gcc0Aed2BmGRss-wy9LepWc4'  # Spreadsheet ID
main_worksheet = 'EBAY'  # Main worksheet name
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
repricer_rule = 'DP'  # Repricer rule
repricer_logs = {
    'username': '09865371lol@gmail.com',
    'password': 'Qaz111qaz111!'
}


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



