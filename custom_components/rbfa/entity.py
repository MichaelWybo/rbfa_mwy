"""Base entity for the RBFA integration."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MyCoordinator


def _team_display_name(entry, coordinator, team: str) -> str:
    """Return the friendly device name for a team.

    Prefers a user-provided alternative name, then the club/team name
    reported by the RBFA API, and finally falls back to the raw team id
    (e.g. right after setup, before the first refresh has populated
    ``teamdata``).
    """
    if 'alt_name' in entry.options:
        return entry.options['alt_name']
    if 'alt_name' in entry.data:
        return entry.data['alt_name']
    teamdata = getattr(coordinator, 'teamdata', None)
    if teamdata:
        return f"{teamdata['clubName']} | {teamdata['name']}"
    return team


class RbfaEntity(CoordinatorEntity[MyCoordinator]):
    """Base class for RBFA entities.

    Groups every entity created for a given team (sensors + calendar) under
    a single Home Assistant device, so they can be viewed, renamed and
    managed together from Settings > Devices & services.
    """

    _attr_has_entity_name = True

    def __init__(self, coordinator: MyCoordinator, entry) -> None:
        """Initialize a RBFA entity."""
        super().__init__(coordinator=coordinator)
        self.entry = entry
        self.team = entry.data['team']
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.team)},
            name=_team_display_name(entry, coordinator, self.team),
            manufacturer="RBFA",
            model="Team",
        )
