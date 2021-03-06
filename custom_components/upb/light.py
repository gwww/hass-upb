"""Platform for UPB light integration."""
import logging

import voluptuous as vol

from . import UpbEntity, DOMAIN, create_entity_service

from homeassistant.const import ATTR_ENTITY_ID
import homeassistant.helpers.config_validation as cv

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_BRIGHTNESS_PCT,
    ATTR_FLASH,
    ATTR_TRANSITION,
    SUPPORT_BRIGHTNESS,
    SUPPORT_FLASH,
    SUPPORT_TRANSITION,
    Light,
)

_LOGGER = logging.getLogger(__name__)

LIGHT_FADE_START_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID, default=[]): cv.entity_ids,
        vol.Required(ATTR_BRIGHTNESS_PCT): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
        vol.Optional("rate", default=-1): vol.All(
            vol.Coerce(int), vol.Range(min=-1, max=255)
        ),
    }
)

LIGHT_FADE_STOP_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ENTITY_ID, default=[]): cv.entity_ids}
)

LIGHT_BLINK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID, default=[]): cv.entity_ids,
        vol.Required("rate", default=20): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=255)
        ),
    }
)

LIGHT_UPDATE_STATUS_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ENTITY_ID, default=[]): cv.entity_ids}
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the UPB light platform."""
    if discovery_info is None:
        return

    upb = hass.data[DOMAIN]["upb"]
    async_add_entities(UpbLight(upb.devices[dev], upb) for dev in upb.devices)

    create_entity_service(
        hass, DOMAIN, "UpbLight", "light_fade_start", LIGHT_FADE_START_SCHEMA
    )
    create_entity_service(
        hass, DOMAIN, "UpbLight", "light_fade_stop", LIGHT_FADE_STOP_SCHEMA
    )
    create_entity_service(hass, DOMAIN, "UpbLight", "light_blink", LIGHT_BLINK_SCHEMA)
    create_entity_service(
        hass, DOMAIN, "UpbLight", "light_update_status", LIGHT_UPDATE_STATUS_SCHEMA
    )


class UpbLight(UpbEntity, Light):
    """Representation of an UPB Light."""

    def __init__(self, element, upb):
        """Initialize an UpbLight."""
        super().__init__(element, upb)
        self._brightness = self._element.status

    @property
    def supported_features(self):
        """Flag supported features."""
        if self._element.dimmable:
            return SUPPORT_BRIGHTNESS | SUPPORT_TRANSITION | SUPPORT_FLASH
        return SUPPORT_FLASH

    @property
    def brightness(self):
        """Get the brightness."""
        return self._brightness

    @property
    def is_on(self) -> bool:
        """Get the current brightness."""
        return self._brightness != 0

    async def async_turn_on(self, **kwargs):
        """Turn on the light."""
        flash = kwargs.get(ATTR_FLASH)
        if flash:
            if flash == "short":
                self._element.blink(50)
            else:
                self._element.blink(100)
        else:
            rate = kwargs.get(ATTR_TRANSITION, -1)
            brightness = round(kwargs.get(ATTR_BRIGHTNESS, 255) / 2.55)
            self._element.turn_on(brightness, rate)

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        rate = kwargs.get(ATTR_TRANSITION, -1)
        self._element.turn_off(rate)

    async def light_fade_start(self, brightness_pct, rate):
        """Start dimming a light."""
        self._element.fade_start(brightness_pct, rate)

    async def light_fade_stop(self):
        """Stop dimming a light."""
        self._element.fade_stop()

    async def light_blink(self, rate):
        """Blink a light."""
        self._element.blink(rate)

    async def light_update_status(self):
        """Update the status of a light."""
        self._element.update_status()

    def _element_changed(self, element, changeset):
        status = self._element.status
        if status is None:
            self._brightness = 0
        else:
            self._brightness = round(status * 2.55)
