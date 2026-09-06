
from __future__ import annotations
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import MyCoordinator


class RbfaEntity(CoordinatorEntity[MyCoordinator]):
    """Base class for RBFA entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MyCoordinator) -> None:
        """Initialize a RBFA entity."""
        super().__init__(coordinator=coordinator)
