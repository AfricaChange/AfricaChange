"""Legacy payment-route provider contract.

This contract remains separate from `providers.base_provider` because the
historical Orange/Wave route integrations still use a narrower callback-focused
interface than the canonical provider registry.
"""


class BaseProvider:
    """Minimal callback verification contract for legacy route providers."""

    def verify_callback(self, payload, headers):
        """Validate a legacy callback payload."""
        raise NotImplementedError("Signature non implementee")
