import os
import asyncio
import time
import aiohttp
import google.auth.exceptions
import gspread.utils
import sys
import json
import codecs
import re
import sp_api.base.exceptions
import websockets
import csv
import base64
import requests
import random
from typing import Optional
from xsellco_api.sync import Repricers
from sp_api.base import Marketplaces, SellingApiException
from sp_api.api import Feeds
from sp_api.base.reportTypes import ReportType
from lxml import html
from lxml.etree import ParserError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from aiohttp import client_exceptions
from aiohttp import BasicAuth
from itertools import cycle
from parser_settings import *
from main_settings import what_need_to_parse, col_names, shop_name, server_host, standard_stock, \
    strategy

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
timeout = aiohttp.ClientTimeout(total=120)


class RequestsToEbay:
    def __init__(self, data, exceptions, exceptions_repricer, proxies, server_connect, indices,
                 reserve_proxies=None, allow_triggers=None):
        self.data = data
        self.exceptions = exceptions
        self.exceptions_repricer = exceptions_repricer
        self.proxies = proxies
        self.allow_triggers = allow_triggers
        self.reserve_proxies = reserve_proxies
        self.server_connect = server_connect
        self.report = {
            'all_processed': 0,
            'nones_new': 0,
            'stock_new': 0,
            'new_price': 0,
            'new_ship_price': 0,
            'errors': {
                'unknown_errors': 0,
                'no_block_with_info': 0,
                'no_title_in_link': 0,
                'proxy_errors': 0,
                'time_out_errors': 0,
                'ebay_close_connection': 0,
                'server_close_connection': 0,
                'error 400': 0
            },
        }
        self.sku_index = indices["sku"]
        self.url_index = indices["url"]
        self.price_index = indices["price"]
        self.shipping_price_index = indices["shipping_price"]
        self.quantity_index = indices["quantity"]
        self.shipping_days_index = indices["shipping_days"]
        self.supplier_index = indices["supplier"]
        self.variations_index = indices["variations"]

        self.file_worker = FilesWorker()

    @staticmethod
    def add_proxies_to_list(proxies_list_from_supplier, proxies_list_for_app):
        for proxy_info in proxies_list_from_supplier:
            login = proxy_info['login']
            password = proxy_info['password']
            ip = proxy_info['ip']
            port = proxy_info['port_http']
            proxy = f'{login}:{password}@{ip}:{port}'
            proxies_list_for_app.append(proxy)

        return proxies_list_for_app

    def __add_to_report(self, new_data, previous_price, previous_shipping_price, previous_qty):
        args = [previous_qty, previous_price, previous_shipping_price]
        for arg in args:
            if not isinstance(arg, dict):
                try:
                    float(arg)
                except ValueError:
                    previous_qty = 0
                    previous_price = 0
                    previous_shipping_price = 0

        try:
            if float(previous_qty) == 0 and int(new_data["data"]["quantity"]) != float(previous_qty):
                self.report["stock_new"] += 1
            if float(previous_qty) != 0 and int(new_data["data"]["quantity"]) == 0:
                self.report["nones_new"] += 1
            if float(previous_price) != float(new_data["data"]["price"]):
                self.report["new_price"] += 1
            if float(previous_shipping_price) != float(new_data["data"]["ship_price"]):
                self.report["new_ship_price"] += 1
        except ValueError:
            return

    # Функция для авторизации прокси
    @staticmethod
    async def __proxy_auth(proxy):
        username = proxy.split(':')[0]
        password = proxy.split(':')[1].split('@')[0]
        host_and_port = proxy.split('@')[1]

        proxy_url = 'http://' + host_and_port
        proxy_auth = BasicAuth(username, password)

        return proxy_url, proxy_auth

    @staticmethod
    async def __date_to_days(string_with_date):
        if 'Get it by ' in string_with_date:
            string_with_date = string_with_date.replace('Get it by ', '')
        date_ebay = datetime.strptime(string_with_date + ' 2024', '%a, %b %d %Y').date()
        today = date.today()

        days_left = (date_ebay - today).days

        return days_left

    @staticmethod
    async def __find_in_page_by_xpath(lxml_tree, elements):
        for element in elements:
            desired_element = lxml_tree.xpath(element)
            if desired_element:
                return desired_element
        return None

    @staticmethod
    async def __find_in_page_by_slicing(page, strs):
        for str_ in strs:
            try:
                index = page.index(str_.get('s'))
                index2 = page.index(str_.get('e'), index + len(str_.get('s')))
                return page[index + len(str_.get('s')):index2]
            except ValueError:
                continue
        return None

    @staticmethod
    async def __find_in_page_by_regular(page, strs) -> Optional[re.Match]:
        for str_ in strs:
            match = re.search(str_, page, re.DOTALL)
            if match:
                return match
        return None

    @staticmethod
    def __other_countries(text):
        text = text.lower()
        pattern = re.compile(r'located in: .*?(usa|us|united states)\b.*?</span>', re.IGNORECASE)
        match = pattern.search(text)
        try:
            if len(match[0]) < 200:
                return False
            else:
                return True
        except TypeError:
            return None

    @staticmethod
    def __not_latin(text):
        pattern = re.compile(r'[\u4E00-\u9FFF\u3400-\u4DBF\u3040-\u30FF\uAC00-\uD7AF]', re.IGNORECASE)
        return bool(pattern.search(text))

    @staticmethod
    def __does_not_ship_to(text):
        text = text.lower()
        pattern = re.compile(r'does not ship to (.*?)</span>', re.IGNORECASE)
        match = pattern.search(text)
        try:
            if match:
                return match[0]
        except TypeError:
            return None

        return None

    async def parser_page(self, page, row, proxy_for_check):
        sku, url, price_previous, shipping_price_previous, quantity_previous, shipping_days_previous, \
            supplier_name = row[self.sku_index], row[self.url_index].split('?')[0], \
            row[self.price_index], row[self.shipping_price_index], row[self.quantity_index], \
            row[self.shipping_days_index], row[self.supplier_index]

        output = {
            'url': url,
            'data': {
                'sku': sku,
                'price': '0',
                'ship_price': '0',
                'quantity': '0',
                'ship_days': '0days',
                'supplier': '{no info}',
                'variation': 'false'
            },
            'errors': []
        }

        if self.allow_triggers:
            for trigger in self.allow_triggers:
                if trigger in page:
                    output['data']['supplier'] = '{listing off}'

                    self.__add_to_report(output, price_previous, shipping_price_previous, quantity_previous)

                    return output

        if 'eBay is unavailable in your location.' in page:
            print('ban proxy by eBay')
            output['data']['supplier'] = '{ban proxy by eBay}'
            return output

        if 'Something went wrong. Please try your request again.' in page and \
                '<div class="center-panel-container vi-mast"' not in page:
            output['data']['supplier'] = '{unknown error}'
            with open('exception_page.html', 'w') as file:
                file.write(page)

            self.report['errors']['unknown_errors'] += 1
            return output

        does_not_shipping = self.__does_not_ship_to(page)
        if does_not_shipping and 'united states' not in does_not_shipping:
            with open(f'./page_errors/{sku}.html', 'w') as file:
                file.write(page)

            output['data']['supplier'] = '{proxy ban} | ' + proxy_for_check
            return output
        elif does_not_shipping and 'united states' in does_not_shipping:
            output['data']['supplier'] = '{does not ship to USA}'
            error_message = f'Нет доставки по США'
            self.file_worker.append_error_to_file_with_errors('processing', 'errors.csv', sku, error_message)

            self.__add_to_report(output, price_previous, shipping_price_previous, quantity_previous)

            return output

        if strategy == 'drop':
            another_country = self.__other_countries(page)
            if another_country:
                output['data']['supplier'] = '{not in USA}'
                output['errors'].append('supplier not in USA')
                error_message = f'Поставщик находится не в США'
                self.file_worker.append_error_to_file_with_errors('processing', 'errors.csv', sku, error_message)

                self.__add_to_report(output, price_previous, shipping_price_previous, quantity_previous)

                return output

        try:
            tree = html.fromstring(page)
        except ParserError:
            output['data']['supplier'] = '{page without content}'
            return output

        tasks = {
            "main_block_info": self.__find_in_page_by_xpath(tree, main_block),
            "catalog_div": self.__find_in_page_by_xpath(tree, parse_catalog_check),
            "select_div": self.__find_in_page_by_xpath(tree, parse_select_div),
            "title": self.__find_in_page_by_xpath(tree, parse_title_h1),
            "price_supp": self.__find_in_page_by_regular(page, parse_keys_price) if what_need_to_parse["price"] else None,
            "ship_price_supp": self.__find_in_page_by_regular(page, parse_keys_ship_price) if what_need_to_parse[
                "shipping price"] else None,
            "quantity_supp": self.__find_in_page_by_slicing(page, parse_keys_quantity) if what_need_to_parse[
                "quantity"] else None,
            "ship_date_supp": self.__find_in_page_by_slicing(page, parse_keys_ship_date) if what_need_to_parse[
                "shipping days"] else None,
            "supplier_name": self.__find_in_page_by_xpath(tree, parse_keys_supplier_name) if what_need_to_parse[
                "supplier name"] else None,
            "part_number": self.__find_in_page_by_xpath(tree, parse_keys_part_number) if what_need_to_parse[
                "part number"] else None,
            "item_weight": self.__find_in_page_by_xpath(tree, parse_keys_item_weight) if what_need_to_parse[
                "item weight"] else None,
            "dimensions": self.__find_in_page_by_xpath(tree, parse_keys_product_dimensions) if what_need_to_parse[
                "product dimensions"] else None,
            "color": self.__find_in_page_by_xpath(tree, parse_keys_color) if what_need_to_parse["color"] else None,
            "unit_count": self.__find_in_page_by_xpath(tree, parse_keys_unit_count) if what_need_to_parse[
                "unit count"] else None,
            "material_type": self.__find_in_page_by_xpath(tree, parse_keys_material_type) if what_need_to_parse[
                "material type"] else None,
            "power_source": self.__find_in_page_by_xpath(tree, parse_keys_power_source) if what_need_to_parse[
                "power source"] else None,
            "voltage": self.__find_in_page_by_xpath(tree, parse_keys_voltage) if what_need_to_parse[
                "voltage"] else None,
            "wattage": self.__find_in_page_by_xpath(tree, parse_keys_wattage) if what_need_to_parse[
                "wattage"] else None,
            "included_components": self.__find_in_page_by_xpath(tree, parse_keys_included_components) if
            what_need_to_parse[
                "included components"] else None,
            "speed": self.__find_in_page_by_xpath(tree, parse_keys_speed) if what_need_to_parse["speed"] else None,
            "number_of_boxes": self.__find_in_page_by_xpath(tree, parse_keys_number_of_boxes) if what_need_to_parse[
                "number of boxes"] else None,
            "description": self.__find_in_page_by_xpath(tree, parse_keys_description) if what_need_to_parse[
                "description"] else None
        }

        results = {}
        try:
            for key, task in tasks.items():
                if task is not None:
                    results[key] = await task
                else:
                    results[key] = None
        except Exception as e:
            print(f"Error: {e}")

        if results["catalog_div"]:
            output['data']['supplier'] = '{link on catalog}'
            output['errors'].append('link to the catalog')
            error_message = f'Ссылка на каталог товаров.'
            self.file_worker.append_error_to_file_with_errors('processing', 'errors.csv', sku, error_message)

            self.__add_to_report(output, price_previous, shipping_price_previous, quantity_previous)

            return output

        if not results["main_block_info"]:
            output['data']['supplier'] = '{no block with info}'

            self.report['errors']['no_block_with_info'] += 1
            self.__add_to_report(output, price_previous, shipping_price_previous, quantity_previous)

            dir_path = './page_errors'
            if os.path.isdir(dir_path):
                with open(f'{dir_path}/{sku}.html', 'w') as file:
                    file.write(page)
            else:
                os.makedirs(dir_path)
                with open(f'{dir_path}/{sku}.html', 'w') as file:
                    file.write(page)
            await asyncio.sleep(30)
            return output

        latin_check = self.__not_latin(results["main_block_info"][0].text_content())
        if latin_check:
            output['data']['supplier'] = '{page not on latin}'
            print('NO LATIN')
            return output

        if not results["title"]:
            output['data']['supplier'] = '{no title in link}'

            self.report['errors']['no_title_in_link'] += 1
            self.__add_to_report(output, price_previous, shipping_price_previous, quantity_previous)

            return output

        if 'Local pickup only' in results["main_block_info"][0].text_content():
            output['data']['supplier'] = '{only pickup}'
            output['errors'].append('local pickup error')
            error_message = f'У поставщика только самовывоз, нужно удалить товар.'
            self.file_worker.append_error_to_file_with_errors('processing', 'errors.csv', sku, error_message)

            self.__add_to_report(output, price_previous, shipping_price_previous,
                                 quantity_previous)

            return output

        if results["select_div"]:
            data_new = {
                'sku': sku,
                'price': price_previous,
                'ship_price': shipping_price_previous,
                'quantity': quantity_previous,
                'ship_days': shipping_days_previous,
                'supplier': supplier_name,
                'variation': 'true'
            }
            output['data'].update(data_new)

            return output

        shipping_price = 0
        if 'Varies' in results["main_block_info"][0].text_content() and results["ship_price_supp"] is None:
            results["ship_price_supp"] = 0
            results["ship_date_supp"] = '7'
        else:
            if results["ship_price_supp"]:
                shipping_price = results["ship_price_supp"].group(1)

            if results["ship_date_supp"]:
                try:
                    results["ship_date_supp"] = await self.__date_to_days(results["ship_date_supp"])
                except ValueError:
                    raise ValueError(f'Error with str {results["ship_date_supp"]} in url: {url}')
            else:
                results["ship_date_supp"] = '7'

        if 'See price on checkout' in page and results["price_supp"] is None:
            price = 0
        else:
            try:
                if results["price_supp"]:
                    price = float(results["price_supp"].group(1))
                else:
                    price = 0
            except ValueError:
                price = results["price_supp"].group(1)
            except Exception as error:
                with open('exception_page.html', 'w', encoding='utf-8') as file:
                    file.write(page)
                raise Exception(f'{error} in {url}, {results["price_supp"]}')

        if results["quantity_supp"] is None or ('This listing ended' in page):
            results["quantity_supp"] = '0'

        try:
            if results["quantity_supp"]:
                qty = int(results["quantity_supp"])
            else:
                await self.server_connect.post_error(f'На странице не было найдено кол-во. @L_trix\n'
                                                     f'{url}', shop_name)
                raise Exception(f'Qty is None in {url}')
        except Exception as error:
            with open('exception_page.html', 'w', encoding='utf-8') as file:
                file.write(page)
            raise Exception(f'{error} in {url}, {results["quantity_supp"]}')

        if results["supplier_name"]:
            supplier = results["supplier_name"][0]
        else:
            supplier = await self.__find_in_page_by_slicing(page, parse_keys_supplier_name_scalp)
            if supplier is None:
                supplier = '{supplier | None}'

        if results["title"]:
            # title logic
            pass

        if results["part_number"]:
            # logic
            pass

        if results["item_weight"]:
            # logic
            pass

        if results["dimensions"]:
            # dimensions logic
            pass

        if results["color"]:
            # color logic
            pass

        if results["unit_count"]:
            # unit logic
            pass

        if results["material_type"]:
            # material_logic
            pass

        if results["power_source"]:
            # power logic
            pass

        if results["voltage"]:
            # logic
            pass

        if results["wattage"]:
            # logic
            pass

        if results["included_components"]:
            # logic
            pass

        if results["speed"]:
            # logic
            pass

        if results["number_of_boxes"]:
            # logic
            pass

        if results["description"]:
            # logic
            pass

        data_new = {
            'sku': sku,
            'price': price,
            'ship_price': shipping_price,
            'quantity': qty,
            'ship_days': str(results["ship_date_supp"]) + 'days',
            'supplier': supplier,
            'variation': 'false'
        }
        output['data'].update(data_new)

        self.__add_to_report(output, price_previous, shipping_price_previous, quantity_previous)

        return output

    # Функция для обработки запроса на сайт
    async def __fetch(self, row, proxy_url, proxy_auth):
        try:
            sku, url, price, shipping_price, stock, shipping_days, \
                supplier_name = (row[self.sku_index],
                                 row[self.url_index].split('?')[0].replace(' ', '').replace('\n', '').replace('\t', ''),
                                 row[self.price_index], row[self.shipping_price_index], row[self.quantity_index],
                                 row[self.shipping_days_index], row[self.supplier_index])
            try:
                variation = row[self.variations_index] if row[self.variations_index] != '' else 'false'
            except IndexError:
                variation = 'false'

            if url != '' and 'ebay' in url and url != col_names['url']:  # Если ссылка пустая, не пытаемся к ней стучаться
                if url.split('/')[0] == 'ebay.com':
                    url = 'https://www.' + url

                """Проверяем находится ли SKU в исключениях или является оно вариацией,
                                если да, то возвращаем словарь с прошлыми значениями строки"""
                try:
                    if (sku != col_names['sku'] and sku in self.exceptions) or str(variation).lower() == 'true':
                        output = {
                            'url': url,
                            'data': {
                                'sku': sku,
                                'price': price,
                                'ship_price': shipping_price,
                                'quantity': stock,
                                'ship_days': shipping_days,
                                'supplier': supplier_name,
                                'variation': variation
                            },
                            'errors': []
                        }

                        return output
                except ValueError as error:
                    error_message = f'ValueError In {sku}. {error}'
                    await self.server_connect.post_error(error_message, shop_name)

                async with aiohttp.ClientSession() as session:
                    try:
                        return await self.__get_response(session, row, proxy_url, proxy_auth)
                    except asyncio.TimeoutError:
                        return self.__error_output('asyncio timeout', url, sku, variation)
                    except aiohttp.client_exceptions.ClientProxyConnectionError:  # Случай при плохом ответе прокси
                        await asyncio.sleep(45)
                        return self.__error_output('proxy error', url, sku, variation)
                    except aiohttp.client_exceptions.ClientOSError:
                        await asyncio.sleep(45)
                        return self.__error_output('ebay close connection', url, sku, variation)
                    except aiohttp.client_exceptions.ServerDisconnectedError:
                        print('connection error')
                        await asyncio.sleep(45)
                        return self.__error_output('server closed connection', url, sku, variation)
                    except ConnectionResetError:
                        print('ConnectionResetError')
                        await asyncio.sleep(45)
                        return self.__error_output('connection reset error', url, sku, variation)

            elif 'ebay' not in url and url != col_names['url'] and len(url) > 5:
                error_message = f'Ссылка ведёт не на сайт Ebay'
                self.file_worker.append_error_to_file_with_errors('processing', 'errors.csv', sku, error_message)
        except IndexError:
            return None

    def __error_output(self, message, url, sku, variation):
        output = {
            'url': url,
            'data': {
                'sku': sku,
                'price': 0,
                'ship_price': 0,
                'quantity': 0,
                'ship_days': '0days',
                'supplier': '{' + message + '}',
                'variation': variation
            },
            'errors': [message]
        }

        if message == 'proxy error':
            self.report['errors']['proxy_errors'] += 1
        if message == 'time out error':
            self.report['errors']['time_out_errors'] += 1
        if message == 'ebay close connection':
            self.report['errors']['ebay_close_connection'] += 1
        if message == 'server closed connection':
            self.report['errors']['server_close_connection'] += 1
        if message == 'error 400':
            self.report['errors']['error 400'] += 1

        return output

    async def __get_response(self, session, row, proxy_url, proxy_auth):
        url = row[self.url_index].split('?')[0]
        sku = row[self.sku_index]
        try:
            variation = row[self.variations_index]
        except IndexError:
            variation = 'false'
        price = row[self.price_index]
        shipping_price = row[self.shipping_price_index]
        qty = row[self.quantity_index]
        try:
            async with session.get(url, proxy=proxy_url,
                                   proxy_auth=proxy_auth,
                                   headers=headers) as response:  # При помощи сессии делаем запрос к ссылке
                self.report['all_processed'] += 1
                status = response.status
                response_text = await response.text()
                if status == 403:  # Если сервер закрыл доступ - выводим ошибку
                    error_message = f'Ebay was locked connection: {url}'
                    await self.server_connect.post_error(error_message, shop_name)
                    raise ConnectionError(f'Ebay was locked connection: {url}')
                elif status == 404:
                    output = {
                        'url': url,
                        'data': {
                            'sku': sku,
                            'price': 0,
                            'ship_price': 0,
                            'quantity': 0,
                            'ship_days': '0days',
                            'supplier': '{404}',
                            'variation': variation
                        },
                        'errors': []
                    }
                    self.__add_to_report(output, price, shipping_price, qty)

                    return output
                else:
                    return await self.parser_page(response_text, row, proxy_url)
        except TimeoutError:
            return self.__error_output('time out error', url, variation, sku)
        except aiohttp.client_exceptions.ClientHttpProxyError:
            return self.__error_output('proxy error', url, variation, sku)
        except aiohttp.client_exceptions.ClientPayloadError:
            print('error 400')
            await asyncio.sleep(15)
            return self.__error_output('error 400', url, variation, sku)

    async def get_req(self, threads):
        random.seed(datetime.now().timestamp())
        proxies = self.add_proxies_to_list(self.proxies, [])

        random.seed(datetime.now().timestamp())

        self.file_worker.create_file_intermediate_csv('processing', 'process.csv')
        self.file_worker.create_file_with_errors_csv('processing', 'errors.csv')
        all_res = []
        processed = 0

        batch_size_per_thread = 10  # Размер каждого пакета ссылок для одного потока
        total_batch_size = threads * batch_size_per_thread  # Общий размер пакета ссылок

        user_agents = self.file_worker.read_txt('./user_agents/user_agents.txt')

        proxies_data = []

        # # Создание списка прокси с учетом удвоенного количества потоков
        for proxy in proxies:
            proxy_url, proxy_auth = await self.__proxy_auth(proxy)
            proxies_data.append({'url': proxy_url, 'auth': proxy_auth})

        data_list = self.data  # Используем обычный список
        while data_list:  # Продолжаем, пока список не пуст
            current_batch = data_list[:total_batch_size]  # Получаем текущий общий пакет ссылок
            data_list = data_list[total_batch_size:]  # Обновляем список, удаляя обработанные элементы
            # Выполнение задач в пуле потоков
            tasks = []

            for data in current_batch:
                headers['user-agent'] = random.choice(user_agents)
                proxy = random.choice(proxies_data)
                tasks.append(self.__fetch(data, proxy['url'], proxy['auth']))

            results = await asyncio.gather(*tasks)
            all_res.extend(results)
            self.file_worker.append_to_file_intermediate(all_res, 'processing', 'process.csv')
            all_res.clear()
            processed += total_batch_size
            print(f'Processed: [{processed} | {len(self.data)}]')
            sys.stdout.flush()

        return {
            'status': 'success',
            'report': self.report
        }


