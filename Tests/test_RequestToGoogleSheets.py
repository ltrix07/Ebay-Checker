
def test_get_all_info():
    ls = list(range(1, 101))
    print(ls[10:20])



# def test_get_headers():
#     result = google_sheet.get_headers('EBAY')
#     print(result)
#
#
# def test_get_index_of_column():
#     names = ['sku', 'supplier1', 'price ebay', 'shipping', 'stock', 'shipping days', 'supplier name', 'variation']
#     print(google_sheet.get_index_of_column('EBAY', names))
#
#
# def test_get_data_by_columns():
#     names = ['sku', 'supplier1', 'price ebay', 'shipping', 'stock', 'shipping days', 'supplier name', 'variation']
#     result = google_sheet.get_data_by_columns('EBAY', names)
#
#     print(result)
#
#
# def test_set():
#     col_names = {'sku': 'sku',
#                  'url': 'supplier1',
#                  'price': 'price ebay',
#                  'shipping_price': 'shipping',
#                  'quantity': 'stock',
#                  'shipping_days': 'shipping days',
#                  'supplier': 'supplier name',
#                  'variations': 'variation'}
#
#     print(list(col_names.values()))


if __name__ == '__main__':
    test_get_all_info()
