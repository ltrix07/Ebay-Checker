""" --- Parsing settings --- """
allow_triggers = ['CURRENTLY SOLD OUT', 'We looked everywhere.', 'Looks like this page is missing.',
                  'The item you selected is unavailable', 'The item you selected has ended',
                  'This listing was ended', "The listing you're looking for has ended",
                  'Service Unavailable - Zero size object', 'This item is out of stock.',
                  'This listing sold', 'This listing ended']


headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'referer': 'https://www.google.com/',
    'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    'sec-ch-ua-full-version': '"124.0.6367.207"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"Linux"',
    'sec-ch-ua-platform-version': '"6.6.15"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'cross-site',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}


""" --- Parser keys --- """
parse_keys_price = ['//div[@class="x-price-primary"][1]//span[@class="ux-textspans"]/text()']
parse_keys_ship_price = ['//div[@class="ux-labels-values__values col-9"][1]//div[1]//span[contains(concat(" ", normalize-space(@class), " "), " ux-textspans ") and contains(concat(" ", normalize-space(@class), " "), " ux-textspans--BOLD ")]/text()',
                         '//div[@class="ux-labels-values__values col-9"][1]//span[@class="ux-textspans ux-textspans--POSITIVE ux-textspans--BOLD"]/text()']
parse_keys_quantity = [{'s': '"maxValue":"', 'e': '"'}]
parse_keys_ship_date = [{'s': 'and "},{"_type":"TextSpan","text":"', 'e': '"'},
                        {'s': '"text":"Get it by ', 'e': '"'},
                        {'s': 'Estimated on or before "},{"_type":"TextSpan","text":"', 'e': '"'},
                        {'s': 'and </span><!--F/--><!--F#10[3]--><span class="ux-textspans ux-textspans--BOLD">', 'e': '<'}]
parse_keys_supplier_name = ['//div[@class="x-sellercard-atf__info__about-seller"][1]//a[@class="ux-action"][1]//span[@class="ux-textspans ux-textspans--BOLD"]/text()']
parse_keys_supplier_name_scalp = [{'s': 'data-clientpresentationmetadata=\'{"_ssn":"', 'e': '"'},
                                  {'s': '{"_ssn":"', 'e': '"'}]
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
main_block = ['//div[@class="center-panel-container vi-mast"]/text()']
