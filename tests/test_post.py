#!/usr/bin/python3
import datetime
import json
from time import sleep

from requests.exceptions import HTTPError
import timeit
import requests
from loguru import logger 
import datetime

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from _config_manager import ConfigManager

config_manager = ConfigManager()

logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}", level="DEBUG")

TYPE = config_manager.get_setting("Parameters","type")
SERIAL_NUMBER = config_manager.get_setting("Parameters","serial_number")

def post_request():
    try:
        payload = {
            "Eventdatetime": str(str(datetime.datetime.now())),
            "EquipmentType": TYPE,
            "SerialNumber": SERIAL_NUMBER,
            "FeedingTime": str((timeit.default_timer() + 10) - timeit.default_timer()),
            "RFIDNumber": f"TEST_{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
            "WeightLambda": 150,
            "FeedWeight": 100
        }
        return payload
    except ValueError as v:
        logger.error(f'Post_request function error: {v}')

def send_post(postData):
    url = "https://smart-farm.kz:8502/api/v2/RawFeedings"
    headers = {'Content-type': 'application/json'}
    try:
        post = requests.post(url, data = json.dumps(postData), headers = headers, timeout=30)
        logger.info(f'Status Code {post.status_code}')
        return post.status_code
    except HTTPError as http_err:
        logger.error(f'HTTP error occurred: {http_err}')
    except Exception as err:
        logger.error(f'Other error occurred: {err}')

@logger.catch
def main_test():
    try:
        post_msg = post_request()
        answer = send_post(post_msg)
        logger.info(f"Ответ от сервера: {answer}")
        if answer == 200:
            logger.info(f'Тест успешно завершен.\nПроверьте на сервере, пришло ли следующее сообщение:')
            logger.info(f'\n\n{json.dumps(post_msg, indent=4)}')
        else:
            logger.error(f'Что-то пошло не так.\nПроверьте подключение к интернету.')
        logger.info(f'Через 10 минут я закроюсь')
        sleep(600)
    except HTTPError as http_err:
        logger.error(f'HTTP error occurred: {http_err}')


main_test()