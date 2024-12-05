import re


def find_in_page_by_regular(page, strs):
    for str_ in strs:
        match = re.search(str_, page, re.DOTALL)
        if match:
            return match
    return None


def test_find_in_page_by_regular():
    string = 'ck","priceCurrency":"USD","price":"6.98"},"aggregateRating":{"@type":"AggregateRating","ratingValue":"4.83","ratingCount":"6"},"gtin13":"736530623388","mpn":"13211546730, V137000030","model":"ES-1000 ES-2000 ES-210 ES-211 ES-'
    regs = [r'"price":"([\d.]+)"']
    print(find_in_page_by_regular(string, regs))


def test_find_in_page_by_regular_logic():
    results = {}
    page = 'ck","priceCurrency":"USD","price":"6.98"},"aggregateRating":{"@type":"AggregateRating","ratingValue":"4.83","ratingCount":"6"},"gtin13":"736530623388","mpn":"13211546730, V137000030","model":"ES-1000 ES-2000 ES-210 ES-211 ES-'
    regs = [r'"price":"([\d.]+)"']
    results['price_supp'] = find_in_page_by_regular(page, regs)

    if 'See price on checkout' in page and results["price_supp"] is None:
        price = 0
    else:
        try:
            if results["price_supp"]:
                price = float(results["price_supp"].group(1))
            else:
                # await self.server_connect.post_error(f'На странице не была найдена цена. @L_trix\n'
                #                                      f'{url}', shop_name)
                raise Exception(f'Price is None in {url}')
        except ValueError:
            price = results["price_supp"].group(1)
        except Exception as error:
            with open('exception_page.html', 'w', encoding='utf-8') as file:
                file.write(page)
            raise Exception(f'{error} in {url}, {results["price_supp"]}')

    print(price)


if __name__ == '__main__':
    test_find_in_page_by_regular()
    test_find_in_page_by_regular_logic()
