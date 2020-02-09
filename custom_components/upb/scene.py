"""Platform for UPB link integration."""
import logging
import voluptuous as vol

from . import UpbEntity, DOMAIN, create_entity_service

from homeassistant.components.light import ATTR_BRIGHTNESS_PCT
from homeassistant.components.scene import Scene
from homeassistant.const import ATTR_ENTITY_ID
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

UPB_LINK_ACTIVATE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ENTITY_ID, default=[]): cv.entity_ids}
)
UPB_LINK_DEACTIVATE_SCHEMA = UPB_LINK_ACTIVATE_SCHEMA
UPB_LINK_GOTO_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID, default=[]): cv.entity_ids,
        vol.Required("brightness_pct"): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
        vol.Optional("rate", default=-1): vol.All(
            vol.Coerce(int), vol.Range(min=-1, max=255)
        ),
    }
)

UPB_LINK_FADE_START_SCHEMA = vol.Schema(
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

UPB_LINK_FADE_STOP_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ENTITY_ID, default=[]): cv.entity_ids}
)

UPB_LINK_BLINK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID, default=[]): cv.entity_ids,
        vol.Required("rate", default=20): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=255)
        ),
    }
)

UPB_COMMAND_TO_EVENT_MAPPING = {
    "goto": "goto",
    "activate": "activated",
    "deactivate": "deactivated",
    "blink": "blink",
    "fade_start": "fade_started",
    "fade_stop": "fade_stopped",
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the UPB scene platform."""
    if discovery_info is None:
        return

    create_entity_service(
        hass, DOMAIN, "UpbLink", "upb_link_activate", UPB_LINK_ACTIVATE_SCHEMA
    )
    create_entity_service(
        hass, DOMAIN, "UpbLink", "upb_link_deactivate", UPB_LINK_DEACTIVATE_SCHEMA
    )
    create_entity_service(
        hass, DOMAIN, "UpbLink", "upb_link_goto", UPB_LINK_GOTO_SCHEMA
    )
    create_entity_service(
        hass, DOMAIN, "UpbLink", "upb_link_fade_start", UPB_LINK_FADE_START_SCHEMA
    )
    create_entity_service(
        hass, DOMAIN, "UpbLink", "upb_link_fade_stop", UPB_LINK_FADE_STOP_SCHEMA
    )
    create_entity_service(
        hass, DOMAIN, "UpbLink", "upb_link_blink", UPB_LINK_BLINK_SCHEMA
    )

    upb = hass.data[DOMAIN]["upb"]
    async_add_entities(UpbLink(upb.links[link], upb) for link in upb.links)


class UpbLink(UpbEntity, Scene):
    """Representation of an UPB Link."""

    def __init__(self, element, upb):
        """Initialize an UpbLink."""
        super().__init__(element, upb)

    def _element_changed(self, element, changeset):
        if changeset.get("last_change") is None:
            return

        command = changeset["last_change"]["command"]
        event = f"{DOMAIN}.scene_{UPB_COMMAND_TO_EVENT_MAPPING[command]}"
        data = {"entity_id": self.entity_id}
        if command == "goto" or command == "fade_start":
            data["brightness_pct"] = changeset["last_change"]["level"]
        rate = changeset["last_change"].get("rate")
        if rate:
            data["rate"] = rate

        self.hass.bus.fire(event, data)

    async def async_activate(self):
        """Activate the task."""
        self._element.activate()

    async def upb_link_activate(self):
        """Activate the task."""
        self._element.activate()

    async def upb_link_deactivate(self):
        """Activate the task."""
        self._element.deactivate()

    async def upb_link_goto(self, brightness_pct, rate):
        """Activate the task."""
        self._element.goto(brightness_pct, rate)

    async def upb_link_fade_start(self, brightness_pct, rate):
        """Start dimming a link."""
        self._element.fade_start(brightness_pct, rate)

    async def upb_link_fade_stop(self):
        """Stop dimming a link."""
        self._element.fade_stop()

    async def upb_link_blink(self, rate):
        """Blink a link."""
        self._element.blink(rate)
