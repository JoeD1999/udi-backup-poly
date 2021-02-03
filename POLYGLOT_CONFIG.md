## Configuration

This node server does not have any configuration parameters.

## How it works
When the query command is run the node server will query the ISY for the status of all dimmer and on/off type devices.  The current status of these devices will be saved.  When the restore command is run, the node server will attempt to use the saved status values to reset all the saved device status values.