class RequestToServer:
    def __init__(self):
        pass

    @staticmethod
    async def websocket_handler(data):
        async with websockets.connect('ws://' + server_host) as websocket:
            await websocket.send(json.dumps(data))
            response = json.loads(await websocket.recv())
            await websocket.close()

        return response

    async def get_proxies(self):
        data = {
            'message_type': 'get_proxy_all_isp'
        }

        return await self.websocket_handler(data)

    async def proxy_ban(self, proxies):
        data = {
            'message_type': 'bad_proxy',
            'proxies': proxies,
        }

        return await self.websocket_handler(data)

    async def send_message(self, text):
        data = {
            'message_type': 'send_custom_error',
            'shop_name': shop_name,
            'message_text': text
        }

        return await self.websocket_handler(data)

    async def reset_proxy(self, proxies):
        data = {
            'message_type': 'reset_proxy',
            'proxies': proxies
        }

        return await self.websocket_handler(data)

    async def post_error(self, error_message, shop):
        data = {
            'message_type': 'error',
            'shop_name': shop,
            'error_text': str(error_message)
        }

        return await self.websocket_handler(data)

    async def post_report(self, shop, report, average_time_by_link, time_of_code_processing, proxies):
        data = {
            'message_type': 'send_report_text',
            'shop_name': shop,
            'all_processed': report['all_processed'],
            'nones_new': report['nones_new'],
            'stock_new': report['stock_new'],
            'new_price': report['new_price'],
            'new_shipping': report['new_ship_price'],
            'errors': report['errors'],
            'bad_info_perc': round(report['errors']['proxy_errors'] / report['all_processed'], 2),
            'average_time_for_processing_link': average_time_by_link,
            'time_of_code_processing': time_of_code_processing,
            'proxies': proxies
        }

        return await self.websocket_handler(data)

    async def send_file(self, message_type, caption, file_path):
        with open(file_path, 'rb') as file:
            data = file.read()
            encoded_data = base64.b64encode(data).decode('utf-8')
            message = {
                "message_type": message_type,
                "caption": caption,
                "file_name": file_path.split('/')[-1],
                "file": encoded_data
            }

        return await self.websocket_handler(message)


