from lxml import html

parse_keys_price = ['//div[@class="x-price-primary"][1]//span[@class="ux-textspans"]/text()']
parse_keys_ship_price = ['//div[@class="ux-labels-values__values col-9"][1]//div[1]//span[contains(concat(" ", normalize-space(@class), " "), " ux-textspans ") and contains(concat(" ", normalize-space(@class), " "), " ux-textspans--BOLD ")]/text()',
                         '//div[@class="ux-labels-values__values col-9"][1]//span[@class="ux-textspans ux-textspans--POSITIVE ux-textspans--BOLD"]/text()']
parse_keys_quantity = [{'s': '"maxValue":"', 'e': '"'}]
parse_keys_ship_date = ['//div[@class="ux-labels-values__values col-9"][2]//span[contains(concat(" ", normalize-space(@class), " "), " ux-textspans ") and contains(concat(" ", normalize-space(@class), " "), " ux-textspans--BOLD ")][2]/text()',
                        '//div[contains(concat(" ", normalize-space(@class), " "), " ux-labels-values__values ") and contains(concat(" ", normalize-space(@class), " "), " col-9 ")][2]//span[contains(concat(" ", normalize-space(@class), " "), " ux-textspans ") and not(contains(concat(" ", normalize-space(@class), " "), " ux-textspans "))]/text()',
                        '//div[@class="vim ux-labels-values-with-custom-help"][1]//div[@class="ux-labels-values__values col-9"]//span[contains(concat(" ", normalize-space(@class), " "), " ux-textspans ") and contains(concat(" ", normalize-space(@class), " "), " ux-textspans--BOLD ")][2]/text()']
parse_keys_supplier_name = ['//div[@class="x-sellercard-atf__info__about-seller"][1]//a[@class="ux-action"][1]//span[@class="ux-textspans ux-textspans--BOLD"]/text()']
parse_title_h1 = ['//h1[@class="x-item-title__mainTitle"]']
parse_select_div = ['//div[@class="x-msku__box-cont"]']
parse_catalog_check = ['//div[@class="cat-wrapper"]',
                       '//div[@class="s-item s-item__pl-on-bottom"]']
pick_up_info_check = ['//div[contains(concat(" ", normalize-space(@class), " "), " vim ") and contains(concat(" ", normalize-space(@class), " "), " d-vi-evo-region ")]/text()']
main_block = ['//div[@class="center-panel-container vi-mast"]']


def __find_in_page_by_xpath(lxml_tree, elements=list):
    for element in elements:
        desired_element = lxml_tree.xpath(element)
        if desired_element:
            return desired_element
    return None

def main():
    with open('exception_page.html', 'r', encoding='utf-8') as file:
        page = file.read()
        
    tree = html.fromstring(page)
    
    shipping_price = __find_in_page_by_xpath(tree, parse_keys_ship_price)
    ship_date_supp = __find_in_page_by_xpath(tree, parse_keys_ship_date)
    
    if shipping_price:
        shipping_price = '0' if 'Free' in shipping_price[0] \
            else shipping_price[0].replace('US $', '')
    else:
        raise Exception(f'Shipping price is None')
    
    try:
        if shipping_price:
            shp_price = float(shipping_price)
            print(shp_price)
        else:
            raise Exception(f'Shipping price is None')
    except Exception as error:
        with open('exception_page.html', 'w', encoding='utf-8') as file:
            file.write(page)
        raise Exception(f'{error} in {shipping_price}')

    if ship_date_supp:
        try:
            if ship_date_supp[0]:
                ship_date_supp = ship_date_supp[0]
                print(ship_date_supp)
            else:
                raise Exception(f'Shipping days is None')
        except ValueError:
            raise ValueError(f'Error with str {ship_date_supp}')


if __name__ == '__main__':
    main()