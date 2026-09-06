import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .API import TeamApp, RbfaUpdateError

_LOGGER = logging.getLogger(__name__)



class MyCoordinator(DataUpdateCoordinator):
    """Class to manage fetching RBFA data."""

    def __init__(self, hass: HomeAssistant, my_api) -> None:
        """Initialize the coordinator."""

        self.collector = TeamApp(hass, my_api)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}",
            update_interval=timedelta(minutes=15),
        )
        self.api = my_api

    async def _async_update_data(self):
        """Fetch data from the RBFA service."""
        _LOGGER.debug('fetch data coordinator')
        try:
            await self.collector.update(self.api)
        except RbfaUpdateError as exc:
            # Erreur réelle (réseau, HTTP, GraphQL) : on le signale
            # proprement au coordinator, qui marquera les entités
            # "unavailable" sans perdre les dernières données connues.
            raise UpdateFailed(str(exc)) from exc
        return self.collector.matchdata

    @property
    def collections(self):
        return self.collector.collections

    @property
    def teamdata(self):
        return self.collector.teamdata
