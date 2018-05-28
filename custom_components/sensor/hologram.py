"""
Sensor for Hologram devices.

"""

import logging
import datetime
import json
import voluptuous as vol
import requests
import base64

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = datetime.timedelta(seconds=30)
API_URL = 'http://dashboard.hologram.io/api/1/csr/rdm/?apikey='
CONF_API_KEY = 'api_key'
CONF_DEVICE_ID = 'device_id'
DEFAULT_NAME = 'hologram'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the hologram sensor."""
    api_key = config[CONF_API_KEY]
    device_id = config[CONF_DEVICE_ID]
    name = config[CONF_NAME]
    add_devices([HologramDevice(device_id, name, api_key)])

def datetime_to_iso(time):
    """Take hologram time format and return datetime iso string."""
    datetime_obj = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
    return datetime_obj.isoformat()


class HologramDevice(Entity):
    """Class for a single hologram device."""

    def __init__(self, device_id, name, api_key):
        """Initialise the device object."""
        self._device_id = device_id
        self._api_key = api_key
        self._message_data = {}
        self._name = '{}_{}'.format(name, device_id)
        self._state = None

    def get_last_message(self):
        """Return the last message from a device."""

        url = (API_URL + self._api_key)
        params = {'deviceid': self._device_id , 'limit' : 1}
        resp = requests.get(url, json=params, timeout=10)
        json_data = resp.json()
        payload = json.loads(base64.b64decode(json.loads(json_data['data'][0]['data'])['data']).decode('utf-8'))
        # decode utf-8 not required once json lib updated
        time = json_data['data'][0]['logged']

        return {'payload': payload,
                'time': time}
                #'time': datetime_to_iso(time)}

    def update(self):
        """Fetch the latest device message."""
        self._message_data = self.get_last_message()
        self._state = self._message_data['payload']

    @property
    def name(self):
        """Return the HA name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the payload of the last message."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return other details about the last message."""
        return self._message_data
