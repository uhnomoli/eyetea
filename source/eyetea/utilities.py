import argparse
import base64
import ipaddress
import os
import pathlib
import random
import socket
import string
import time
import urllib.parse

import werkzeug.security
import werkzeug.utils


class HostPort:
    def __init__(self, value):
        if ':' not in value:
            raise argparse.ArgumentTypeError(
                'Host port must be in <ip>:<port> form')

        host, port = value.rsplit(':', 1)

        self.host = ipaddress.ip_address(host).compressed
        self.port = Port(port)

class HostSpecified:
    def __new__(cls, value, *args, **kwargs):
        host = ipaddress.ip_address(value, *args, **kwargs)
        if host.is_unspecified:
            raise argparse.ArgumentTypeError(
                'Host must not be an unspecified address')

        return host.compressed

class Path:
    def __new__(cls, value, *args, **kwargs):
        path = pathlib.Path(value)
        if not path.exists():
            raise argparse.ArgumentTypeError('Path does not exist')
        elif not path.is_dir():
            raise argparse.ArgumentTypeError('Path must be a directory')
        elif not os.access(path, os.R_OK | os.W_OK | os.X_OK):
            raise argparse.ArgumentTypeError(
                'Lack necessary permissions to path')

        return path.resolve(strict=True)

class Port(int):
    def __new__(cls, value, *args, **kwargs):
        value = super().__new__(int, value, *args, **kwargs)
        if value < 1 or value > 65535:
            raise argparse.ArgumentTypeError(
                'Port must be between 1 and 65535')

        return value


def context_parse(value):
    context = 'execution'
    encoding = None

    try:
        context, encoding = value.split(':', 1)
    except AttributeError:
        context = None
    except ValueError:
        context = value

    return context, encoding

def payload_encode(payload, encoding):
    if encoding in ('b64', 'base64'):
        return base64.b64encode(payload.encode('utf-8')).decode('utf-8')
    elif encoding in ('u', 'url'):
        return urllib.parse.quote_plus(payload)
    else:
        return payload

def interpreter_parse(value):
    interpreter = None
    platform = 'linux'

    try:
        interpreter, platform = value.split(':', 1)
    except AttributeError:
        platform = None
    except ValueError:
        interpreter = value

    return interpreter, platform

def path_secure(base, path, *, allow_traversal=False):
    if not allow_traversal:
        path = werkzeug.utils.secure_filename(path)

    return werkzeug.security.safe_join(base, path)

def port_wait(host, port, timeout=5):
    timeout = timeout * pow(10, 9)
    start = time.perf_counter_ns()
    while (time.perf_counter_ns() - start) < timeout:
        try:
            with socket.create_connection((host, port)) as sd:
                sd.close()

                return
        except ConnectionRefusedError:
            time.sleep(0.5)

    raise RuntimeError('Unable to connect')

def powershell_encode(data):
    return base64.b64encode(data.encode('utf-16le')).decode('utf-8')

def strings_random(count, length):
    strings = set()
    while len(strings) < count:
        strings.add(''.join(random.choices(string.ascii_lowercase, k=length)))

    return list(strings)

