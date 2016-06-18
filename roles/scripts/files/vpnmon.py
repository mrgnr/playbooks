#!/usr/bin/env python3

import logging
from pathlib import Path
import random
import subprocess
import time

import requests
from requests.exceptions import ConnectionError, ReadTimeout


LOG_FILE = Path('/var/log/vpnmon.log')
LOG_LEVEL = logging.INFO
OPENVPN_DIR = Path('/etc/openvpn/')
OPENVPN_CLIENT_CFG = OPENVPN_DIR / 'client.conf'
PING_URL = 'https://google.com'
SLEEP_PERIOD = 60
ROTATE_PROBABILITY = 0.01


def rotate_connection():
    logger = logging.getLogger(__name__)

    # Randomly choose an OpenVPN configuration
    configs = list(OPENVPN_DIR.glob('*.ovpn'))
    config = random.choice(configs)
    logger.info('Rotating connection. Using configuration `{}`'.format(config))

    # Link to the configuration and reload OpenVpn
    if OPENVPN_CLIENT_CFG.is_symlink():
        OPENVPN_CLIENT_CFG.unlink()
    try:
        OPENVPN_CLIENT_CFG.symlink_to(config)
    except FileExistsError as e:
        logger.error('Failed to rotate connection! `{}` already exists!'.
                     format(OPENVPN_CLIENT_CFG))

    subprocess.check_output(['/usr/sbin/service', 'openvpn@client', 'reload'])


def check_connection():
    try:
        subprocess.check_output(['/usr/bin/curl', '--interface', 'tun0', '-L',
                                 PING_URL])
    except subprocess.CalledProcessError:
        logger = logging.getLogger(__name__)
        logger.warning('Failed to ping {}'.format(PING_URL))
        return False
    else:
        return True


def _check_connection():
    try:
        requests.get(PING_URL, timeout=5)
    except (ConnectionError, ReadTimeout):
        logger = logging.getLogger(__name__)
        logger.warning('Failed to ping {}'.format(PING_URL))
        return False
    else:
        return True


def main():
    logger = logging.getLogger(__name__)

    while True:
        if random.uniform(0, 1) < ROTATE_PROBABILITY or not check_connection():
            rotate_connection()

        sleep_period = random.gauss(SLEEP_PERIOD, 10)
        time.sleep(sleep_period)


if __name__ == '__main__':
    log_format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    logging.basicConfig(filename=str(LOG_FILE),
                        level=LOG_LEVEL,
                        format=log_format,
                        datefmt='%m-%d %H:%M')

    try:
        main()
    except Exception as e:
        print(e)
