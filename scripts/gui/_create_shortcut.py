import os
import sys
import platform
import configparser

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
    
    return os.path.dirname(os.path.abspath(__file__))[:-18]


def create_shortcut():
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    script_path = os.path.expanduser('/opt/feeder_project/scripts/gui')

    desktop_file = os.path.join(desktop_path, 'feeder_config.desktop')
    with open(desktop_file, 'w') as f:
        if os.path.exists("/home/maxat/Projects/Agrarka/feeder-installer/venv"):
            f.write(f"""[Desktop Entry]
Type=Application
Name=Config GUI
Exec=bash -c 'source /home/maxat/Projects/Agrarka/feeder-installer/venv/bin/activate && python3 "/home/maxat/Projects/Agrarka/feeder-installer/submod/scripts/gui/config_gui.py"'
Icon=/home/maxat/Projects/Agrarka/feeder-installer/submod/scripts/gui/feeder_shortcut.png
Terminal=false
""")
        else:
            f.write(f"""[Desktop Entry]
Type=Application
Name=Config GUI
Exec=bash -c 'python3 "{script_path}/config_gui.py"'
Icon={script_path}/feeder_shortcut.png
Terminal=false
""")
    os.chmod(desktop_file, 0o755)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    SETTINGS_PATH = f'{os.getcwd()}/submod/settings.ini'
    config.read('submod/settings.ini')
    
    config.set('PATHS', 'PROJECT_PATH', is_raspberry_pi())
    with open('submod/settings.ini', 'w') as configfile:
        config.write(configfile)
    create_shortcut()