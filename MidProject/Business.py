"""
Business.py
===========
Defines the Business class, which holds the configuration for the business
that this appointment system is running for.

By keeping all business-specific config (name, services, working hours) in
one class, the entire system can be reused for any type of business simply
by changing the values in main.py — no other file needs to change.
"""

from datetime import datetime


class Business:
    """
    Represents the business that owns this appointment system.

    Attributes:
        name (str):              Display name of the business.
        services (list[str]):    List of service types offered.
        working_hours (dict):    Dict with 'start' and 'end' keys (HH:MM strings).
        owner (str | None):      Optional name of the business owner.
    """

    def __init__(
        self,
        name: str,
        services: list,
        working_hours: dict,
        owner: str = None,
    ):
        """
        Initialize a Business instance.

        Args:
            name:           Business name, e.g. "Ron's Barbershop".
            services:       List of service names, e.g. ["Haircut", "Beard Trim"].
            working_hours:  Dict with 'start' and 'end', e.g. {"start": "09:00", "end": "18:00"}.
            owner:          Optional owner name.
        """
        self.name = name
        self.services = services
        self.working_hours = working_hours
        self.owner = owner

    def is_valid_service(self, service: str) -> bool:
        """
        Check whether 'service' is in the business's service list (case-insensitive).

        Args:
            service: The service string entered by the user.

        Returns:
            True if the service is offered, False otherwise.
        """
        return service.strip().lower() in [s.lower() for s in self.services]

    def is_within_hours(self, time_str: str) -> bool:
        """
        Check whether 'time_str' (HH:MM) falls within the business's working hours.

        Args:
            time_str: A validated time string in HH:MM format.

        Returns:
            True if the time is within working hours (inclusive), False otherwise.
        """
        fmt = "%H:%M"
        appt_time = datetime.strptime(time_str, fmt)
        start = datetime.strptime(self.working_hours["start"], fmt)
        end = datetime.strptime(self.working_hours["end"], fmt)
        return start <= appt_time <= end

    def services_display(self) -> str:
        """Return the services list as a comma-separated string for display."""
        return ", ".join(self.services)
