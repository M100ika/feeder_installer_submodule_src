import platform
import os 

def is_raspberry_pi(): # проверяет ОС raspberry или нет. 
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if 'Hardware' in line:
                    if 'BCM' in line:
                        return "/etc/feeder/config.ini"
    except IOError:
        pass

    platform_info = platform.uname()
    if 'arm' in platform_info.machine:
        return "/etc/feeder/config.ini"
    
    return os.path.dirname(os.path.abspath(__file__))[:-4]

CONFIG_FILE_PATH = is_raspberry_pi()
print(CONFIG_FILE_PATH)
