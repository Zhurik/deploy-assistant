import yaml


class Config:
    def __init__(self, config_path: str) -> None:
        try:
            with open(config_path, "r") as file:
                data = yaml.safe_load(file)
            self.services = data["services"] if data and "services" in data else []
        except FileNotFoundError:
            self.services = []
