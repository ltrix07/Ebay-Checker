import paramiko
import time

# Функция для подключения к серверу, передачи файлов и выполнения команд
def execute_commands(hostname, password, username, local_files, remote_dir, commands):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=hostname, username=username, password=password)

    # Передача файлов на удаленный сервер
    sftp = client.open_sftp()
    for local_file in local_files:
        remote_file = f"{remote_dir}/{local_file.split('/')[-1]}"
        sftp.put(local_file, remote_file)
    sftp.close()

    print(f"Files uploaded to {hostname}")

    # # Выполнение команд на удаленном сервере с использованием nohup и &
    # stdin, stdout, stderr = client.exec_command(f'rm output.log')
    # time.sleep(1)
    #
    # stdin, stdout, stderr = client.exec_command(f'killall python3')
    # time.sleep(1)
    #
    # stdin, stdout, stderr = client.exec_command(f'source venv/bin/activate')
    # time.sleep(1)
    #
    # for command in commands:
    #     stdin, stdout, stderr = client.exec_command(f'nohup {command} > output.log 2>&1 &')
    #     print(f"Command {command} executed on {hostname}.")

    client.close()

common_params = {
    'username': 'root',
    'password': 'Amazon!23',
    'local_files': ['./moduls.py', './main.py', './parser_settings.py'],
    'remote_dir': '/root',
    'commands': ['python3 main.py']
}

servers = [
    {'hostname': '185.231.70.170'},  # Angel
    {'hostname': '185.224.135.197'},  # Cartier
    {'hostname': '185.224.133.137'},  # Donald
    {'hostname': '185.231.70.194'},  # Martin
    {'hostname': '185.231.70.224'},  # Tatiana
    {'hostname': '185.231.70.223'},  # Belarus
    {'hostname': '185.231.70.214'},  # Suslik
    {'hostname': '185.231.70.213'},  # Lion
    {'hostname': '185.231.70.212'},  # Lopuh
    {'hostname': '185.231.70.211'},  # Koloda
    {'hostname': '185.231.70.209'},  # Sumoist
    {'hostname': '185.231.70.220'},  # Tom
    {'hostname': '185.231.70.219'},  # Bond
    {'hostname': '185.231.70.218'},  # Neptun
    {'hostname': '185.231.70.216'},  # Jabka
    # {'hostname': '185.219.82.239'},  # Artemus
    # {'hostname': '185.224.133.102'},  # Avatar
    # {'hostname': '185.224.134.24'},  # Baza
    # {'hostname': '185.224.134.29'},  # Bear
    # {'hostname': '185.224.134.34'},  # Butyrka
    # {'hostname': '185.224.134.41'},  # Evgenia
    # {'hostname': '185.224.134.46'},  # Jackpot
    # {'hostname': '185.224.134.55'},  # Karpaty
    # {'hostname': '185.224.134.59'},  # Lambo
    # {'hostname': '185.224.134.75'},  # Lera
    # {'hostname': '185.224.134.82'},  # Miron
    # {'hostname': '185.224.134.93'},  # Muscat
    # {'hostname': '185.224.134.102'},  # Sava
    # {'hostname': '185.224.134.105'},  # Sheva 1
    # {'hostname': '185.224.134.106'},  # Sheva 2
]

for server in servers:
    execute_commands(server['hostname'], **common_params)
