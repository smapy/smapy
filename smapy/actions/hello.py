from smapy.action import BaseAction


class World(BaseAction):
    """Test to check API connection, Returns Hello World"""

    def process(self, message):
        self.logger.info("Hello world!")
        message["hello"] = "world!"
