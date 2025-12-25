class ProviderHealth:
    FAIL_LIMIT = 5
    TIMEOUT = 300  # secondes

    @staticmethod
    def allow(provider):
        # à brancher sur Redis plus tard
        return True
