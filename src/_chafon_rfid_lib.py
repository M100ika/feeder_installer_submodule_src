import time
from loguru import logger
from _config_manager import ConfigManager
import serial
from serial.tools import list_ports

from chafon_rfid.base import CommandRunner, ReaderCommand, ReaderInfoFrame, ReaderResponseFrame, ReaderType
from chafon_rfid.command import (CF_GET_READER_INFO, CF_SET_BUZZER_ENABLED, CF_SET_RF_POWER)
from chafon_rfid.response import G2_TAG_INVENTORY_STATUS_MORE_FRAMES
from chafon_rfid.transport_serial import SerialTransport
from chafon_rfid.uhfreader288m import G2InventoryCommand, G2InventoryResponseFrame
import time

class RFIDReader:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.reader_port = self.config_manager.get_setting("RFID_Reader", "reader_port")
        if self.reader_port == "Отсутствует":
            self.reader_port = None
        initial_power = int(self.config_manager.get_setting("RFID_Reader", "reader_power"))
        self.reader_power = self.closest_number(initial_power)
        self.reader_timeout = int(self.config_manager.get_setting("RFID_Reader", "reader_timeout"))
        self.reader_buzzer = int(self.config_manager.get_setting("RFID_Reader", "reader_buzzer"))
        self.transport = None
        self.runner = None
        self._inventory_cmd = None
        self._frame_type = None


    def closest_number(self, power):
        numbers = [1, 3, 5, 7, 10, 15, 20, 26]
        if power < min(numbers):
            return min(numbers)
        return min(numbers, key=lambda x: abs(x - power))


    def find_rfid_reader(self):
        ports = list(list_ports.comports())
        for port in ports:
            try:
                transport = SerialTransport(device=port.device)
                runner = CommandRunner(transport)
                get_reader_info_cmd = ReaderCommand(CF_GET_READER_INFO)
                
                response = runner.run(get_reader_info_cmd)
                reader_info = ReaderInfoFrame(response)
                
                if reader_info.type:  
                    self.config_manager.update_setting("RFID_Reader", "reader_port", port.device)
                    return port.device
                    
            except (OSError, serial.SerialException, ValueError):
                pass
        
        self.config_manager.update_setting("RFID_Reader", "reader_port", "Отсутствует")
        return None


    def _get_reader_type(self):
        get_reader_info = ReaderCommand(CF_GET_READER_INFO)
        self.transport = SerialTransport(device=self.reader_port)
        self.runner = CommandRunner(self.transport)
        reader_info = ReaderInfoFrame(self.runner.run(get_reader_info))
        return reader_info.type

    def _run_command(self, command):
        self.transport.write(command.serialize())
        status = ReaderResponseFrame(self.transport.read_frame()).result_status
        return status

    def _set_power(self):
        return self._run_command(ReaderCommand(CF_SET_RF_POWER, data=[self.reader_power]))

    def _set_buzzer_enabled(self):
        return self._run_command(ReaderCommand(CF_SET_BUZZER_ENABLED, data=[self.reader_buzzer and 1 or 0]))

    def open(self):
        """
        Отдельная инициализация соединения. Вызывать один раз,
        далее использовать read_tag() для чтения.
        """
        if self.transport:
            return True

        if self.reader_port == "Отсутствует":
            self.reader_port = None

        if not self.reader_port:
            found = self.find_rfid_reader()
            if not found:
                logger.error("RFID reader port not found.")
                return False
            self.reader_port = found

        try:
            reader_type = self._get_reader_type()
            if reader_type not in (ReaderType.UHFReader86, ReaderType.UHFReader86_1):
                logger.error(f'Unsupported reader type: {reader_type}')
                return False

            # _get_reader_type уже создал transport/runner
            self._inventory_cmd = G2InventoryCommand(q_value=4, antenna=0x80)
            self._frame_type = G2InventoryResponseFrame
            self._set_power()
            self._set_buzzer_enabled()
            logger.info(f"RFID reader initialized on {self.reader_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to open RFID reader: {e}")
            self.close()
            return False

    def read_tag(self):
        """
        Читает одну метку, используя уже инициализированное соединение.
        Возвращает EPC без CRC или None по таймауту.
        """
        if not self.transport:
            opened = self.open()
            if not opened:
                return None

        tag_id = None
        start_time = time.time()

        while tag_id is None:
            if time.time() - start_time > self.reader_timeout:
                logger.info("RFID read timeout reached.")
                break
            try:
                self.transport.write(self._inventory_cmd.serialize())
                inventory_status = None
                while inventory_status is None or inventory_status == G2_TAG_INVENTORY_STATUS_MORE_FRAMES:
                    resp = self._frame_type(self.transport.read_frame())
                    inventory_status = resp.result_status
                    tags_generator = resp.get_tag()
                    try:
                        first_tag = next(tags_generator, None)
                        if first_tag:
                            tag_id = first_tag.epc.hex()
                            break
                    except StopIteration:
                        continue
            except KeyboardInterrupt:
                logger.error("Operation cancelled by user.")
                break
            except Exception as e:
                logger.error(f'Error while reading RFID: {e}')
                time.sleep(0.05)
                continue

        return tag_id[14:23] if tag_id else None

    def close(self):
        try:
            if self.transport:
                self.transport.close()
                logger.info("RFID reader connection closed.")
        finally:
            self.transport = None
            self.runner = None
            self._inventory_cmd = None
            self._frame_type = None

    def connect(self):
        """
        Старый интерфейс: инициализация + однократное чтение метки.
        Оставлен для обратной совместимости.
        """
        if not self.open():
            return None
        tag = self.read_tag()
        return tag
        
