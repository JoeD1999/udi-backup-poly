#!/usr/bin/env python3
"""
Polyglot v2 save/restore node server.
Copyright (C) 2020 Robert Paauwe
"""
import sys
import time
import polyinterface
from nodes import backup

LOGGER = polyinterface.LOGGER

if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('BACKUP')
        polyglot.start()
        control = backup.Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
        

