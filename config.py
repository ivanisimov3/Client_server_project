# Загрузка параметров .env

import os
from pathlib import Path
from dotenv import load_dotenv


def load_db_config():

    load_dotenv(Path(__file__).with_name(".env")) # Основная функция, взять значения .env из директории, где находится config.py

    required = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise ValueError(f"Не заданы параметры подключения: {', '.join(missing)}")

    return {
        "host": os.environ["DB_HOST"],
        "port": int(os.environ["DB_PORT"]),
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
    }
