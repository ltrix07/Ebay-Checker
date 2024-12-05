import pytest
from unittest.mock import MagicMock
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from moduls import RequestsToEbay


@pytest.mark.asyncio
@pytest.mark.parametrize('page_slice, elem_key, except_value', [
    ('<div class=ux-labels-values__labels-content><div><!--F#0--><!--F#f_1--><!--F#11[0]--><span class=ux-textspans>'
     'Shipping:</span><!--F/--><!--F/--><!--F/--></div></div></div><div class="ux-labels-values__values col-9"><div '
     'class=ux-labels-values__values-content><div><!--F#0--><!--F#f_1--><!--F#11[0]--><span class="ux-textspans ux-te'
     'xtspans--BOLD">US $5.25</span><!--F/--><!--F#11[1]--><span class=ux-textspans>&nbsp;</span><!--F/--><!--F#11[2]'
     '--><span class=ux-textspans>Standard Shipping</span><!--F/--><!--F#11[3]--><span class=ux-textspans>. </span>'
     '<!--F/-->', 'ship_price', 5.25),
    ('ck","priceCurrency":"USD","price":"6.98"},"aggregateRating":{"@type":"AggregateRating","ratingValue":"4.83",'
     '"ratingCount":"6"},"gtin13":"736530623388","mpn":"13211546730, V137000030","model":"ES-1000 ES-2000 ES-210 '
     'ES-211 ES-', 'price', 6.98)
])
async def test_parser_page(page_slice, elem_key, except_value):
    row_mock = MagicMock()
    row_mock.__getitem__.side_effect = [
        'mock_sku',  # sku
        'http://mock-url.com',  # url
        100.0,  # price_previous
        10.0,  # shipping_price_previous
        5,  # quantity_previous
        '3-5 days',  # shipping_days_previous
        'Mock Supplier'  # supplier_name
    ]

    # Индексы, которые используются в функции
    parser_instance = RequestsToEbay(None, None, None, None, None,
                             None, None, None)
    parser_instance.sku_index = 0
    parser_instance.url_index = 1
    parser_instance.price_index = 2
    parser_instance.shipping_price_index = 3
    parser_instance.quantity_index = 4
    parser_instance.shipping_days_index = 5
    parser_instance.supplier_index = 6

    out_res = parser_instance.parser_page(page_slice, row_mock, 'http://0.0.0.0:8080')
    assert out_res['data'][elem_key] == except_value