# noinspection PyArgumentList
class RequestToGoogleSheets:
    def __init__(self, spreadsheet, main_worksheet, google_creds_path, columns=dict):
        creds = Credentials.from_service_account_file(google_creds_path,
                                                      scopes=['https://www.googleapis.com/auth/spreadsheets'])
        self.service = build('sheets', 'v4', credentials=creds)
        self.spreadsheet = spreadsheet
        self.main_worksheet = main_worksheet
        self.columns_names = columns
        self.indices = self.get_index_of_column()

    def get_all_info(self, worksheet):
        request = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet,
            range=worksheet,
            valueRenderOption='UNFORMATTED_VALUE'
        ).execute()

        return request['values'], self.indices

    def get_batch(self, ranges: list):
        response = self.service.spreadsheets().values().batchGet(
            spreadsheetId=self.spreadsheet,
            ranges=ranges,
            valueRenderOption='UNFORMATTED_VALUE'
        ).execute()

        return response

    def get_headers(self):
        try:
            request = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet,
                range=f'{self.main_worksheet}!1:1',
                valueRenderOption='UNFORMATTED_VALUE'
            ).execute()
        except google.auth.exceptions.TransportError:
            raise ConnectionError(f'Google server not response.')

        return request['values'][0]

    def get_index_of_column(self):
        all_columns = self.get_headers()
        indices = {}
        for header, col_name in self.columns_names.items():
            if col_name:
                index = all_columns.index(col_name)
                indices[header] = index

        return indices

    def collect_to_table_by_index(self, data):
        self.indices = self.get_index_of_column()
        actual_from_table = self.get_all_info(self.main_worksheet)[0]
        try:
            actual_sku = [row[self.indices['sku']] for row in actual_from_table]
        except IndexError:
            actual_sku = ''
        sku_from_data = [item['data']['sku'] for item in data if type(item) is dict]
        price_to_table = []
        ship_price_to_table = []
        quantity_to_table = []
        ship_days_to_table = []
        supplier_to_table = []
        variation_to_table = []

        for i, sku in enumerate(actual_sku):
            if sku in sku_from_data:
                index = sku_from_data.index(sku)
                if data[index]:
                    price_to_table.append([data[index]['data']['price']])
                    ship_price_to_table.append([data[index]['data']['ship_price']])
                    quantity_to_table.append([data[index]['data']['quantity']])
                    ship_days_to_table.append([data[index]['data']['ship_days']])
                    supplier_to_table.append([data[index]['data']['supplier']])
                    variation_to_table.append([str(data[index]['data']['variation'])])
            else:
                index = actual_sku.index(sku)

                price_to_table.append([actual_from_table[index][self.indices['price']]])
                ship_price_to_table.append([actual_from_table[index][self.indices['shipping_price']]])
                quantity_to_table.append([actual_from_table[index][self.indices['quantity']]])
                ship_days_to_table.append([actual_from_table[index][self.indices['shipping_days']]])
                supplier_to_table.append([actual_from_table[index][self.indices['supplier']]])
                try:
                    variation_to_table.append([actual_from_table[index][self.indices['variations']]])
                except IndexError:
                    variation_to_table.append(['false'])
        output = {
            'price': price_to_table,
            'ship_price': ship_price_to_table,
            'quantity': quantity_to_table,
            'ship_days': ship_days_to_table,
            'supplier': supplier_to_table,
            'variation': variation_to_table
        }
        return output

    def update_table(self, data):
        body_data = []

        if what_need_to_parse["price"] and len(data['price']) > 0:
            body_data.append({
                'range': f'{self.main_worksheet}!{gspread.utils.rowcol_to_a1(1, self.indices["price"] + 1)}:{gspread.utils.rowcol_to_a1(len(data["price"]), self.indices["price"] + 1)}',
                'values': data['price']
            })

        if what_need_to_parse["shipping price"] and len(data['ship_price']) > 0:
            body_data.append({
                'range': f'{self.main_worksheet}!{gspread.utils.rowcol_to_a1(1, self.indices["shipping_price"] + 1)}:{gspread.utils.rowcol_to_a1(len(data["ship_price"]), self.indices["shipping_price"] + 1)}',
                'values': data['ship_price']
            })

        if what_need_to_parse["quantity"] and len(data['quantity']) > 0:
            body_data.append({
                'range': f'{self.main_worksheet}!{gspread.utils.rowcol_to_a1(1, self.indices["quantity"] + 1)}:{gspread.utils.rowcol_to_a1(len(data["quantity"]), self.indices["quantity"] + 1)}',
                'values': data['quantity']
            })

        if what_need_to_parse["shipping days"] and len(data['ship_days']) > 0:
            body_data.append({
                'range': f'{self.main_worksheet}!{gspread.utils.rowcol_to_a1(1, self.indices["shipping_days"] + 1)}:{gspread.utils.rowcol_to_a1(len(data["ship_days"]), self.indices["shipping_days"] + 1)}',
                'values': data['ship_days']
            })

        if what_need_to_parse["supplier name"] and len(data['supplier']) > 0:
            body_data.append({
                'range': f'{self.main_worksheet}!{gspread.utils.rowcol_to_a1(1, self.indices["supplier"] + 1)}:{gspread.utils.rowcol_to_a1(len(data["supplier"]), self.indices["supplier"] + 1)}',
                'values': data['supplier']
            })

        if len(data['variation']) > 0:
            body_data.append({
                'range': f'{self.main_worksheet}!{gspread.utils.rowcol_to_a1(1, self.indices["variations"] + 1)}:{gspread.utils.rowcol_to_a1(len(data["variation"]), self.indices["variations"] + 1)}',
                'values': data['variation']
            })

        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': body_data
        }

        request = self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.spreadsheet,
                                                                   body=body)
        try:
            response = request.execute()
            return response
        except HttpError as error:
            raise HttpError(f'Error with write info: {error}')


