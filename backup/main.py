import asyncio
from moduls import RequestsToEbay, RequestToGoogleSheets, RequestToServer, FilesWorker
from settings import google_creds_path, spreadsheet_id, main_worksheet, allow_triggers, col_names, \
    exceptions_repricer_worksheet, exceptions_worksheet, shop_name, transient_vice_for_threads
import time
import socket
import math

lock = asyncio.Lock()


def collect_info_from_sheet(google_sheet):
    main_data, indices = google_sheet.get_all_info(main_worksheet)
    exceptions = [row[0] for row in google_sheet.get_all_info(exceptions_worksheet)[0]]
    exceptions_repricer = [row[0] for row in google_sheet.get_all_info(exceptions_repricer_worksheet)[0]]
    return main_data, indices, exceptions, exceptions_repricer


def add_proxies_to_list(proxies_list_from_supplier, proxies_list_for_app):
    for proxy_info in proxies_list_from_supplier:
        login = proxy_info['login']
        password = proxy_info['password']
        ip = proxy_info['ip']
        port = proxy_info['port_http']
        proxy = f'{login}:{password}@{ip}:{port}'
        proxies_list_for_app.append(proxy)


def average_processing_time_by_link(start_time, end_time, processed_data):
    processing_time = end_time - start_time
    average_time = processing_time / len(processed_data)

    return average_time


def thread_count(all_data_from_sheet_length):
    if all_data_from_sheet_length >= transient_vice_for_threads:
        threads = math.ceil(all_data_from_sheet_length / transient_vice_for_threads)
    else:
        threads = 1

    return threads


async def main():
    # Обозначаем классы для работы с сервером и гугл таблицами.
    file_worker = FilesWorker()
    server_connect = RequestToServer()
    google_sheets = RequestToGoogleSheets(spreadsheet=spreadsheet_id, main_worksheet=main_worksheet,
                                          google_creds_path=google_creds_path, columns=col_names)
    proxies = []
    try:
        async with lock:
            # Получаем информацию из таблицы.
            data_from_sheet, indices, exceptions_from_sheet, \
                exceptions_repricer_from_sheet = collect_info_from_sheet(google_sheets)

            # Определяем кол-во потоков в зависимости от кол-ва товаров в инвентаре
            threads = thread_count(len(data_from_sheet))

            # Делаем запрос на сервер для получения прокси.
            response = await server_connect.get_proxies(threads)
            proxy_full_info = response['data']['proxies']

            add_proxies_to_list(proxy_full_info, proxies)

            # Добавляем резервный прокси **лучше постараться реализовать при помощи запроса на сервер.
            reserve_proxy = ['angel3223221:P7oDSPbSPz@185.228.195.119:50100']

            # Реализуем класс для обработки страниц ебей.
            start_time = time.time()
            ebay_parser = RequestsToEbay(data=data_from_sheet, proxies=proxies, reserve_proxies=reserve_proxy,
                                         allow_triggers=allow_triggers, exceptions=exceptions_from_sheet,
                                         exceptions_repricer=exceptions_repricer_from_sheet,
                                         server_connect=server_connect, indices=indices)

            # Вызываем метод для обработки ссылок из таблицы и парсинг страниц.
            report = await ebay_parser.get_req(threads)
            all_res = await file_worker.read_file('./processing/process.csv')
            errors = await file_worker.check_info_into_errors_file('./processing/errors.csv')

            if errors:
                await server_connect.send_file('send_file_processed', f'Errors {shop_name}',
                                               './processing/errors.csv')

            # Собираем данные для загрузки в таблицу и загружаем.
            to_table = google_sheets.collect_to_table_by_index(all_res)
            try:
                google_sheets.update_table(to_table)
            except Exception as e:
                print(e)
                await server_connect.send_file('send_file_processed', shop_name,
                                               './processing/process.csv')

            # Завершаем выполнение программы и отправляем отчёт.
            end_time = time.time()
            average_time_for_processing_link = average_processing_time_by_link(start_time, end_time, all_res)
            full_time_of_code_processing = end_time - start_time

            await server_connect.post_report(shop_name, report, average_time_for_processing_link,
                                             full_time_of_code_processing, proxy_full_info)

    except socket.timeout as error:
        await server_connect.post_error(error, shop_name)
        await server_connect.reset_proxy(proxy_full_info)
    except Exception as error:
        response1 = await server_connect.post_error(error, shop_name)
        response2 = await server_connect.reset_proxy(proxy_full_info)
        if response1['errors']:
            print(response1)
        if response2['errors']:
            print(response2)


asyncio.run(main())
