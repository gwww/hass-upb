"""Platform for UPB link integration."""
import logging
import voluptuous as vol

from . import UpbEntity, DOMAIN, create_entity_service, connect_entity_services

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

        data = {"entity_id": self.entity_id}
        command = changeset["last_change"]["command"]
        if command == "goto":
            event = f"{DOMAIN}.scene_{command}"
            data["level"] = changeset["last_change"]["level"]
            rate = changeset["last_change"].get("rate")
            if rate:
                data["rate"] = rate
        else:
            event = f"{DOMAIN}.scene_{command}d"

        self.hass.bus.fire(event, data)

    async def async_activate(self):
        """Activate the task."""
        self._element.activate()

    async def upb_link_activate(self, data):
        """Activate the task."""
        self._element.activate()

    async def upb_link_deactivate(self, data):
        """Activate the task."""
        self._element.deactivate()

    async def upb_link_goto(self, data):
        """Activate the task."""
        self._element.goto(data["brightness_pct"], data["rate"])
