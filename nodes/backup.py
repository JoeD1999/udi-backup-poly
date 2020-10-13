#!/usr/bin/env python3
"""
Polyglot v2 node server to save/restore node status.
Copyright (C) 2020 Robert Paauwe
"""

import polyinterface
import sys
import time
import datetime
import requests
import threading
import socket
import math
import node_funcs

LOGGER = polyinterface.LOGGER

@node_funcs.add_functions_as_methods(node_funcs.functions)
class Controller(polyinterface.Controller):
    id = 'backup'
    hint = [0,0,0,0]

    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'BACKUP'
        self.address = 'backup'
        self.primary = self.address
        self.configured = False
        self.dsc = None
        self.mesg_thread = None
        self.discovery_ok = False

        self.params = node_funcs.NSParameters([{
            'name': 'IP Address',
            'default': 'set me',
            'isRequired': True,
            'notice': 'IP Address of ISY must be set',
            },
            {
            'name': 'Username',
            'default': 'set me',
            'isRequired': True,
            'notice': 'ISY Username must be set',
            },
            {
            'name': 'Password',
            'default': 'set me',
            'isRequired': True,
            'notice': 'ISY Password must be set',
            },
            ])

        self.poly.onConfig(self.process_config)

    # Process changes to customParameters
    def process_config(self, config):
        LOGGER.error('process_config = {}'.format(config))
        (valid, changed) = self.params.update_from_polyglot(config)
        if changed and not valid:
            LOGGER.debug('-- configuration not yet valid')
            self.removeNoticesAll()
            self.params.send_notices(self)
        elif changed and valid:
            LOGGER.debug('-- configuration is valid')
            self.removeNoticesAll()
            self.configured = True
            # TODO: Run discovery/startup here?
            if self.discovery_ok:
                self.discover()
        elif valid:
            LOGGER.debug('-- configuration not changed, but is valid')
            # is this necessary
            #self.configured = True

    def start(self):
        LOGGER.info('Starting node server')
        self.set_logging_level()
        self.check_params()

        self.discovery_ok = True

        # Read current device status
        if self.configured:
            self.discover()
            LOGGER.info('Node server started')
        else:
            LOGGER.info('Waiting for configuration to be complete')

    def longPoll(self):
        pass

    def shortPoll(self):
        pass

    def query(self):
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    # Use discover to query for all device status.
    def discover(self, *args, **kwargs):
        LOGGER.debug('in discover()')

        isy = 'http://' + self.params.get('IP Address') + '/rest/status'

        c = requests.get(isy, auth=(self.params.get('Username'), self.params.get('Password')))

        LOGGER.debug(c)


    # Delete the node server from Polyglot
    def delete(self):
        LOGGER.info('Removing node server')

    def stop(self):
        LOGGER.info('Stopping node server')

    def update_profile(self, command):
        st = self.poly.installprofile()
        return st

    def check_params(self):
        # NEW code, try this:
        self.removeNoticesAll()

        if self.params.get_from_polyglot(self):
            LOGGER.debug('All required parameters are set!')
            self.configured = True
        else:
            LOGGER.debug('Configuration required.')
            LOGGER.debug('IP Address = ' + self.params.get('IP Address'))
            LOGGER.debug('Username = ' + self.params.get('Username'))
            self.params.send_notices(self)

    def remove_notices_all(self, command):
        self.removeNoticesAll()

    def set_logging_level(self, level=None):
        if level is None:
            try:
                level = self.get_saved_log_level()
            except:
                LOGGER.error('set_logging_level: get saved level failed.')

            if level is None:
                level = 10
            level = int(level)
        else:
            level = int(level['value'])

        self.save_log_level(level)

        LOGGER.info('set_logging_level: Setting log level to %d' % level)
        LOGGER.setLevel(level)


    commands = {
            'UPDATE_PROFILE': update_profile,
            'REMOVE_NOTICES_ALL': remove_notices_all,
            'DEBUG': set_logging_level,
            }

    # For this node server, all of the info is available in the single
    # controller node.
    drivers = [
            {'driver': 'ST', 'value': 1, 'uom': 2},   # node server status
            ]

