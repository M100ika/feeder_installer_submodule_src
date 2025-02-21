#!/bin/bash

mkdir -p /home/pi/Documents/

# Парсим serial_number
serial_number=$(awk -F' *= *' '/serial_number/ {print $2}' /home/pi/feeder_v71/feeder_installer_submodule_src/src/config.ini)

# Время и данные системы
date=$(date '+%Y-%m-%d %H:%M:%S')
uis=$(cat /proc/uptime | awk '{print int($1)}')
number=$(cat /proc/sys/kernel/random/boot_id)
proc_temp=$(awk '{print $1/1000}' /sys/class/thermal/thermal_zone0/temp)
shutdown=$(last -x | head -1 | tail -c 35 | head -c 17)
daemon_en_1=$(systemctl is-enabled feeder.service 2>/dev/null)
daemon_ac_1=$(systemctl is-active feeder.service 2>/dev/null)

# Определяем состояние демона
dep="false"
dap="false"
[[ $daemon_en_1 == "enabled" ]] && dep="true"
[[ $daemon_ac_1 == "active" ]] && dap="true"

local_ip=$(hostname -I | awk '{print $1}')
errorCode="WAIT_FOR_TUNNEL"

# Запуск временного туннеля Cloudflare
TUNNEL_URL=$(cloudflared tunnel --url ssh://localhost:22 2>&1 | awk '/https:\/\/.*\.trycloudflare.com/ {print $NF}')

# Проверка результата
if [[ -z "$TUNNEL_URL" ]]; then
    TUNNEL_URL="TUNNEL_FAILED"
    errorCode="TUNNEL_FAILED $local_ip"
else
    errorCode="$TUNNEL_URL $local_ip"
fi

# Функция для создания JSON
post_data_to_file() {
    cat <<JSON
{
    "EventDate": "$date",
    "SerialNumber": "$serial_number",
    "Uptime": "$uis",
    "BootId": "$number",
    "CpuTemp": "$proc_temp",
    "LastShutdown": "$shutdown",
    "ErrorCode": "$errorCode",
    "IsActive": "$dap",
    "IsEnabled": "$dep"
}
JSON
}

# Если система только что загрузилась, сохраняем данные
if [ "$uis" -lt 10 ]; then
    echo "$(post_data_to_file)" >> /home/pi/Documents/Last_shutdown.txt
fi

# Запись в лог
echo "$(post_data_to_file)" > /home/pi/Documents/logservice.txt

# Отправка данных на сервер и проверка ответа
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Accept: application/json" \
  -H "Content-Type:application/json" \
  -X POST --data "$(post_data_to_file)" "http://smart-farm.kz:8501/v2/SmartScalesStatuses")

# Логируем результат
if [[ "$RESPONSE" -eq 200 ]]; then
    echo "$date - ✅ Данные успешно отправлены. HTTP $RESPONSE" >> /home/pi/Documents/logservice.txt
else
    echo "$date - ❌ Ошибка отправки данных. HTTP $RESPONSE" >> /home/pi/Documents/logservice.txt
fi

# Вывод в консоль (для отладки)
echo "Отправка завершена. HTTP статус: $RESPONSE"
