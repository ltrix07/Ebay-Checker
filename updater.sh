#!/bin/bash

# Переходим в директорию с локальным репозиторием
cd Ebay-Checker

# Получаем хэш последнего коммита на GitHub
remote_hash=$(git ls-remote https://github.com/ltrix07/Ebay-Checker.git HEAD | cut -f1)

# Получаем хэш последнего коммита в локальном репозитории
local_hash=$(git rev-parse HEAD)

# Проверяем отличается ли хэш коммита на GitHub от хэша в локальном репозитории
if [ "$remote_hash" != "$local_hash" ]; then
    echo "Требуется обновление."

    # Получаем последние изменения из репозитория GitHub
    git pull origin master

    # Перезапускаем код Python
    killall python3
    rm nohup.out
    source venv/bin/activate
    nohup python3 main.py &
else
    echo "Обновление не требуется."
fi