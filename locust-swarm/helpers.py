#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import paramiko
import socket
import time


def get_abs_path(dir):
    expanded = os.path.expanduser(os.path.expandvars(dir))
    return os.path.abspath(expanded)


def is_fabricable(ip_address, port=22):
    #logging.debug("Attemping to ssh into {0}:{1}".format(ip_address, port))
    print "Attemping to ssh into {0}:{1}".format(ip_address, port)
    while True:
        if can_ssh(ip_address, port):
            #logging.debug("successfully sshed into {0}".format(ip_address))
            print "successfully sshed into {0}".format(ip_address)
            break
        else:
            print "waiting to ssh into {0}".format(ip_address)
        time.sleep(10)


def can_ssh(host, port=22, timeout=3):
    original_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)

    try:
        transport = paramiko.Transport((host, port))
        transport.close()
        return True
    except:
        pass
    finally:
        socket.setdefaulttimeout(original_timeout)
    return False


# vim: filetype=python
