import asyncio
import json
import os.path
import time
import math
import traceback
import signal
from moduls import RequestsToEbay, RequestToGoogleSheets, RequestToServer, FilesWorker, RequestToAMZ
from main_settings import google_creds_path, spreadsheet_id, main_worksheet, col_names, \
    exceptions_repricer_worksheet, exceptions_worksheet, shop_name, transient_vice_for_threads
from parser_settings import allow_triggers


lock = asyncio.Lock()
errors_for_retry = ['timeout', 'TimeoutError']


async def collect_info_from_sheet(google_sheet):
    main_data, indices = google_sheet.get_all_info(main_worksheet)
    exceptions = [row[0] for row in google_sheet.get_all_info(exceptions_worksheet)[0]]
    exceptions_repricer = [row[0] for row in google_sheet.get_all_info(exceptions_repricer_worksheet)[0]]
    return main_data, indices, exceptions, exceptions_repricer


async def cancel_all_tasks(loop=None):
    if loop is None:
        loop = asyncio.get_running_loop()

    # Получить список всех выполняемых задач
    tasks = [task for task in asyncio.all_tasks(loop) if task is not asyncio.current_task()]

    # Отменить задачи
    for task in tasks:
        task.cancel()

    # Подождать завершения отмененных задач
    await asyncio.gather(*tasks, return_exceptions=True)


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


async def read_file_of_processing(worker, server):
    all_res = worker.read_file('./processing/process.csv')
    errors = worker.check_info_into_errors_file('./processing/errors.csv')

    if errors:
        await server.send_file('send_file_processed', f'Errors {shop_name}',
                               './processing/errors.csv')

    return all_res


async def collect_proxies(server):
    response = await server.get_proxies()
    proxy_full_info = response['data']['proxies']

    return proxy_full_info


async def exception_processing(server, error_message, retries, timeout, proxies=None):
    if retries != 0:
        await server.post_error(error_message, shop_name)
        await asyncio.sleep(60 * timeout)
    else:
        if proxies:
            await server.reset_proxy(proxies)
        return 'reboot'


