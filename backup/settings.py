""" --- Server settings --- """
server_host = '91.209.226.51:3000'  # Server host


""" --- Global settings --- """
strategy = 'brands' # Can be 'brands' or 'listings'


""" --- Amazon settings --- """
amz_creds = {
    "lwa_app_id": 'Atzr|IwEBIMlRR3JPV_fBr6r2SriKRbjjdPqSq35qcJEoep3_Bm5YgWemwfPIUywR-H1atB5V6MnVOXxKzFpUHhONpRAv0MUriDNeU4N1nYj3kWn9MZKKa3KC3-SMSnQbHC1MbXVRXhYl1nRzUrazL3rwkJxbel94cdph215JrOhi2VJ6ns5nuGe5-Rrz0FKVd0qopfRlRakxQvBYAaIWBzLnuFvFDfhTj5HoCSYohF8IIBPfZxdOMNBRPwUmWJylxtv3bQcUn9RB2rP0vc2TfF6jrhzbTZitCZ0h8jcwST-6rgDJ8wewQgaANYbuqmIsTyrOjuBTSeo',
    "lwa_client_secret": 'amzn1.application-oa2-client.c0a6ae54ef6042a4b65c8389cc022804',  # Amazon Creds
    "refresh_token": 'amzn1.oa2-cs.v1.3eb664ee4c4ed11bd300c953694122a5eb5545b591bd4b51efd3abafa701c6c2',
}
seller_id = None  # Seller ID
shop_name = 'Angel'  # Shop name


""" --- Google settings --- """
google_creds_path = './credentials/google_creds.json'  # Google Creds
spreadsheet_id = '1vL6sd8fuCL2H26MIHbhl77Gzb9tto4oKiH8to6fFnUQ'  # Spreadsheet ID
main_worksheet = 'EBAY'  # Main worksheet name
exceptions_worksheet = 'Exceptions'  # Worksheet with exceptions
exceptions_repricer_worksheet = 'Exceptions for Repricer'  # Worksheet with exceptions for "Repricer.com"
col_names = {'sku': 'sku',
             'url': 'supplier1',
             'price': 'price ebay',
             'shipping_price': 'shipping',
             'quantity': 'stock',
             'shipping_days': 'shipping days',
             'supplier': 'supplier name',
             'variations': 'variation',
             'handling_time': 'handling-time',
             'merchant_shipping_template': 'merchant_shipping_group_name',
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


""" --- Parsing settings --- """
allow_triggers = ['CURRENTLY SOLD OUT', 'We looked everywhere.', 'Looks like this page is missing.',
                  'The item you selected is unavailable', 'The item you selected has ended',
                  'This listing was ended', "The listing you're looking for has ended",
                  'Service Unavailable - Zero size object', 'This item is out of stock.',
                  'This listing sold', 'This listing ended']
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'accept-language': 'en;q=1.0',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    'sec-ch-ua-full-version': '"124.0.6367.60"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-platform-version': '"15.0.0"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
}
transient_vice_for_threads = 50000


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
    "title": False,
    "description": False
}


""" --- Parser keys --- """
parse_keys_price = ['//div[@class="x-price-primary"][1]//span[@class="ux-textspans"]/text()']
parse_keys_ship_price = ['//div[@class="ux-labels-values__values col-9"][1]//div[1]//span[contains(concat(" ", normalize-space(@class), " "), " ux-textspans ") and contains(concat(" ", normalize-space(@class), " "), " ux-textspans--BOLD ")]/text()',
                         '//div[@class="ux-labels-values__values col-9"][1]//span[@class="ux-textspans ux-textspans--POSITIVE ux-textspans--BOLD"]/text()']
parse_keys_quantity = [{'s': '"maxValue":"', 'e': '"'}]
parse_keys_ship_date = ['//div[@class="ux-labels-values__values col-9"][2]//span[contains(concat(" ", normalize-space(@class), " "), " ux-textspans ") and contains(concat(" ", normalize-space(@class), " "), " ux-textspans--BOLD ")][2]/text()',
                        '//div[@class="ux-labels-values__values col-9")][2]//span[contains(concat(" ", normalize-space(@class), " "), " ux-textspans ") and not(contains(concat(" ", normalize-space(@class), " "), " ux-textspans "))]/text()',
                        '//div[@class="vim ux-labels-values-with-custom-help"][1]//div[@class="ux-labels-values__values col-9"]//span[contains(concat(" ", normalize-space(@class), " "), " ux-textspans ") and contains(concat(" ", normalize-space(@class), " "), " ux-textspans--BOLD ")][2]/text()']
parse_keys_supplier_name = ['//div[@class="x-sellercard-atf__info__about-seller"][1]//a[@class="ux-action"][1]//span[@class="ux-textspans ux-textspans--BOLD"]/text()']
parse_keys_part_number = []
parse_keys_item_weight = []
parse_keys_product_dimensions = []
parse_keys_color = []
parse_keys_unit_count = []
parse_keys_material_type = []
parse_keys_power_source = []
parse_keys_voltage = []
parse_keys_wattage = []
parse_keys_included_components = []
parse_keys_speed = []
parse_keys_number_of_boxes = []
parse_title_h1 = ['//h1[@class="x-item-title__mainTitle"]']
parse_keys_description = []

parse_select_div = ['//div[@class="x-msku__box-cont"]']
parse_catalog_check = ['//div[@class="cat-wrapper"]',
                       '//div[@class="s-item s-item__pl-on-bottom"]']
pick_up_info_check = ['//div[contains(concat(" ", normalize-space(@class), " "), " vim ") and contains(concat(" ", normalize-space(@class), " "), " d-vi-evo-region ")]/text()']
main_block = ['//div[@class="center-panel-container vi-mast"]']



