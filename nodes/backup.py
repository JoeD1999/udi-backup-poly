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
import json
import math
import xmltodict
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
        self.current_state = []

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
        #LOGGER.error('process_config = {}'.format(config))
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
                LOGGER.info('Calling discover() from process config')
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
            LOGGER.info('Calling discover() from start')
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
        LOGGER.info('in discover()')

        #isy = 'http://' + self.params.get('IP Address') + '/rest/status'
        isy = 'http://' + self.params.get('IP Address') + '/rest/nodes'

        c = requests.get(isy, auth=(self.params.get('Username'), self.params.get('Password')))

        jdata = xmltodict.parse(c.text)

        c.close()

        #LOGGER.error(jdata['nodes'])
        LOGGER.debug('Query done, look at each entry')
        count = 0
        self.current_state = []
        for node in jdata['nodes']['node']:
            # node['@id'] is the node address
            try:
                if 'property' not in node:
                    continue

                p = node['property']
                if isinstance(p, list):
                    LOGGER.info('Device ' + node['name'] + ' has a property list, skipping')
                    continue

                if 'family' in node:
                    family =  node['family']
                else:
                    family = 1
                LOGGER.debug('address = ' + node['address'])
                LOGGER.debug('name = ' + node['name'])
                LOGGER.debug('type = ' + node['type'])
                LOGGER.debug('family = ' + str(family))
                LOGGER.debug('   ' + p['@id'] + ' = ' + p['@value'] + ' -- ' + p['@uom'])


                if p['@id'] == 'ST' and p['@value'] is not "":
                    if p['@uom'] == '100' or p['@uom'] == '51':
                        category = node['type'].split('.')[0]
                        if family == 1 and (category == '1' or category == '2'):
                            # insteon categories 1 and 2
                            entry = {
                                'address': node['address'],
                                'name': node['name'],
                                'value': p['@value']
                            }
                            self.current_state.append(entry)
                            count += 1
                        elif family == 4 and (category == '3' or category == '4'):
                            # z-wave categories 3 and 4
                            entry = {
                                'address': node['address'],
                                'name': node['name'],
                                'value': p['@value']
                            }
                            self.current_state.append(entry)
                            count += 1

            except Exception as e:
                LOGGER.error('Failed to process ' + node['name'] + ': ' + str(e))
                LOGGER.error(str(p))

        LOGGER.info('Processed ' + str(count) + ' devices.')


        # Save the current state
        for node in self.current_state:
            LOGGER.info('Saving ' + node['address'] + '/' + node['name'] + ' value ' + node['value'])

        cdata = {
                'state': self.current_state,
                'level': 10,
                }
        #self.poly.saveCustomData(cdata)
        self.save_custom_param('state', self.current_state)

    def restore(self, command):
        LOGGER.debug('getting custom data to restore: ' + str(command))
        state = self.get_custom_param('state')
        if state is not None:
            for node in self.polyConfig['customData']['state']:
                cmd = 'http://' + self.params.get('IP Address')
                if node['value'] == '0':
                    cmd += '/rest/nodes/' + node['address'] + '/cmd/DOF'
                else:
                    cmd += '/rest/nodes/' + node['address'] + '/cmd/DON/' + node['value']
                LOGGER.info('Calling ' + cmd)

                c = requests.get(cmd, auth=(self.params.get('Username'), self.params.get('Password')))
                c.close()


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
            'DISCOVER': discover,
            'RESTORE': restore,
            }

    # For this node server, all of the info is available in the single
    # controller node.
    drivers = [
            {'driver': 'ST', 'value': 1, 'uom': 2},   # node server status
            ]

