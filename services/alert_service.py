import logging

logger = logging.getLogger("africachange.alerts")


class AlertService:

    @staticmethod
    def critical(message):
        logger.critical(message)
        # futur : email / Slack / SMS

    @staticmethod
    def warning(message):
        logger.warning(message)

    @staticmethod
    def info(message):
        logger.info(message)
