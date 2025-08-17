"""Translation helper for Kubernetes integration."""

from homeassistant.helpers.translation import async_get_translations


async def get_translations(hass, language: str) -> dict[str, dict[str, str]]:
    """Get translations for the integration."""
    return await async_get_translations(hass, language, "kubernetes")