class FilesWorker:
    def __init__(self):
        pass

    @staticmethod
    def read_json(file_path):
        with open(file_path, 'r') as file:
            json_data = json.load(file)

        return json_data

    @staticmethod
    def read_txt(file_path):
        with open(file_path, 'r') as file:
            txt_data = file.readlines()

        return [i.replace('\n', '').replace('\t', '') for i in txt_data]

    @staticmethod
    def create_file_for_amazon(data, indices):
        input_to_file = [["sku", "product-id", "product-id-type", "price", "item-condition",
                          "quantity", "will-ship-internationally",
                          "handling-time", "merchant_shipping_group_name", "add-delete"]]
        for row in data[1:]:
            try:
                row_price = row[indices["amazon_price"]]
                row_quantity = row[indices["quantity"]]
                try:
                    if isinstance(row_quantity, str):
                        quantity_int = int(row_quantity) if int(row_quantity) <= 5 else standard_stock
                    else:
                        quantity_int = row_quantity if row_quantity <= 5 else standard_stock
                except ValueError:
                    quantity_int = 0

                try:
                    if isinstance(row_price, str):
                        price_float = float(row_price) if float(row_price) != 0 else ''
                    else:
                        price_float = row_price if row_price != 0 else ''
                except ValueError:
                    price_float = ''
                    quantity_int = 0
            except IndexError:
                price_float = ''
                quantity_int = 0

            try:
                input_to_file.append([str(row[indices["sku"]]), str(row[indices["asin"]]), "1", str(price_float), "11",
                                      str(quantity_int), "1", str(row[indices["handling_time"]]),
                                      str(row[indices["merchant_shipping_template"]]), "a"])
            except IndexError:
                continue

        if not os.path.isdir('./uploads'):
            os.mkdir('./uploads')

        with open(f'./uploads/upload.txt', 'w') as text_file:
            for line in input_to_file:
                text_file.write('\t'.join(line) + '\n')

    @staticmethod
    def append_to_file_intermediate(data, file_path, filename):
        with open(f'./{file_path}/{filename}', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)

            for element in data:
                if element:
                    sku = element["data"]["sku"]
                    url = element["url"]
                    price = element["data"]["price"]
                    shipping_price = element["data"]["ship_price"]
                    quantity = element["data"]["quantity"]
                    shipping_days = element["data"]["ship_days"]
                    supplier = element["data"]["supplier"]
                    variation = element["data"]["variation"]
                    errors = element["errors"]

                    writer.writerow([sku, url, price, shipping_price, quantity, shipping_days,
                                     supplier, variation, errors])

    def create_file_intermediate_csv(self, file_path, file_name):
        if os.path.exists(f"./{file_path}"):
            to_file = ["sku", "url", "price", "shipping_price", "quantity", "shipping_days",
                       "supplier", "variation", "errors"]

            with open(f'./{file_path}/{file_name}', 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(to_file)
        else:
            os.makedirs(f'./{file_path}')
            self.create_file_intermediate_csv(file_path, file_name)

    def create_file_with_errors_csv(self, file_path, file_name):
        if os.path.exists(f"./{file_path}"):
            to_file = ["sku, error"]

            with open(f'./{file_path}/{file_name}', 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(to_file)
        else:
            os.makedirs(f'./{file_path}')
            self.create_file_intermediate_csv(file_path, file_name)

    @staticmethod
    def append_error_to_file_with_errors(file_path, file_name, sku, error):
        with open(f'./{file_path}/{file_name}', 'a', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([sku, error])

    @staticmethod
    def check_info_into_errors_file(file_path):
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            rows_count = 0
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                rows_count += 1
                if rows_count > 1:
                    return True

        return False

    @staticmethod
    def read_file(file_path):
        data = []
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)
            for row in csv_reader:
                sku = row[0]
                url = row[1]
                price = row[2]
                shipping_price = row[3]
                quantity = row[4]
                shipping_days = row[5]
                supplier = row[6]
                variation = row[7]
                errors = row[8]

                errors_list = [error.strip() for error in errors.strip('[]').split(',')]

                data.append({
                    'url': url,
                    'data': {
                        'sku': sku,
                        'price': price,
                        'ship_price': shipping_price,
                        'quantity': quantity,
                        'ship_days': shipping_days,
                        'supplier': supplier,
                        'variation': variation
                    },
                    'errors': errors_list
                })

        return data

    @staticmethod
    def compile_reprice_file(
            file_path: str, data: list, indices: dict, repricer_rule: str, merchant_id: str | None,
            marketplace: str | None = None, fba: str | None = None,
    ) -> str:
        if merchant_id is None:
            return 'no_reprice'

        to_csv = [['sku', 'marketplace', 'merchant_id', 'fba', 'price_min', 'price_max', 'repricer_name']]
        for row in data[1:]:
            if row[indices.get('amazon_price')] == '':
                price_from_sheet = 0
            else:
                price_from_sheet = row[indices.get('amazon_price')]
            price_min = round(float(price_from_sheet), 2)
            sku = row[indices.get('sku')]
            repricer_name = ''

            if repricer_rule == 'DP':
                if price_min > 300:
                    repricer_name = '-2.00$BRAND'
                elif price_min > 150:
                    repricer_name = '-1.00$BRAND'
                elif price_min > 100:
                    repricer_name = '-0.50$BRAND'
                elif price_min > 50:
                    repricer_name = '-0.20$BRAND'
                elif price_min > 25:
                    repricer_name = '-0.10$BRAND'
                elif price_min > 15:
                    repricer_name = '-0.05$BRAND'
                else:
                    repricer_name = '-0.01$BRAND'
            elif repricer_rule == 'BB':
                repricer_name = 'BUY BOX'
            elif repricer_rule == 'BB_brand':
                repricer_name = 'Buy Box BRAND'

            if price_min > 500:
                price_max = round(price_min * 1.15, 2)
            elif price_min > 100:
                price_max = round(price_min * 1.3, 2)
            elif price_min > 30:
                price_max = round(price_min * 1.5, 2)
            elif price_min > 10:
                price_max = round(price_min * 1.75, 2)
            elif price_min > 5:
                price_max = round(price_min * 2, 2)
            else:
                price_max = round(price_min * 3, 2)

            if marketplace is None:
                marketplace = 'AUS'

            if fba is None:
                fba = 'No'

            to_csv.append([sku, marketplace, merchant_id, fba, price_min, price_max, repricer_name])

        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(to_csv)

        return 'file_collected'


class RequestToAMZ:
    def __init__(self, amz_creds):
        self.credentials = amz_creds

    def _refresh_access_token(self, retries=5, delay=5):
        url = 'https://api.amazon.com/auth/o2   /token'
        payload = {
            'grant_type': 'refresh_token',
            'client_id': self.credentials.get('lwa_app_id'),
            'client_secret': self.credentials.get('lwa_client_secret'),
            'refresh_token': self.credentials.get('refresh_token')
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        for _ in range(retries):
            try:
                response = requests.post(url, data=payload, headers=headers)
                if response.status_code == 200:
                    tokens = response.json()
                    return tokens['access_token']
                else:
                    return None
            except (ConnectionError, TimeoutError) as e:
                print(f'Connection failed: {e}.')
                time.sleep(delay)

    def upload_to_amz(self, file_name: str) -> str | object:
        new_token = self._refresh_access_token()
        try:
            res = Feeds(credentials=self.credentials, marketplace=Marketplaces.US, restricted_data_token=new_token)
            with open(file_name, 'rb') as file:
                create_file = res.create_feed_document(file=file,
                                                       content_type='text/tab-separated-values; charset=UTF-8')

            url = create_file.payload.get('url')
            feed_document_id = create_file.payload.get('feedDocumentId')

            with open(file_name, 'rb') as file:
                requests.put(url, data=file.read())

            res.create_feed(ReportType.POST_FLAT_FILE_INVLOADER_DATA, feed_document_id)

            return 'success'
        except sp_api.base.exceptions.SellingApiForbiddenException:
            return 'no_valid_key'
        except Exception as e:
            return e


class RepricerWorker:
    def __init__(self, logs: dict | None = None):
        self.logs = logs

    def __send_file_by_logs(self, file_path: str) -> dict:
        username = self.logs.get('username')
        password = self.logs.get('password')

        repricer = Repricers(username, password)
        response = repricer.upload_report(file_path=file_path)

        return response

    def send_template(self, file_path: str) -> object | None:
        if self.logs:
            return self.__send_file_by_logs(file_path)

        print('You need specify your authorization method')
        return
