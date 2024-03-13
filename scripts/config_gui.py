import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path
import serial
from serial.tools import list_ports
import subprocess
import time
from tkinter import simpledialog
from functools import partial
import datetime

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from _config_manager import ConfigManager 
from _chafon_rfid_lib import RFIDReader


class ConfigGUI:
    def __init__(self, root):
        self.root = root
        self.stop_service('feeder.service')
        self.root.title("Конфигуратор оборудования")
        self.arduino_find_button = None
        self.rfid_find_button = None
        self.config_manager = ConfigManager("../config/config.ini")
        self.create_style() 
        self.user_level = tk.StringVar(value="user")
        self.draw_gui()
        self.disable_editing()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)


    def create_style(self):
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Arial', 11), padding=5)
        self.style.configure('TCheckbutton', font=('Arial', 10), padding=5)
        self.style.configure('TButton', font=('Arial', 10, 'bold'), padding=5)
        self.style.configure('TEntry', font=('Arial', 10), padding=5)
        self.style.configure('TLabelframe', font=('Arial', 12, 'bold'), padding=10)
        self.style.configure('TLabelframe.Label', font=('Arial', 12, 'bold'), padding=5)
        self.style.theme_use('default')


    def on_closing(self):
        self.start_service('feeder.service')
        self.root.destroy()


    def run_in_terminal(self):
        script_path = Path(__file__).parent.parent / 'src' / 'main_feeder.py'
        cmd = f'xterm -geometry 155x30 -bg black -fg white -fa \'Monospace\' -fs 12 -title "Feeder test terminal" -e python3 {script_path}'
        subprocess.run(cmd, shell=True, check=True)


    def draw_tests_tab(self):
        self.tests_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tests_frame, text='Тесты')
        test_files = [
            ("relay_test.py", "Тест реле"),
            ("rfid_ethernet_test.py", "Тест RFID по Ethernet"),
            ("rfid_usb_test_2.py", "Тест RFID по USB"),
            ("test_post.py", "Тестирование отправки данных на сервер"),
            ("weight_measure_test.py", "Тест весов")
        ]

        for test_file, name in test_files:
            relay_test_button = ttk.Button(self.tests_frame, text=name, command=partial(self.run_test, test_file, name))
            relay_test_button.pack(pady=5)


    def run_test(self, test_file, name):
        test_script_path = Path(__file__).parent.parent / 'tests' / test_file
        self.run_in_new_terminal(name, f'python3 {test_script_path}')


    def run_in_new_terminal(self, name, command):
        cmd = f'xterm -geometry 155x30 -bg black -fg white -fa \'Monospace\' -fs 12 -title "{name}" -e \'{command}\''
        subprocess.run(cmd, shell=True, check=True)
    

    def save_changes(self):
        for section, entries in self.entries.items():
            for setting, info in entries.items():
                var = info['var']
                if isinstance(var, tk.IntVar) or isinstance(var, tk.StringVar):
                    value = var.get()  
                else:
                    continue 
                    
                self.config_manager.update_setting(section, setting, str(value))
        messagebox.showinfo("Сохранение", "Настройки сохранены успешно!")
        if self.user_level.get() == "admin":
            try:
                self.run_in_terminal()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось запустить скрипт: {e}")

        # sudo_password = simpledialog.askstring("Пароль sudo", "Введите пароль sudo:", show='*')
        # if sudo_password is not None:
        #     try:
        #        
        #         command = 'echo {} | sudo -S systemctl restart feeder.service'.format(sudo_password)
        #         process = subprocess.run(command, shell=True, check=True, text=True, input=sudo_password, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #         messagebox.showinfo("Перезапуск сервиса", "Сервис успешно перезапущен!")
        #     except subprocess.CalledProcessError as e:
        #         messagebox.showerror("Ошибка", f"Не удалось перезапустить сервис: {e.stderr}")
        # else:
        #     messagebox.showinfo("Отмена", "Операция отменена пользователем.")

        # try:
        #     # subprocess.run(['sudo', 'systemctl', 'restart', 'feeder.service'], check=True)
        #     messagebox.showinfo("Перезапуск сервиса", "Сервис успешно перезапущен!")
        # except subprocess.CalledProcessError as e:
        #     messagebox.showerror("Ошибка", f"Не удалось перезапустить сервис: {e}")
            # /etc/sudoers
            # yourusername ALL=(ALL) NOPASSWD: /bin/systemctl restart feeder.service


    def service_exists(self, service_name):
        try:
            subprocess.check_call(['systemctl', 'status', service_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def stop_service(self, service_name):
        if self.service_exists(service_name):
            subprocess.run(['sudo', 'systemctl', 'stop', service_name], check=True)

    def start_service(self, service_name):
        if self.service_exists(service_name):
            subprocess.run(['sudo', 'systemctl', 'start', service_name], check=True)

    def find_arduino(self):
        ports = list(list_ports.comports())
        for port in ports:
            try:
                s = serial.Serial(port.device, 9600, timeout=1)
                time.sleep(2)
                s.write(b'\x01')
                time.sleep(1)
                response = s.readline().decode().strip()
                s.close()
                if response == "Arduino!":
                    self.config_manager.update_setting("Parameters", "arduino_port", port.device)
                    messagebox.showinfo("Поиск Arduino", f"Arduino найден на порту: {port.device}")
                    return
            except (OSError, serial.SerialException) as e:
                messagebox.showwarning("Ошибка поиска Arduino: ", e)
        self.config_manager.update_setting("Parameters", "arduino_port", "Отсутствует")
        messagebox.showwarning("Поиск Arduino", "Arduino не найден.")
        
        
    def search_rfid_reader(self):
        rfid_usb = RFIDReader()
        rfid_usb_port = rfid_usb.find_rfid_reader()
        if rfid_usb_port:
            messagebox.showinfo("Поиск RFID-ридера", f"RFID-ридер найден на порту: {rfid_usb_port}")
        else:
            messagebox.showwarning("Поиск RFID-ридера", "RFID-ридер не найден.")


    def draw_gui(self):
        self.notebook = ttk.Notebook(self.root)
        self.user_frame = ttk.Frame(self.notebook)
        self.mainframe = ttk.Frame(self.notebook)
        self.notebook.add(self.user_frame, text='Пользователь')
        self.notebook.add(self.mainframe, text='Настройки')
        self.notebook.pack(expand=True, fill='both')

        self.draw_settings_tab()
        self.draw_user_tab()
        self.draw_tests_tab()


    def draw_settings_tab(self):
        self.entries = {}
        config = self.config_manager.get_config()

        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(0, weight=1)

        exclude_list = [
            ('Parameters', 'url'),
            ('Parameters', 'median_url'),
            ('Parameters', 'array_url'),  
            ('DbId', 'id'),
            ('DbId', 'version'),
        ]

        checkbox_options = {
            ('Parameters', 'debug'): 'Debug',
            ('Parameters', 'database'): 'Database',
            ('RFID_Reader', 'reader_buzzer'): 'Reader Buzzer',
            ('RFID_Reader', 'reader_usb'): 'Reader USB',
            ('Calibration', 'calibration_mode'): 'Calibration Mode'            
        }

        readonly_options = {
            ('Calibration', 'offset'),
            ('Calibration', 'scale'),
        }
        row_number = 0 
        self.arduino_find_button = ttk.Button(self.mainframe, text="Найти Arduino", command=self.find_arduino)
        self.arduino_find_button.grid(row=row_number, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        row_number += 1

        self.rfid_find_button = ttk.Button(self.mainframe, text="Найти RFID-ридер", command=self.search_rfid_reader)
        self.rfid_find_button.grid(row=row_number, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        row_number += 1

        # Изначально делаем кнопки недоступными
        self.arduino_find_button.config(state='disabled')
        self.rfid_find_button.config(state='disabled')
        for section in config.sections():
            self.entries[section] = {}

            section_frame = ttk.LabelFrame(self.mainframe, text=section) 
            section_frame.grid(column=0, row=row_number, sticky=(tk.W, tk.E), padx=5, pady=5)
            section_frame.columnconfigure(1, weight=1)

            section_row_number = 0
            for option in config[section]:
                if (section, option) in exclude_list:
                    continue

                row = ttk.Frame(section_frame)
                row.grid(row=section_row_number, column=0, columnspan=2, sticky=(tk.E, tk.E), padx=5, pady=2)

                label = ttk.Label(row, text=option)
                label.grid(row=0, column=0, sticky=tk.W)

                if (section, option) in checkbox_options.keys():
                    var = tk.IntVar(value=int(config.get(section, option)))
                    cb = ttk.Checkbutton(row, variable=var, onvalue=1, offvalue=0)
                    cb.grid(row=0, column=1, sticky=tk.W)
                    self.entries[section][option] = {'var': var, 'widget': cb}
                else:
                    entry_var = tk.StringVar(value=config.get(section, option))
                    entry = ttk.Entry(row, textvariable=entry_var)
                    if (section, option) in readonly_options:
                        entry.config(state='readonly')
                    entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
                    self.entries[section][option] = {'var': entry_var, 'widget': entry}

                section_row_number += 1

            row_number += 1

        save_button = ttk.Button(self.mainframe, text="Сохранить изменения", command=self.save_changes)  
        save_button.grid(row=row_number, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)


    def draw_user_tab(self):
        ttk.Label(self.user_frame, text="Выберите ваш уровень доступа:").pack(pady=10)
        ttk.Radiobutton(self.user_frame, text="Обычный пользователь", variable=self.user_level, value="user", command=self.update_access_level).pack(anchor=tk.W)
        ttk.Radiobutton(self.user_frame, text="Технический специалист", variable=self.user_level, value="admin", command=self.update_access_level).pack(anchor=tk.W)


    def update_access_level(self):
        if self.user_level.get() == "admin":
            entered_password = simpledialog.askstring("Пароль", "Введите пароль технического специалиста:", show='*')
            if entered_password is not None and self.check_password(entered_password):
                self.enable_editing()
            else:
                messagebox.showwarning("Ошибка", "Неверный пароль!")
                self.user_level.set("user")
        else:
            self.disable_editing()


    def enable_editing(self):
        for section, options in self.entries.items():
            for option, info in options.items():
                widget = info['widget']
                if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Checkbutton):
                    widget.config(state='normal')

        if self.arduino_find_button and self.rfid_find_button:
            self.arduino_find_button.config(state='normal')
            self.rfid_find_button.config(state='normal')


    def disable_editing(self):
        for section, options in self.entries.items():
            for option, info in options.items():
                widget = info['widget']
                if isinstance(widget, ttk.Entry):
                    widget.config(state='readonly')
                elif isinstance(widget, ttk.Checkbutton):
                    widget.config(state='disabled')
        if self.arduino_find_button and self.rfid_find_button:
            self.arduino_find_button.config(state='disabled')
            self.rfid_find_button.config(state='disabled')


    def check_password(self, entered_password):
        correct_password = datetime.datetime.now().strftime('%d')
        return entered_password == correct_password


def main():
    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()