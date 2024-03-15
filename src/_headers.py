import sys
import subprocess
import pkg_resources
from pkg_resources import DistributionNotFound, VersionConflict
import platform

def should_install_requirement(requirement) -> str:
    should_install = False
    try:
        pkg_resources.require(requirement)
    except (DistributionNotFound, VersionConflict):
        should_install = True
    return should_install


def install_packages(requirement_list) -> list:
    try:
        requirements = [
            requirement
            for requirement in requirement_list
            if should_install_requirement(requirement)
        ]
        if len(requirements) > 0:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *requirements])
        else:
            from loguru import logger
            logger.info("Requirements already satisfied (info).")
    except Exception as e:
        print(e)


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
    
    return "../../config/config.ini"

CONFIG_FILE_PATH = is_raspberry_pi()