async def processing(server_connect, timeout_between_sheets_requests):
    amz_worker = RequestToAMZ()
    file_worker = FilesWorker()

    async with lock:
        retries = 36
        while True:
            try:
                google_sheets = RequestToGoogleSheets(
                    spreadsheet=spreadsheet_id, main_worksheet=main_worksheet,
                    google_creds_path=google_creds_path, columns=col_names
                )
                break
            except Exception as e:
                traceback.print_exc()
                error_message = f'Осталось попыток - {retries} для определения класса {RequestToGoogleSheets.__name__}.\n' \
                                f'Следующая попытка через 10 минут.\n' \
                                f'\nТип ошибки: {type(e).__name__}'
                status = await exception_processing(server_connect, error_message, retries, 10)
                retries -= 1
                if status == 'reboot':
                    error_message = f'Класс {RequestToGoogleSheets.__name__} та и не смог быть определён ' \
                                    f'по причине ошибки - {type(e).__name__}.\n' \
                                    f'\nКод перезапускается...'
                    await server_connect.post_error(error_message, shop_name)
                    await cancel_all_tasks(loop=asyncio.get_running_loop())
                    return await processing(server_connect, timeout_between_sheets_requests)

    print('Connect to Google Sheets success.')
    await asyncio.sleep(timeout_between_sheets_requests)

    print('Collect data for check...')
    async with lock:
        retries = 36
        while True:
            try:
                data_from_sheet, indices, exceptions_from_sheet, \
                    exceptions_repricer_from_sheet = await collect_info_from_sheet(google_sheet=google_sheets)
                break
            except Exception as e:
                traceback.print_exc()
                error_message = f'Осталось попыток - {retries} для вызова функции {collect_info_from_sheet.__name__}.\n' \
                                f'Следующая попытка через 10 минут.\n' \
                                f'\nТип ошибки: {type(e).__name__}'
                status = await exception_processing(server_connect, error_message, retries, 10)
                retries -= 1
                if status == 'reboot':
                    error_message = f'Функция {collect_info_from_sheet.__name__} та и не смогла успешно выполнится ' \
                                    f'по причине ошибки - {type(e).__name__}.\n' \
                                    f'\nКод перезапускается...'
                    await server_connect.post_error(error_message, shop_name)
                    await cancel_all_tasks(loop=asyncio.get_running_loop())
                    return await processing(server_connect, timeout_between_sheets_requests)
    await asyncio.sleep(timeout_between_sheets_requests)

    # Определяем кол-во потоков в зависимости от кол-ва товаров в инвентаре
    threads = thread_count(len(data_from_sheet))

    # Делаем запрос на сервер для получения прокси.
    print('Getting proxies by API...')
    proxy_full_info = await collect_proxies(server_connect)
    with open('my_proxies.json', 'w') as file:
        json.dump(proxy_full_info, file, indent=4)

    # Добавляем резервный прокси **лучше постараться реализовать при помощи запроса на сервер.
    reserve_proxy = ['angel3223221:P7oDSPbSPz@185.228.195.119:50100']

    # Реализуем класс для обработки страниц ebay.
    start_time = time.time()
    ebay_parser = RequestsToEbay(data=data_from_sheet, proxies=proxy_full_info, reserve_proxies=reserve_proxy,
                                 allow_triggers=allow_triggers, exceptions=exceptions_from_sheet,
                                 exceptions_repricer=exceptions_repricer_from_sheet,
                                 server_connect=server_connect, indices=indices)
    await asyncio.sleep(1)

    # Вызываем метод для обработки ссылок из таблицы и парсинг страниц.
    print(f'Starting check with {threads} threads...')
    report = await ebay_parser.get_req(threads)
    if report['status'] == 'reload proxy':
        to_ban_info = []
        bad_proxies = list(set(report['proxy_ids']))
        for proxy in proxy_full_info:
            if proxy['ip'] in bad_proxies:
                to_ban_info.append(proxy)
                proxy['comment'] = 'ban'

        await server_connect.reset_proxy(proxy_full_info)
        await asyncio.sleep(5)
        await server_connect.proxy_ban(to_ban_info)
        print('Proxy is bad. Code reloading after 30 sec.')
        await asyncio.sleep(30)
        await cancel_all_tasks(loop=asyncio.get_running_loop())
        return await processing(server_connect, timeout_between_sheets_requests)
    report_data = report['report']

    print('Reading result...')
    all_res = await read_file_of_processing(file_worker, server_connect)

    print('Collect to table info...')
    # Собираем данные для загрузки в таблицу и загружаем.
    async with lock:
        retries = 36
        while True:
            try:
                to_table = google_sheets.collect_to_table_by_index(all_res)
                break
            except Exception as e:
                traceback.print_exc()
                error_message = f'Осталось попыток - {retries} для вызова функции {google_sheets.collect_to_table_by_index.__name__}.\n' \
                                f'Следующая попытка через 10 минут.\n' \
                                f'\nТип ошибки: {type(e).__name__}'
                status = await exception_processing(server_connect, error_message, retries, 10, proxies=proxy_full_info)
                retries -= 1
                if status == 'reboot':
                    error_message = f'Функция {google_sheets.collect_to_table_by_index.__name__} та и не смогла успешно выполнится ' \
                                    f'по причине ошибки - {type(e).__name__}.\n' \
                                    f'\nКод перезапускается...'
                    caption = f'{shop_name} - бот не смог достучаться до таблицы, чтобы ' \
                              f'занести информацию после чека.'
                    await server_connect.post_error(error_message, shop_name)
                    await server_connect.send_file('send_file_processed', caption, './processing/process.csv')
                    await cancel_all_tasks(loop=asyncio.get_running_loop())
                    return await processing(server_connect, timeout_between_sheets_requests)
    await asyncio.sleep(timeout_between_sheets_requests)

    print('Uploading...')
    async with lock:
        retries = 36
        while True:
            try:
                google_sheets.update_table(to_table)
                break
            except Exception as e:
                traceback.print_exc()
                error_message = f'Осталось попыток - {retries} для вызова функции {google_sheets.update_table.__name__}.\n' \
                                f'Следующая попытка через 10 минут.\n' \
                                f'\nТип ошибки: {type(e).__name__}'
                status = await exception_processing(server_connect, error_message, retries, 10, proxies=proxy_full_info)
                retries -= 1
                if status == 'reboot':
                    error_message = f'Функция {google_sheets.update_table.__name__} та и не смогла успешно выполнится ' \
                                    f'по причине ошибки - {type(e).__name__}.\n' \
                                    f'\nКод перезапускается...'

                    caption = f'{shop_name} - бот не смог достучаться до таблицы, чтобы ' \
                              f'занести информацию после чека.'
                    await server_connect.send_file('send_file_processed', caption, './processing/process.csv')
                    await server_connect.post_error(error_message, shop_name)
                    await cancel_all_tasks(loop=asyncio.get_running_loop())
                    return await processing(server_connect, timeout_between_sheets_requests)
    await asyncio.sleep(timeout_between_sheets_requests)

    # Завершаем выполнение программы и отправляем отчёт.
    end_time = time.time()
    average_time_for_processing_link = average_processing_time_by_link(start_time, end_time, all_res)
    full_time_of_code_processing = end_time - start_time

    print('Collect Amazon file...')
    # Собираем обновленные данные из таблицы и создаем файл для загрузки на амз
    async with lock:
        retries = 36
        while True:
            try:
                updated_data, new_indices, exceptions_from_sheet_new, \
                    exceptions_repricer_from_sheet_new = await collect_info_from_sheet(google_sheet=google_sheets)
                break
            except Exception as e:
                traceback.print_exc()
                error_message = f'Осталось попыток - {retries} для вызова функции {collect_info_from_sheet.__name__}.\n' \
                                f'Следующая попытка через 10 минут.\n' \
                                f'\nТип ошибки: {type(e).__name__}'
                status = await exception_processing(server_connect, error_message, retries, 10, proxies=proxy_full_info)
                retries -= 1
                if status == 'reboot':
                    error_message = f'Функция {collect_info_from_sheet.__name__} та и не смогла успешно выполнится ' \
                                    f'по причине ошибки - {type(e).__name__}.\n' \
                                    f'\nКод перезапускается...'
                    message = 'Бот обновил информацию в таблице, но не смогу получить обновленную для ' \
                              'отправки на Амазон.'
                    await server_connect.send_message(message)
                    await server_connect.post_error(error_message, shop_name)
                    await cancel_all_tasks(loop=asyncio.get_running_loop())
                    return await processing(server_connect, timeout_between_sheets_requests)

    file_worker.create_file_for_amazon(updated_data, new_indices)

    print('Sending file to Amazon...')
    status_of_sending_to_amz = amz_worker.upload_to_amz('./uploads/upload.txt')
    if status_of_sending_to_amz != 'success':
        print(f'Тип ошибки - {type(status_of_sending_to_amz).__name__}. Ошибка: {status_of_sending_to_amz}')
        report_data['amz_updated'] = False
    else:
        report_data['amz_updated'] = True

    print('Sending report...')
    await server_connect.post_report(shop_name, report_data, average_time_for_processing_link,
                                     full_time_of_code_processing, proxy_full_info)

    print('Done!')


async def main():
    server = RequestToServer()
    while True:
        try:
            await processing(server, 5)
            await asyncio.sleep(60 * 60 * 6)
        finally:
            if os.path.isfile('my_proxies.json'):
                with open('my_proxies.json', 'r') as file:
                    proxies = json.load(file)

                await server.reset_proxy(proxies)


asyncio.run(main())
