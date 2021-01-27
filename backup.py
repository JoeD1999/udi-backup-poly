#!/usr/bin/env python3
"""
Polyglot v3 save/restore node server.
Copyright (C) 2020,2021 Robert Paauwe
"""
import sys
import time
import udi_interface
from nodes import backup

LOGGER = udi_interface.LOGGER

if __name__ == "__main__":
    try:
        polyglot = udi_interface.Interface('BACKUP')
        polyglot.start()
        control = backup.Controller(polyglot, 'controller', 'controller', 'Save/Restore')
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
        

