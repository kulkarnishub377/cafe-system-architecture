from django.apps import AppConfig


class CafeConfig(AppConfig):
    """App configuration for the cafe application."""

    name = 'cafe'

    def ready(self) -> None:
        """Connect signal handlers when the app registry is fully populated."""
        import cafe.signals  # noqa: F401 – registers signal receivers
