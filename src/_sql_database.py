import sqlite3
import os
from loguru import logger
import requests
import json
from _config_manager import ConfigManager


class SqlDatabase:
    def __init__(self, db_path='sql_table.db'):
        self.config_manager = ConfigManager()
        self.__url = self.config_manager.get_setting("Parameters", "url")
        self.__headers = {'Content-type': 'application/json'}
        self.__sql_table_path = db_path

        # Проверка и создание таблицы, если не существует
        self.__table_check()

    def no_internet(self, payload):
        """Сохранить данные, если нет интернета."""
        if payload:
            self.__insert_data(payload)
        else:
            logger.error('SqlDatabase no_internet: Empty payload')

    def internet_on(self):
        """Проверить интернет и попытаться отправить сохраненные данные."""
        try:
            # Проверка наличия интернета перед отправкой
            requests.get("https://www.google.com", timeout=5)

            # Если интернет есть, пробуем отправить все накопленные данные
            self.__send_saved_data()
        except requests.RequestException:
            logger.warning('Internet is not available. Data will remain in the database.')

    def __table_check(self):
        """Создать таблицу, если не существует"""
        try:
            with sqlite3.connect(self.__sql_table_path) as db:
                sql = db.cursor()
                sql.execute("""CREATE TABLE IF NOT EXISTS json_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Eventdatetime TEXT,
                    EquipmentType TEXT,
                    SerialNumber TEXT,
                    FeedingTime REAL,
                    RFIDNumber TEXT,
                    WeightLambda REAL,
                    FeedWeight REAL
                )""")
                db.commit()
        except Exception as e:
            logger.error(f'SqlDatabase __table_check: {e}')

    def __insert_data(self, payload):
        """Сохранить данные в базу"""
        try:
            with sqlite3.connect(self.__sql_table_path) as db:
                sql = db.cursor()
                values = self.__table_values_convert(payload)
                sql.execute(
                    """INSERT INTO json_data 
                       (Eventdatetime, EquipmentType, SerialNumber, FeedingTime, RFIDNumber, WeightLambda, FeedWeight) 
                       VALUES (?, ?, ?, ?, ?, ?, ?);""",
                    values
                )
                db.commit()
                logger.info(f"Data saved locally: {values}")
        except Exception as e:
            logger.error(f'SqlDatabase __insert_data: {e}')

    def __table_values_convert(self, payload):
        return (payload['Eventdatetime'], payload["EquipmentType"], payload["SerialNumber"],
                payload["FeedingTime"], payload["RFIDNumber"], payload["WeightLambda"], payload["FeedWeight"])

    def __db_row_to_json(self, db_row):
        return {
            "Eventdatetime": db_row[1],
            "EquipmentType": db_row[2],
            "SerialNumber": "s" + db_row[3],
            "FeedingTime": db_row[4],
            "RFIDNumber": db_row[5],
            "WeightLambda": db_row[6],
            "FeedWeight": db_row[7]
        }

    def __take_all_data(self):
        try:
            with sqlite3.connect(self.__sql_table_path) as db:
                sql = db.cursor()
                sql.execute("SELECT * FROM json_data")
                return sql.fetchall()
        except Exception as e:
            logger.error(f'SqlDatabase __take_all_data: {e}')
            return []

    def __delete_saved_data(self, id):
        try:
            with sqlite3.connect(self.__sql_table_path) as db:
                sql = db.cursor()
                sql.execute("DELETE FROM json_data WHERE id = ?", (id,))
                db.commit()
        except Exception as e:
            logger.error(f'SqlDatabase __delete_saved_data: {e}')

    def __send_saved_data(self):
        """Отправить все сохранённые данные"""
        try:
            all_data = self.__take_all_data()
            for row in all_data:
                id = row[0]
                post_data = self.__db_row_to_json(row)
                response = requests.post(self.__url, data=json.dumps(post_data), headers=self.__headers, timeout=5)
                if response.status_code == 200:
                    self.__delete_saved_data(id)
                    logger.info(f'Successfully sent data from DB. ID: {id}')
                else:
                    logger.warning(f'Failed to send data from DB. ID: {id}. Status code: {response.status_code}')
        except Exception as e:
            logger.error(f'SqlDatabase __send_saved_data: {e}')
