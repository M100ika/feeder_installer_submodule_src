# Сабмодуль проекта: Feeder
**Версия**: 7.1  
**Автор**: Суйеубаев Максат Жамбылович

**Email**: maxat.suieubayev@gmail.com  
**GitHub URL проекта**: https://github.com/M100ika/feeder_installer_submodule_src.git

## Пояснение 
Сабмодуль — это отдельный компонент проекта, который может быть размещён в собственном репозитории и подключен к основному проекту как зависимость. Это позволяет обновлять, управлять версиями и разрабатывать компоненты проекта независимо друг от друга. Для работы с сабмодулем, его нужно клонировать вместе с основным проектом (или подтянуть изменения, если он уже склонирован), используя команды git, предназначенные для работы с сабмодулями, например git submodule update --init --recursive. Это позволяет автоматически загружать и обновлять код сабмодуля на устройствах, где развёртывается основной проект, обеспечивая актуальность кода и упрощая процесс обновления.

## Обзор
Этот сабмодуль является частью проекта "Feeder" и предназначен для обеспечения автоматического обновления кода на устройствах Raspberry Pi. В него входит исходный код на Python для функционала проекта, тесты, дополнительные скрипты и графический интерфейс пользователя (GUI) для настройки.

## Структура
- **src/**: Содержит исходный код на Python, необходимый для функциональности проекта, включая модули для обработки аналого-цифрового преобразования, управления конфигурациями, функций кормушки, взаимодействия с базой данных и интеграции считывателя RFID.
- **tests/**: Содержит различные тестовые скрипты для проверки надежности и функциональности компонентов, включая тесты для реле, модуля RFID (Ethernet и USB), связи с сервером и измерения веса.
- **scripts/**: Содержит дополнительные скрипты для поддержки проекта, включая GUI для более простого управления настройками.
- **README.md**: Предоставляет обзор содержания сабмодуля и его назначения в рамках проекта "Feeder".

## Файлы исходного кода
- `_adc_data.py`: Управляет аналого-цифровым преобразованием.
- `_config_manager.py`: Обрабатывает настройки конфигурации.
- `_feeder_module.py`: Содержит функции кормушки.
- `_headers.py`: Модуль управления дополнительными библиотеками
- `_glb_val.py`: Определяет общие константы и заголовки.
- `main_feeder.py`: Основной исполняемый скрипт проекта.
- `_sql_database.py`: Управляет взаимодействием с базой данных.
- `_chafon_rfid_lib.py`: Интегрирует считыватель RFID Chafon CF-MU904.

## Тестовые скрипты
- `relay_test.py`: Тестирует датчик перерывания луча.
- `rfid_ethernet_test.py`: Тестирует модуль чтения RFID по Ethernet.
- `rfid_usb_test_2.py`: Тестирует модуль чтения RFID по USB.
- `test_post.py`: Тестирует связь с сервером.
- `weight_measure_test`: Тестирует датчик измерения веса.

## Дополнительные скрипты
- **gui/**: Содержит файлы GUI для настройки пользователя.

### Файлы GUI
- `config_gui.py`: Графический интерфейс пользователя для изменения конфигураций проекта.

## Установка и использование
Для использования этого сабмодуля его следует регулярно обновлять в рамках процедуры обновления проекта "Feeder". Пожалуйста, обратитесь к основной документации проекта за подробными инструкциями по обновлению и управлению этим сабмодулем.

