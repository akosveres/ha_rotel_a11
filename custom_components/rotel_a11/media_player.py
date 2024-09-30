"""
Support for controlling a Rotel A11 amplifier over a serial connection in Home Assistant.

For more details about this platform, please refer to the documentation at
https://github.com/akosveres/ha_rotel_a11
"""

import logging
import urllib.request
import voluptuous as vol
from serial import Serial

from homeassistant.components.media_player import (
    PLATFORM_SCHEMA,
    MediaPlayerEntity,
    MediaPlayerEntityFeature
)

from homeassistant.const import (
    CONF_DEVICE,
    CONF_NAME,
    CONF_SLAVE,
    CONF_TYPE,
    STATE_OFF,
    STATE_ON,
)

import homeassistant.helpers.config_validation as cv

import homeassistant.loader as loader

__version__ = "0.1"

_LOGGER = logging.getLogger(__name__)


"""
SUPPORT_A11 = (
    SUPPORT_SELECT_SOURCE
    | SUPPORT_SELECT_SOUND_MODE
    | SUPPORT_TURN_OFF
    | SUPPORT_TURN_ON
    | SUPPORT_VOLUME_MUTE
)

# SUPPORT_A11_WITH_CXN = (
#     SUPPORT_SELECT_SOURCE
#     | SUPPORT_SELECT_SOUND_MODE
#     | SUPPORT_TURN_OFF
#     | SUPPORT_TURN_ON
#     | SUPPORT_VOLUME_MUTE
#     | SUPPORT_VOLUME_STEP
# )
"""

SUPPORT_A11 = (
    MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_STEP
)

# SUPPORT_A11_WITH_CXN = (
#     MediaPlayerEntityFeature.SELECT_SOURCE
#     | MediaPlayerEntityFeature.SELECT_SOUND_MODE
#     | MediaPlayerEntityFeature.TURN_OFF
#     | MediaPlayerEntityFeature.TURN_ON
#     | MediaPlayerEntityFeature.VOLUME_MUTE
#     | MediaPlayerEntityFeature.VOLUME_STEP
# )

DEFAULT_NAME = "Rotel A11"
DEVICE_CLASS = "receiver"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE): cv.string,
        vol.Required(CONF_TYPE): cv.string,      
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_SLAVE): cv.string,
    }
)

NORMAL_INPUTS_A11 = {
    # "A1" : "#03,04,00",
    # "A2" : "#03,04,01",
    # "A3" : "#03,04,02",
    # "A4" : "#03,04,03",
    # "D1" : "#03,04,04",
    # "D2" : "#03,04,05",
    # "D3" : "#03,04,06",
    "Bluetooth" : "bluetooth!",
    "AUX1" : "aux1!",
    "PHONO" : "phono!"
}

# NORMAL_INPUTS_CXA81 = {
#     "A1" : "#03,04,00",
#     "A2" : "#03,04,01",
#     "A3" : "#03,04,02",
#     "A4" : "#03,04,03",
#     "D1" : "#03,04,04",
#     "D2" : "#03,04,05",
#     "D3" : "#03,04,06",
#     "Bluetooth" : "#03,04,14",
#     "USB" : "#03,04,16",
#     "XLR" : "#03,04,20"
# }

NORMAL_INPUTS_AMP_REPLY_A11 = {
    # "#04,01,00" : "A1",
    # "#04,01,01" : "A2",
    # "#04,01,02" : "A3",
    # "#04,01,03" : "A4",
    # "#04,01,04" : "D1",
    # "#04,01,05" : "D2",
    # "#04,01,06" : "D3",
    "source=bluetooth$" : "Bluetooth",
    "source=aux1$" : "AUX1",
    "source=phono$" : "PHONO"
}

# NORMAL_INPUTS_AMP_REPLY_CXA81 = {
#     "#04,01,00" : "A1",
#     "#04,01,01" : "A2",
#     "#04,01,02" : "A3",
#     "#04,01,03" : "A4",
#     "#04,01,04" : "D1",
#     "#04,01,05" : "D2",
#     "#04,01,06" : "D3",
#     "#04,01,14" : "Bluetooth",
#     "#04,01,16" : "USB",
#     "#04,01,20" : "XLR"
# }

SOUND_MODES = {
    "A" : "#1,25,0",
    "AB" : "#1,25,1",
    "B" : "#1,25,2"
}

AMP_CMD_GET_PWSTATE = "power?"
AMP_CMD_GET_CURRENT_SOURCE = "source?"
AMP_CMD_GET_MUTE_STATE = "mute?"

