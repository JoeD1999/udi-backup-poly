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
import socket
import json
import math
import xmltodict
#import node_funcs

LOGGER = udi_interface.LOGGER

class Controller(udi_interface.Node):
    id = 'backup'
    hint = [0,0,0,0]

    def __init__(self, polyglot, primary, address, name):
        super(Controller, self).__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.name = 'Save/Restore lighting'
        self.address = address
        self.primary = primary
        self.configured = False
        self.mesg_thread = None
        self.discovery_ok = False
        self.current_state = []
        self.Parameters = Custom(polyglot, 'customparams')
        self.Notices = Custom(polyglot, 'notices')
        self.CustomData = Custom(polyglot, 'customdata')

        """
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
        """

        self.poly.onCustomParams(self.parameterHandler)
        self.poly.onStart(address, self.start)

        self.poly.addNode(self)

    def parameterHandler(self, params):
        self.Parameters.load(params)

        # TODO: Check parameters and possibly run discover
        configured = True
        try:
            self.Notices.clear()
            if self.Parameters['IP Address'] is None:
                self.Notices.ip = 'Please set the IP address of the ISY'
                configured = False
            if self.Parameters['Username'] is None:
                self.Notices.ip = 'Please set the ISY username'
                configured = False
            if self.Parameters['Password'] is None:
                self.Notices.ip = 'Please set the ISY password'
                configured = False
        except Exception as e:
            LOGGER.error('Parameter Failure: {}'.format(e))

        if not configured:
            self.configured = False
            return

        try:
            if self.Parameters.isChanged('IP Address') or
            self.Parameters.isChanged('Username') or
            self.Parameters.isChanged('Password'):
                self.discover()
        except Exception as e:
            LOGGER.error('Parameter Failure: {}'.format(e))

    def start(self):
        LOGGER.info('Starting node server')
        self.check_params()
        self.poly.updateProfile()
        self.poly.setCustomParamsDoc()

        if self.configured:
            LOGGER.info('Calling discover() from start')
            self.discover()
            LOGGER.info('Node server started')
        else:
            LOGGER.info('Waiting for configuration to be complete')

    # TODO: What should query really do?  Maybe query should get the
    # device status and save it instead of discover?
    def query(self):
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    # Use discover to query for all device status.
    def discover(self, *args, **kwargs):
        LOGGER.info('in discover()')

        isy = 'http://' + self.Parameters['IP Address'] + '/rest/nodes'

        c = requests.get(isy, auth=(self.Parameters['Username'], self.Parameters['Password']))

        jdata = xmltodict.parse(c.text)

        c.close()

        #LOGGER.error(jdata['nodes'])
        LOGGER.debug('Query done, look at each entry')
        count = 0
        current_state = []
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
                                        'name': node['name'], 
                                        'value':  p['@value']
                                    }
                            self.CustomData[node['address']] = entry
                            #current_state.append(entry)
                            count += 1
                        elif family == 4 and (category == '3' or category == '4'):
                            # z-wave categories 3 and 4
                            '''
                            entry = {
                                'address': node['address'],
                                'name': node['name'],
                                'value': p['@value']
                            }
                            current_state.append(entry)
                            '''
                            entry = {
                                        'name': node['name'], 
                                        'value':  p['@value']
                                    }
                            self.CustomData[node['address']] = entry
                            count += 1

            except Exception as e:
                LOGGER.error('Failed to process ' + node['name'] + ': ' + str(e))
                LOGGER.error(str(p))

        LOGGER.info('Processed ' + str(count) + ' devices.')


    def save(self, current_stat):
        # TODO: use a Custom class custom data here and maybe move this 
        #       to a separate method?
        # Save the current state
        for node in current_state:
            LOGGER.info('Saving ' + node['address'] + '/' + node['name'] + ' value ' + node['value'])

        self.CustomData.load(current_state)
        """
        cdata = {
                'state': self.current_state,
                'level': 10,
                }
        #self.poly.saveCustomData(cdata)
        self.save_custom_param('state', self.current_state)
        """

    def restore(self, command):
        LOGGER.debug('getting custom data to restore: ' + str(command))
        for address in self.CustomData.keys():
            cmd = 'http://' + self.Parameters['IP Address']
            if self.CustomData[address]['value'] == '0':
                cmd += '/rest/nodes/' + address + '/cmd/DOF'
            else:
                cmd += '/rest/nodes/' + address + '/cmd/DON/' + self.CustomData[address]['value']
            LOGGER.info('Calling ' + cmd)

            c = requests.get(cmd, auth=(self.Parameters['Username'], self.Parameters['Password']))
            c.close()

        """
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
        """


    # Delete the node server from Polyglot
    def delete(self):
        LOGGER.info('Removing node server')

    def stop(self):
        LOGGER.info('Stopping node server')

    def check_params(self):
        # NEW code, try this:
        self.Notices.clear()

        if self.params.get_from_polyglot(self):
            LOGGER.debug('All required parameters are set!')
            self.configured = True
        else:
            LOGGER.debug('Configuration required.')
            LOGGER.debug('IP Address = ' + self.params.get('IP Address'))
            LOGGER.debug('Username = ' + self.params.get('Username'))
            self.params.send_notices(self)

    commands = {
            'DISCOVER': discover,
            'QUERY': discover,
            'RESTORE': restore,
            }

    # For this node server, all of the info is available in the single
    # controller node.
    drivers = [
            {'driver': 'ST', 'value': 1, 'uom': 2},   # node server status
            ]

