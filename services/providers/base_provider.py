class BaseProvider:

    def verify_callback(self, payload, headers):
        """
        Doit être implémenté par chaque provider
        """
        raise NotImplementedError("Signature non implémentée")
