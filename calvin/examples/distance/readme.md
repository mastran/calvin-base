# Distance sensor

In this example a SR04 Ultrasonic distance sensor is used with Calvin on a
Raspberry Pi.


## Setup

### Hardware

- A SR04 Ultrasonic distance sensor
- A Raspberry Pi 


### Installation

Edit the file `gpio-pins.json` to reflect your pin assignment (if it differs
from the one specified in the file). The default pin-settings used in this
example are (in BCM-mode)

    "echo_pin": 24,
    "trig_pin": 23

- Vcc needs +5v (pin 2).
- For ground, any ground pin works of course. I like pin 6 myself.


### Calvin configuration

The following plugins needs to be loaded to run this script:
- `distance_plugin`
- `gpio_plugin`

A `calvin.conf` file is prepared for this purpose. For the `calvin.conf` to be
loaded, start the calvin script from within the directory the `calvin.conf`
file is placed. For other ways of loading the configuration, please see
the Calvin Wiki page about [Configuration](https://github.com/EricssonResearch/calvin-base/wiki/Configuration)


## Running

Run the following command from within the directory the `calvin.conf`
file is placed:

    $ CALVIN_GLOBAL_STORAGE_TYPE=\"local\" csruntime --host localhost --keep-alive distance.calvin --attr-file gpio-pins.json

## DHT

Calvin's internal registry is not strictly needed when running this small example,
it has therefor been turned off. To turn it on and run the application with DHT
instead, remove `CALVIN_GLOBAL_STORAGE_TYPE=\"local\"` from the command. I.e:

    $ csruntime --host localhost --keep-alive distance.calvin --attr-file gpio-pins.json




