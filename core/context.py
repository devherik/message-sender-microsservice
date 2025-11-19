"""
Global context module.
"""


class GlobalContext:
    """
    A class to manage global context settings.
    """

    def __init__(self):
        self.settings = {}

    def set(self, key, value):
        """
        Set a context setting.

        :param key: The setting key.
        :param value: The setting value.
        """
        self.settings[key] = value

    def get(self, key, default=None):
        """
        Get a context setting.

        :param key: The setting key.
        :param default: The default value if the key is not found.
        :return: The setting value or default.
        """
        return self.settings.get(key, default)

    def remove(self, key):
        """
        Remove a context setting.

        :param key: The setting key to remove.
        """
        if key in self.settings:
            del self.settings[key]

    def clear(self):
        """
        Clear all context settings.
        """
        self.settings.clear()


global_context = GlobalContext()
