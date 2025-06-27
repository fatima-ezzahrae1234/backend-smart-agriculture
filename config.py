import os
from dotenv import load_dotenv

class EnvironmentConfig:
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        load_dotenv()  # Charge automatiquement les variables du .env

    def __call__(self, key: str, default=None):
        return os.getenv(key.upper(), default)

# Instance unique à utiliser partout
env = EnvironmentConfig()


