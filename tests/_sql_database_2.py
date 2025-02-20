import sqlite3
import os
from loguru import logger
import requests
import json
#from _config_manager import ConfigManager

class SqlDatabase:
    def __init__(self, db_path='sql_table.db', init_table=True, connection=None):
        self.__url = "https://smart-farm.kz:8502/api/v2/RawFeedings"
        self.__headers = {'Content-type': 'application/json'}
        self.__sql_table_path = db_path
        self.__connection = connection

        if init_table:
            self.__table_check()

    def __get_connection(self):
        """Использует открытое соединение или создает новое"""
        if self.__connection:
            return self.__connection
        return sqlite3.connect(self.__sql_table_path)

    def no_internet(self, payload):
        if payload:
            self.__insert_data(payload)
        else:
            logger.error('SqlDatabase no_internet: Empty payload')

    def internet_on(self):
        try:
            with self.__get_connection() as db:
                sql = db.cursor()
                count = sql.execute("SELECT COUNT(*) FROM json_data").fetchone()[0]
                if count > 0:
                    self.__send_saved_data()
        except Exception as e:
            logger.error(f'SqlDatabase internet_on: {e}')

    def __table_check(self):
        try:
            with self.__get_connection() as db:
                sql = db.cursor()
                sql.execute("""CREATE TABLE IF NOT EXISTS json_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Eventdatetime TEXT,
                    EquipmentType TEXT,
                    SerialNumber TEXT,
                    FeedingTime REAL,
                    RFIDNumber TEXT,
                    WeightLambda REAL,
                    FeedWeight REAL)""")
                db.commit()
        except Exception as e:
            logger.error(f'SqlDatabase __table_check: {e}')

    def __insert_data(self, payload):
        try:
            with self.__get_connection() as db:
                sql = db.cursor()
                values = self.__table_values_convert(payload)
                sql.execute("INSERT INTO json_data (Eventdatetime, EquipmentType, SerialNumber, FeedingTime, RFIDNumber, WeightLambda, FeedWeight) VALUES (?,?,?,?,?,?,?);", values)
                db.commit()
        except Exception as e:
            logger.error(f'SqlDatabase __insert_data: {e}')

    def __table_values_convert(self, payload):
        return (payload['Eventdatetime'], payload["EquipmentType"], payload["SerialNumber"],
                payload["FeedingTime"], payload["RFIDNumber"], payload["WeightLambda"], payload["FeedWeight"])

    def __db_row_to_json(self, db_row):
        return {
            "Eventdatetime": db_row[1],
            "EquipmentType": db_row[2],
            "SerialNumber": db_row[3],
            "FeedingTime": db_row[4],
            "RFIDNumber": db_row[5],
            "WeightLambda": db_row[6],
            "FeedWeight": db_row[7]
        }

    def __take_all_data(self):
        try:
            with self.__get_connection() as db:
                sql = db.cursor()
                sql.execute("SELECT * FROM json_data")
                return sql.fetchall()
        except Exception as e:
            logger.error(f'SqlDatabase __take_all_data: {e}')
            return []

    def __delete_saved_data(self, id):
        try:
            with self.__get_connection() as db:
                sql = db.cursor()
                sql.execute("DELETE from json_data WHERE id = ?", (id,))
                db.commit()
        except Exception as e:
            logger.error(f'SqlDatabase __delete_saved_data: {e}')

    def __send_saved_data(self):
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
