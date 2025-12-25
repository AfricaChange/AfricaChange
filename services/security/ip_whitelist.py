import ipaddress
from flask import current_app

class IPWhitelist:

    PROVIDERS = {
        "orange": [
            "196.201.200.0/24",
            "196.201.201.0/24",
        ],
        "wave": [
            "41.203.216.0/22",
        ],
    }

    @staticmethod
    def is_allowed(provider: str, ip: str) -> bool:
        # 🧪 Mode DEV / local
        if current_app.debug:
            return True

        try:
            ip_obj = ipaddress.ip_address(ip)
        except ValueError:
            return False

        networks = IPWhitelist.PROVIDERS.get(provider.lower(), [])
        for net in networks:
            if ip_obj in ipaddress.ip_network(net):
                return True

        return False
