import unittest

from providers.factory import ProviderFactory
from providers.registry import ProviderRegistry


class ProviderRegistryTestCase(unittest.TestCase):
    def test_senepay_provider_is_registered(self):
        self.assertIn("senepay", ProviderRegistry.list_names())

    def test_factory_creates_registered_provider(self):
        provider = ProviderFactory.create("senepay")
        self.assertEqual(provider.provider_name, "senepay")

    def test_provider_exposes_common_interface(self):
        provider = ProviderFactory.create("senepay")
        payin_result = provider.payin(reference="PAYIN-1", amount=1000)
        payout_result = provider.payout(reference="PAYOUT-1", amount=1000)
        balance_result = provider.get_balance()

        self.assertEqual(payin_result["operation"], "payin")
        self.assertEqual(payout_result["operation"], "payout")
        self.assertEqual(balance_result["operation"], "balance")


if __name__ == "__main__":
    unittest.main()
