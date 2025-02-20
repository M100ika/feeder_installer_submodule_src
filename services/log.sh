#!/bin/bash

echo "УСТАНАВЛИВАЮ cloudflared..."

# Установка cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/

echo "cloudflared установлен."

echo "СОЗДАЮ СКРИПТ ДЛЯ АВТОЗАПУСКА ТУННЕЛЯ..."

cat << 'EOF' > /home/pi/feeder_v71/feeder_installer_submodule_src/services/start_tunnel.sh
#!/bin/bash

mkdir -p /home/pi/Documents/

# ПАРСИМ serial_number из config.ini
serial_number=$(awk -F' *= *' '/serial_number/ {print $2}' /home/pi/feeder_v71/feeder_installer_submodule_src/src/config.ini)

# ВРЕМЯ и СИСТЕМНЫЕ ДАННЫЕ
date=$(date '+%Y-%m-%d %H:%M:%S')
uis=$(cat /proc/uptime | awk '{print int($1)}')
number=$(cat /proc/sys/kernel/random/boot_id)

proc_temp=$(cat /sys/class/thermal/thermal_zone0/temp)
proc_temp=$(bc <<< "scale=1; $proc_temp / 1000")

shutdown=$(last -x | head -1 | tail -c 35 | head -c 17)

daemon_en_1=$(systemctl is-enabled feeder.service 2>/dev/null)
daemon_ac_1=$(systemctl is-active feeder.service 2>/dev/null)

if [[ $daemon_en_1 == "enabled" ]]; then
    dep="true"
else
    dep="false"
fi

if [[ $daemon_ac_1 == "active" ]]; then
    dap="true"
else
    dap="false"
fi

local_ip=$(hostname -I | awk '{print $1}')

errorCode="WAIT_FOR_TUNNEL"

# ЗАПУСК ВРЕМЕННОГО ТУННЕЛЯ CLOUDFLARE
TUNNEL_URL=$(cloudflared tunnel --url ssh://localhost:22 2>&1 | grep -o "https://.*\.trycloudflare.com")

# ЕСЛИ ТУННЕЛЬ НЕ СОЗДАЛСЯ
if [[ -z "$TUNNEL_URL" ]]; then
    TUNNEL_URL="TUNNEL_FAILED"
    errorCode="TUNNEL_FAILED $local_ip"
else
    errorCode="$TUNNEL_URL $local_ip"
fi

# ФУНКЦИЯ ДЛЯ СОЗДАНИЯ JSON-ФАЙЛА
post_data_to_file()
{
    cat <<JSON
{   
    "EventDate": "$date",
    "SerialNumber": "$serial_number",
    "Uptime": "$uis",
    "BootId": "$number",
    "CpuTemp": "$proc_temp",
    "LastShutdown":"$shutdown",
    "ErrorCode": "$errorCode",
    "IsActive": "$dap", 
    "IsEnabled": "$dep"
}
JSON
}

# ЕСЛИ СИСТЕМА ТОЛЬКО ПЕРЕЗАГРУЗИЛАСЬ
if [ "$uis" -lt 10 ]; then
    echo "$(post_data_to_file)" >> /home/pi/Documents/Last_shutdown.txt
fi

# ЗАПИСЬ В ЛОГ
echo "$(post_data_to_file)" > /home/pi/Documents/logservice.txt

# ОТПРАВКА JSON НА СЕРВЕР
curl -s \
 -H "Accept: application/json" \
 -H "Content-Type:application/json" \
 -X POST --data "$(post_data_to_file)" "http://smart-farm.kz:8501/v2/SmartScalesStatuses"
EOF

chmod +x /home/pi/feeder_v71/feeder_installer_submodule_src/services/start_tunnel.sh

echo "Скрипт start_tunnel.sh создан."

echo "НАСТРАИВАЮ АВТОЗАПУСК через crontab..."

# Добавляем в crontab автозапуск после перезагрузки с полным путём
(crontab -l 2>/dev/null; echo "@reboot /bin/bash /home/pi/feeder_v71/feeder_installer_submodule_src/services/start_tunnel.sh") | crontab -

echo "АВТОЗАПУСК НАСТРОЕН."

echo "ВСЁ ГОТОВО. Теперь туннель будет запускаться после каждой перезагрузки, а ссылка отправляться на сервер."
