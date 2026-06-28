from abc import ABC, abstractmethod


class BaseProvider(ABC):
    provider_name = "base"

    @abstractmethod
    def payin(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def payout(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def get_status(self, reference: str):
        raise NotImplementedError

    @abstractmethod
    def get_balance(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def verify_webhook(self, payload, headers) -> bool:
        raise NotImplementedError

    @abstractmethod
    def handle_webhook(self, payload, headers):
        raise NotImplementedError

    def normalize_result(self, *, success: bool, operation: str, reference: str = None, status: str = None, message: str = None, payload=None):
        return {
            "success": success,
            "provider": self.provider_name,
            "operation": operation,
            "reference": reference,
            "status": status,
            "message": message,
            "payload": payload or {},
        }
