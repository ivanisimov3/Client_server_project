# Загрузка параметров .env

import os
from pathlib import Path
from dotenv import load_dotenv


def load_db_config():

    load_dotenv(Path(__file__).with_name(".env")) # Основная функция, взять значения .env из директории, где находится config.py

    return {
        "host": os.environ["DB_HOST"],
        "port": int(os.environ["DB_PORT"]),
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
    }
