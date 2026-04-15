# models package
# All table models imported here so Base.metadata can discover them.

from models.site import Site
from models.tenant import Tenant
from models.meter import Meter
from models.meter_assignment import MeterAssignment
from models.meter_reading import MeterReading

__all__ = ["Site", "Tenant", "Meter", "MeterAssignment", "MeterReading"]
