import unittest
from unittest.mock import patch
import sqlite3
from _sql_database_2 import SqlDatabase


class TestSqlDatabase(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(':memory:')
        self.db = SqlDatabase(connection=self.connection, init_table=True)

    def tearDown(self):
        self.connection.close()

    def test_table_creation(self):
        # Просто проверка, что нет ошибок
        self.db._SqlDatabase__table_check()

    def test_insert_data(self):
        payload = {
            'Eventdatetime': '2025-02-21T10:00:00',
            'EquipmentType': 'Feeder',
            'SerialNumber': 'SN123456',
            'FeedingTime': 12.5,
            'RFIDNumber': 'RFID1234',
            'WeightLambda': 45.7,
            'FeedWeight': 33.3
        }

        self.db._SqlDatabase__insert_data(payload)

        result = self.db._SqlDatabase__take_all_data()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][3], 'SN123456')

    def test_take_all_data(self):
        payload = {
            'Eventdatetime': '2025-02-21T10:00:00',
            'EquipmentType': 'Feeder',
            'SerialNumber': 'SN7890',
            'FeedingTime': 15.0,
            'RFIDNumber': 'RFID9999',
            'WeightLambda': 55.7,
            'FeedWeight': 40.3
        }
        self.db._SqlDatabase__insert_data(payload)

        result = self.db._SqlDatabase__take_all_data()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][3], 'SN7890')

    @patch('requests.post')
    def test_send_saved_data(self, mock_post):
        payload = {
            'Eventdatetime': '2025-02-21T10:00:00',
            'EquipmentType': 'Feeder',
            'SerialNumber': 'SN654321',
            'FeedingTime': 9.5,
            'RFIDNumber': 'RFID7777',
            'WeightLambda': 22.2,
            'FeedWeight': 11.1
        }
        self.db._SqlDatabase__insert_data(payload)

        mock_post.return_value.status_code = 200

        self.db._SqlDatabase__send_saved_data()

        mock_post.assert_called()

        result = self.db._SqlDatabase__take_all_data()
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()
