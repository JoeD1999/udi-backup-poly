
# backup-polyglot

This is the backup/restore Poly for the [Universal Devices ISY994i](https://www.universal-devices.com/residential/ISY) [Polyglot interface](http://www.universal-devices.com/developers/polyglot/docs/) with  [Polyglot V3](https://github.com/UniversalDesignInc/pg3)
(c) 2020,2021 Robert Paauwe

This node server takes a snapshot of the lighting type device status and can then later restore the devices to those values.

Lighting devices are those devices that have a status value using the unit-of-measure for level (0-255) or percent.  This should cover most Insteon switch/lamp modules and Z-wave switch/lamp modules.

## Installation

1. Backup Your ISY in case of problems!
   * Really, do the backup, please
2. Go to the Polyglot Store in the UI and install.
3. Add NodeServer in Polyglot Web
   * After the install completes, Polyglot will reboot your ISY, you can watch the status in the main polyglot log.
4. Once your ISY is back up open the Admin Console.
5. Configure the node server with the ISY ip address, username, and password

### Node Settings
The settings for this node are:

#### Short Poll
   * Not used
#### Long Poll
   * Not used

#### IP Address
   * The IP Address of the ISY to snapshot and restore
#### Username
   * The ISY username
#### Password
   * The ISY password

## Requirements
Polisy running Polyglot version 3.x

# Upgrading

Then restart the Backup nodeserver by selecting it in the Polyglot dashboard and select Control -> Restart, then watch the log to make sure everything goes well.

# Release Notes

- 2.0.0 01/27/2021
   - Updates to work on Polyglot version 3
- 1.0.2 10/20/2020
   - filter devices by family and category.  Only save Insteon and Z-Wave
     switches/dimmers
- 1.0.1 10/16/2020
   - fix bug where backup would cause duplicate entries
   - changed to /rest/nodes endpoint to improve performance
- 1.0.0 10/15/2020
   - Initial release to public github
