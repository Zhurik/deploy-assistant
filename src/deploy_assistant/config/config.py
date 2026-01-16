import yaml
from .constants import CONFIG_FILE


class Config:
    def __init__(self) -> None:
        try:
            with open(CONFIG_FILE, "r") as file:
                data = yaml.safe_load(file)
            self.services = data["services"] if data and "services" in data else []
        except FileNotFoundError:
            self.services = []
