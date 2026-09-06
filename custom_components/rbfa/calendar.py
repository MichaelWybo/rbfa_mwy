import logging
from datetime import datetime, timedelta
from typing import Optional, List

from homeassistant.core import HomeAssistant
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const       import DOMAIN
from .coordinator import MyCoordinator
from .entity      import RbfaEntity


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RBFA sensor based on a config entry."""
    coordinator: MyCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [TeamCalendar(
            coordinator,
            entry,
        )]
    )

class TeamCalendar(RbfaEntity, CalendarEntity):
    """Defines a RBFA Team Calendar."""

    _attr_icon = "mdi:soccer"

    def __init__(
        self,
        coordinator,
        config,
    ) -> None:
        """Initialize the RBFA Team entity."""
        super().__init__(coordinator)
        self.config = config
        team = config.data['team']
        _LOGGER.debug('team: %r', team)
        self._attr_unique_id = f"{DOMAIN}_calendar_{team}"
        # Garde l'entity_id stable quelle que soit la langue de Home
        # Assistant (même logique que dans sensor.py).
        self._attr_suggested_object_id = f"{team}"

        self._event = None

    @property
    def name(self) -> str:
        """Return the display name of the calendar.

        Calculé comme une vraie property (et non plus en effet de bord
        dans `event` comme avant) afin d'être disponible dès l'ajout de
        l'entité, sans dépendre du fait que `event` ait déjà été lu.
        """
        if 'alt_name' in self.config.options:
            return self.config.options['alt_name']
        if 'alt_name' in self.config.data:
            return self.config.data['alt_name']
        if self.coordinator.teamdata:
            return f"{self.coordinator.teamdata['clubName']} | {self.coordinator.teamdata['name']}"
        return self.config.data['team']

    @property
    def event(self) -> Optional[CalendarEvent]:
        """Return the next upcoming event."""

        upcoming = self.coordinator.data['upcoming']

        if upcoming != None:
            return CalendarEvent(
                uid         = upcoming['matchid'],
                summary     = upcoming['hometeam'] + ' - ' + upcoming['awayteam'],
                start       = upcoming['starttime'],
                end         = upcoming['endtime'],
                location    = upcoming['location'],
                description = upcoming['series'],
            )

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        """Return calendar events"""
        events: List[CalendarEvent] = []

        _LOGGER.debug("count: %r", len(self.coordinator.collections))
        for team_items in self.coordinator.collections:

            if start_date.date() <= team_items['starttime'].date() <= end_date.date():

                # Summary below will define the name of event in calendar
                events.append(
                    CalendarEvent(
                        uid         = team_items['uid'],
                        summary     = team_items['summary'],
                        start       = team_items['starttime'],
                        end         = team_items['endtime'],
                        location    = team_items['location'],
                        description = team_items['description'],
                    )
                )

        return events
