"""Support the UPB lighting system."""
import logging
import re

import upb_lib
import voluptuous as vol

from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, PLATFORM_SCHEMA, Light)
from homeassistant.const import CONF_FILE_PATH, CONF_URL

DOMAIN = "upb"

_LOGGER = logging.getLogger(__name__)

SUPPORTED_DOMAINS = [
    "light",
]

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Optional(CONF_FILE_PATH, default=None): cv.string,
})

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_URL): cv.string,
                vol.Optional(CONF_FILE_PATH, default=None): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, hass_config: ConfigType) -> bool:
    """Set up the UPB platform."""
    conf = hass_config[DOMAIN]

    upb = upb_lib.UpbPim(
        {
            "url": conf[CONF_URL],
            "UPStartExportFile": conf[CONF_FILE_PATH],
        }
    )
    upb.connect()

    hass.data[DOMAIN] = {"upb": upb}
    for component in SUPPORTED_DOMAINS:
        hass.async_create_task(
            discovery.async_load_platform(hass, component, DOMAIN, {}, hass_config)
        )

    return True


# def create_upb_entities(upb_data, upb_elements, element_type, class_, entities):
#     """Create the UPB devices of a particular class."""
#     if upb_data["config"][element_type]["enabled"]:
#         upb = upb_data["upb"]
#         _LOGGER.debug("Creating upb entities for %s", upb)
#         for element in upb_elements:
#             if upb_data["config"][element_type]["included"][element.index]:
#                 entities.append(class_(element, upb, upb_data))
#     return entities


class UpbEntity(Entity):
    """Base class for all UPB entities."""

    def __init__(self, element, upb):
        """Initialize the base of all UPB devices."""
        self._upb = upb
        self._element = element
        self._unique_id = "{}_{}".format(
            self.__class__.__name__.lower(), element.index)
        _LOGGER.debug("'{}' created, unique_id {}".format(
            element.name, self._unique_id))

    @property
    def name(self):
        """Name of the element."""
        return self._element.name

    @property
    def unique_id(self):
        """Return unique id of the element."""
        return self._unique_id

    @property
    def should_poll(self) -> bool:
        """Don't poll this device."""
        return False

    @property
    def device_state_attributes(self):
        """Return the default attributes of the element."""
        return {**self._element.as_dict(), **self.initial_attrs()}

    @property
    def available(self):
        """Is the entity available to be updated."""
        return self._upb.is_connected()

    def initial_attrs(self):
        """Return the underlying element's attributes as a dict."""
        attrs = {}
        return attrs

    def _element_changed(self, element, changeset):
        pass

    @callback
    def _element_callback(self, element, changeset):
        """Handle callback from an UPB element that has changed."""
        self._element_changed(element, changeset)
        self.async_schedule_update_ha_state(True)

    async def async_added_to_hass(self):
        """Register callback for UPB changes and update entity state."""
        self._element.add_callback(self._element_callback)
        self._element_callback(self._element, {})
