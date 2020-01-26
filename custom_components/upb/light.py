"""Platform for UPB light integration."""
import logging

import upb_lib
import voluptuous as vol

from . import UpbEntity, DOMAIN

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_TRANSITION,
    SUPPORT_BRIGHTNESS,
    SUPPORT_FLASH,
    SUPPORT_TRANSITION,
    Light,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the UPB light platform."""
    if discovery_info is None:
        return

    upb = hass.data[DOMAIN]["upb"]
    async_add_entities(UpbLight(upb.lights[light], upb) for light in upb.lights)
    async_add_entities(UpbLink(upb.links[link], upb) for link in upb.links)


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
            return SUPPORT_BRIGHTNESS | SUPPORT_TRANSITION
        return 0

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
        rate = kwargs.get(ATTR_TRANSITION, -1)
        brightness = round(kwargs.get(ATTR_BRIGHTNESS, 255) / 2.55)
        self._element.turn_on(brightness, rate)

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        rate = kwargs.get(ATTR_TRANSITION, -1)
        self._element.turn_off(rate)

    def _element_changed(self, element, changeset):
        status = self._element.status
        self._brightness = round(status * 2.55)


class UpbLink(UpbEntity, Light):
    """Representation of an UPB Light."""

    def __init__(self, element, upb):
        """Initialize an UpbLight."""
        super().__init__(element, upb)
        self._brightness = self._element.status

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS | SUPPORT_TRANSITION

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
        rate = kwargs.get(ATTR_TRANSITION, -1)
        brightness = round(kwargs.get(ATTR_BRIGHTNESS, -2.55) / 2.55)
        self._element.turn_on(brightness, rate)

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        self._element.deactivate()

    def _element_changed(self, element, changeset):
        status = self._element.status
        self._brightness = round(status * 2.55)
