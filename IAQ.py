#!/usr/bin/env python3
"""
Polyglot v3 indoor air quality node server.
Copyright (C) 2021 Donovan Clay
"""
import sys
import time
import udi_interface
from nodes import iaq

LOGGER = udi_interface.LOGGER

if __name__ == "__main__":
    try:
        polyglot = udi_interface.Interface([iaq.Controller,])
        polyglot.start()
        control = iaq.Controller(polyglot, 'controller', 'controller', 'Indoor_Air_Quality')
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
        