AMP_CMD_SET_MUTE_ON = "mute_on!"
AMP_CMD_SET_MUTE_OFF = "mute_off!"
AMP_CMD_SET_PWR_ON = "power_on!"
AMP_CMD_SET_PWR_OFF = "power_off!"

AMP_CMD_VOL_UP = "vol_up!"
AMP_CMD_VOL_DOWN = "vol_dwn!"

AMP_REPLY_PWR_ON = "power=on$"
AMP_REPLY_PWR_STANDBY = "power=standy$"
AMP_REPLY_MUTE_ON = "mute=on$"
AMP_REPLY_MUTE_OFF = "mute=off$"

AMP_REPLY_VOL_UP = "volume=##$"
AMP_REPLY_VOL_DOWN = "volume=##$"

def setup_platform(hass, config, add_devices, discovery_info=None):
    device = config.get(CONF_DEVICE)
    name = config.get(CONF_NAME)
    roteltype = config.get(CONF_TYPE)
    rotelhost = config.get(CONF_SLAVE)

    if device is None:
        _LOGGER.error("No serial port defined in configuration.yaml for Rotel A11")
        return

    roteltype = "A11"

    add_devices([RotelA11Device(hass, device, name, roteltype, rotelhost)])


class RotelA11Device(MediaPlayerEntity):
    def __init__(self, hass, device, name, roteltype, rotelhost):
        _LOGGER.debug("Setting up Rotel A11")
        self._hass = hass
        self._device = device
        self._mediasource = "#04,01,00"
        self._speakersactive = ""
        self._muted = AMP_REPLY_MUTE_OFF
        self._name = name
        self._pwstate = ""
        self._roteltype = roteltype.upper()
        self._roteltype == "A11"
        self._source_list = NORMAL_INPUTS_A11.copy()
        self._source_reply_list = NORMAL_INPUTS_AMP_REPLY_A11.copy()
        # else:
        #     self._source_list = NORMAL_INPUTS_CXA81.copy()
        #     self._source_reply_list = NORMAL_INPUTS_AMP_REPLY_CXA81.copy()
        self._sound_mode_list = SOUND_MODES.copy()
        self._state = STATE_OFF
        self._rotelhost = rotelhost
        self._serial = Serial(device, baudrate=115200, timeout=2, bytesize=8, parity="N", stopbits=1)
        
    def update(self):
        self._pwstate = self._command_with_reply(AMP_CMD_GET_PWSTATE)
        self._mediasource = self._command_with_reply(AMP_CMD_GET_CURRENT_SOURCE)
        self._muted = self._command_with_reply(AMP_CMD_GET_MUTE_STATE)

    def _command(self, command):
        try:
            self._serial.flush()
            self._serial.write((command+"\r").encode("utf-8"))
            self._serial.flush()
        except:
            _LOGGER.error("Could not send command")
    
    def _command_with_reply(self, command):
        try:
            self._serial.write((command+"\r").encode("utf-8"))
            reply = self._serial.readline()
            return(reply.decode("utf-8")).replace("\r","")
        except:
            _LOGGER.error("Could not send command")
            return ""

    def url_command(self, command):
        urllib.request.urlopen("http://" + self._rotelhost + "/" + command).read()

    @property
    def is_volume_muted(self):
        if AMP_REPLY_MUTE_ON in self._muted:
            return True
        else:
            return False

    @property
    def name(self):
        return self._name

    @property
    def source(self):
        return self._source_reply_list[self._mediasource]

    @property
    def sound_mode_list(self):
        return sorted(list(self._sound_mode_list.keys()))

    @property
    def source_list(self):
        return sorted(list(self._source_list.keys()))

    @property
    def state(self):
        if AMP_REPLY_PWR_ON in self._pwstate:
            return STATE_ON
        else:
            return STATE_OFF

    @property
    def supported_features(self):
        # if self._rotelhost:
        #     return SUPPORT_A11_WITH_CXN
        return SUPPORT_A11

    def mute_volume(self, mute):
        if mute:
            self._command(AMP_CMD_SET_MUTE_ON)
        else:
            self._command(AMP_CMD_SET_MUTE_OFF)

    def select_sound_mode(self, sound_mode):
        self._command(self._sound_mode_list[sound_mode])

    def select_source(self, source):
        self._command(self._source_list[source])

    def turn_on(self):
        self._command(AMP_CMD_SET_PWR_ON)

    def turn_off(self):
        self._command(AMP_CMD_SET_PWR_OFF)

    def volume_up(self):
        self._command(AMP_CMD_VOL_UP)
        self
    
    def volume_down(self):
        self._command(AMP_CMD_VOL_DOWN)
        self
