from main_settings import server_host, shop_name, chat_ids
from moduls import RequestToServer
import asyncio

server_connect = RequestToServer(server_host)


async def test_post():
    print(await server_connect.post_error('error', f'Error on {shop_name} Test', chat_id_for_errors))


asyncio.run(test_post())