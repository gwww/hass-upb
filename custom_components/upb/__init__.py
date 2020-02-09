"""Support the UPB lighting system."""
import logging
import upb_lib
import voluptuous as vol

from homeassistant.const import ATTR_ENTITY_ID, CONF_FILE_PATH, CONF_URL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import ConfigType


DOMAIN = "upb"
CONF_FLAGS = "flags"
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_URL): cv.string,
                vol.Optional(CONF_FILE_PATH, default=""): cv.string,
                vol.Optional(CONF_FLAGS, default=""): cv.string,
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
            "flags": conf[CONF_FLAGS],
        }
    )
    upb.connect()
    hass.data[DOMAIN] = {"upb": upb}

    init_entity_service(hass, DOMAIN)

    for component in ["light", "scene"]:
        hass.async_create_task(
            discovery.async_load_platform(hass, component, DOMAIN, {}, hass_config)
        )
    return True


class UpbEntity(Entity):
    """Base class for all UPB entities."""

    def __init__(self, element, upb):
        """Initialize the base of all UPB devices."""
        self._upb = upb
        self._element = element
        self._unique_id = f"{self.__class__.__name__.lower()}_{element.index}"
        _LOGGER.debug(f"'{element.name}' created, unique_id {self._unique_id}")

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
        connect_entity_services(DOMAIN, self.__class__.__name__, self)


def init_entity_service(hass, domain):
    """Initialize entity service helpers."""
    hass.data[domain]["services"] = {}


def create_entity_service(hass, domain, platform, service_name, schema):
    """Register a service and save it for connecting later."""

    def _handle_service_call(service):
        entity_ids = service.data.get(ATTR_ENTITY_ID, [])
        for entity_id in entity_ids:
            async_dispatcher_send(
                hass, f"SIGNAL_{service.service}_{entity_id}", service.data
            )

    services = hass.data[domain]["services"]
    service_key = (domain, platform)
    if services.get(service_key) is None:
        services[service_key] = []
    services[service_key].append(service_name)

    hass.services.async_register(domain, service_name, _handle_service_call, schema)


def connect_entity_services(domain, platform, entity):
    """Connect to saved services."""

    def wrapped_service_method(method):
        async def wrapper(data):
            args = {k: v for k, v in data.items() if k != ATTR_ENTITY_ID}
            await method(**args)

        return wrapper

    services = entity.hass.data[domain]["services"]
    service_names = services.get((domain, platform), [])
    for service_name in service_names:
        service_method = wrapped_service_method(getattr(entity, service_name))
        async_dispatcher_connect(
            entity.hass, f"SIGNAL_{service_name}_{entity.entity_id}", service_method
        )
