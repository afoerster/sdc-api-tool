import datetime
import os
import shlex
import subprocess
import time
import logging

import pytest
import requests

TIMEOUT_SECONDS = 30

@pytest.fixture(scope="session")
def sdc(request):
    compose_file = "compose/sdc.yml"
    popen_kwargs = {}
    proc = subprocess.Popen(["docker-compose", "-f", compose_file, "up"], **popen_kwargs)
    def cleanup():
        logging.info("cleaning up process")
        proc.kill()
        subprocess.call(
            ["docker-compose", "-f", compose_file, "kill"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.call(
            ["docker-compose", "-f", compose_file, "rm", "-f"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("finished cleanup")
    request.addfinalizer(cleanup)
    curl_until_success(18630)
    return proc

def get_docker_host():
    docker_host = os.environ.get('DOCKER_HOST', '').strip()
    if not docker_host:
        return '127.0.0.1'
    logging.info("using docker host: " + docker_host)
    return docker_host

def curl_until_success(port, endpoint="/", params={}):
    timeout = datetime.datetime.now() + datetime.timedelta(seconds=TIMEOUT_SECONDS)
    url = "http://{}:{}{}".format(
                get_docker_host(), port, endpoint)
    while datetime.datetime.now() < timeout:
        try:
            response = requests.get(url, params=params)
            logging.info("received response from endpoint")
        except requests.exceptions.ConnectionError:
            logging.info("waiting for service")
            pass
        else:
            return response
        time.sleep(0.25)
    raise Exception("service didn't start in time")

def execute_cmd(cmd):
    logging.info("executing command: " + cmd)
    assert subprocess.check_call(shlex.split(cmd)) == 0
