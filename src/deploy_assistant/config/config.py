import yaml


class Config:
    def __init__(self, config_path: str) -> None:
        try:
            with open(config_path, "r") as file:
                data = yaml.safe_load(file)
            self.services = data["services"] if data and "services" in data else []
            self.gitlab_addr = data.get("gitlab", {}).get("addr") if data else None
            self.gitlab_token = data.get("gitlab", {}).get("token") if data else None
        except FileNotFoundError:
            self.services = []
            self.gitlab_addr = None
            self.gitlab_token = None
