#!/usr/bin/env python3
"""
Polyglot v3 node server to save/restore node status.
Copyright (C) 2020,2021 Robert Paauwe
"""

import udi_interface
import sys
import time
import datetime
import requests
import threading
import re
import socket
import json
import math
import xmltodict
import logging

LOGGER = udi_interface.LOGGER

# set log level for various interface modules
udi_interface.interface.LOGGER.setLevel("ERROR")
udi_interface.isy.ILOGGER.setLevel("ERROR")
udi_interface.custom.CLOGGER.setLevel("ERROR")  # override default setting?
udi_interface.node.NLOGGER.setLevel("ERROR")  # override default setting?

Custom = udi_interface.Custom
ISY = udi_interface.ISY

class Controller(udi_interface.Node):
    id = 'backup'
    hint = [0,0,0,0]

    def __init__(self, polyglot, primary, address, name):
        super(Controller, self).__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.name = 'Save_Restore lighting'
        self.address = address
        self.primary = primary
        self.configured = False
        self.mesg_thread = None
        self.discovery_ok = False
        self.current_state = []

        self.Parameters = Custom(polyglot, 'customparams')
        self.Notices = Custom(polyglot, 'notices')
        self.CustomData = Custom(polyglot, 'customdata')
        self.ISY = ISY(polyglot)

        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.LOGLEVEL, self.handleLevelChange)


        self.poly.ready()
        self.poly.addNode(self)

    def start(self):
        LOGGER.info('Starting node server')

        self.poly.updateProfile()
        self.poly.setCustomParamsDoc()

        LOGGER.info('Node server started')

        self.query()

    def handleLevelChange(self, level):
        # Set interface log level to same as node server's
        udi_interface.interface.LOGGER.setLevel(level)
        udi_interface.isy.ILOGGER.setLevel(level)
        udi_interface.custom.CLOGGER.setLevel(level)
        udi_interface.node.NLOGGER.setLevel(level)
        

    def query(self, command=None):
        isy = self.ISY.pyisy()
        if isy is not None:

            # interact with node using address
            NODE = '38 B6 3F 1'
            node = isy.nodes[NODE]
            node.turn_off()
            sleep(5)
            node.turn_on()

            cnt = 0
            LOGGER.debug ('in query()')
            for name, node in isy.nodes:

                # check to make sure this is a device node, not group(scene)
                if re.match(r'^Group', type(node).__name__):
                    continue

                if node.family != None and node.family != "ZWave":
                    continue

                #LOGGER.info('*  {} {} {} {}   {} -- {}'.format(node.family, node.status, node.uom, node.type, type(node.uom), name))
                if node.status is not self.ISY.constants.ISY_VALUE_UNKNOWN:
                    #if node.uom == 100 or node.uom == 51:
                    if node.uom == "100" or node.uom == "51":
                        category = node.type.split('.')[0]
                        if node.family == None and (category == '1' or category == '2'):
                            # insteon categories 1 and 2
                            LOGGER.debug('   Found node {} with type {} category {} and status {}'.format(node.name, node.type, category, node.status))
                            entry = {
                                        'name': node.name, 
                                        'value': node.status 
                                    }
                            self.CustomData[node.address] = entry
                            cnt += 1
                        elif node.family == 'ZWave' and (category == '3' or category == '4'):
                            # z-wave categories 3 and 4
                            LOGGER.info('   Found node {} with type {} category {} and status {}'.format(node.name, node.type, category, node.status))
                            entry = {
                                        'name': node.name, 
                                        'value':  node.status
                                    }
                            self.CustomData[node.address] = entry
                            cnt += 1

        LOGGER.info('Query processed ' + str(cnt) + ' devices.')


    def restore(self, command):
        LOGGER.debug('getting custom data to restore: ' + str(command))
        for address in self.CustomData.keys():
            if self.CustomData[address]['value'] == '0':
                cmd = '/rest/nodes/' + address + '/cmd/DOF'
            else:
                cmd = '/rest/nodes/' + address + '/cmd/DON/' + self.CustomData[address]['value']
            LOGGER.info('Calling ' + cmd)

            self.ISY.cmd(cmd)

    # Delete the node server from Polyglot
    def delete(self):
        LOGGER.info('Removing node server')

    def stop(self):
        LOGGER.info('Stopping node server')

    commands = {
            'SAVE': query,
            'RESTORE': restore,
            }

    # For this node server, all of the info is available in the single
    # controller node.
    drivers = [
            {'driver': 'ST', 'value': 1, 'uom': 2},   # node server status
            {'driver': 'GV0', 'value': 1, 'uom': 56}
            ]

    def poll(self, polltype):

        if 'shortPoll' in polltype:

            self.setDriver('GV0', '1000', True, True)
