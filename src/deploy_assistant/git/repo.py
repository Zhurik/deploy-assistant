import os
import subprocess
import time
import requests
from typing import Optional


class LocalRepo:
    def __init__(self, local_path: str, name: str) -> None:
        self.local_path = local_path
        self.name = name
        self.modified_commit_messages: Optional[str] = None
        self.pipeline_status: Optional[str] = None
        self.pipeline_url: Optional[str] = None
        self.gitlab_project_id: Optional[int] = None
        self.gitlab_addr: Optional[str] = None
        self.gitlab_token: Optional[str] = None
        self.version: str = ""
        self.commits_ahead: int = 0
        self.commit_messages: str = ""

    def set_gitlab_config(self, addr: str, token: str, project_id: int) -> None:
        """Set GitLab configuration for this repository."""
        self.gitlab_addr = addr
        self.gitlab_token = token
        self.gitlab_project_id = project_id

    def fetch_pipeline_status(self) -> None:
        """Fetch pipeline status for the version tag from GitLab API."""
        if not self.gitlab_addr:
            self.pipeline_status = "GitLab config not set"
            return

        if not self.gitlab_project_id or not self.version:
            self.pipeline_status = "Project ID or version not set"
            return

        try:
            headers = {"PRIVATE-TOKEN": self.gitlab_token}
            url = f"https://{self.gitlab_addr}/api/v4/projects/{self.gitlab_project_id}/pipelines"

            # Get pipelines for the version tag
            params = {"ref": self.version, "per_page": 1}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            pipelines = response.json()
            if pipelines:
                pipeline = pipelines[0]
                self.pipeline_status = pipeline["status"]
                self.pipeline_url = pipeline["web_url"]
            else:
                self.pipeline_status = "No pipeline found"
                self.pipeline_url = None

        except requests.exceptions.RequestException as e:
            self.pipeline_status = f"Error: {str(e)}"
            self.pipeline_url = None
        except Exception as e:
            self.pipeline_status = f"Error: {str(e)}"
            self.pipeline_url = None

    def get_data(self) -> None:
        original_cwd = os.getcwd()
        try:
            os.chdir(self.local_path)
            subprocess.run(["git", "checkout", "main"], check=True, capture_output=True)
            subprocess.run(["git", "pull"], check=True, capture_output=True)
            last_tag_result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.version = last_tag_result.stdout.strip()

            # Подсчет количества коммитов после последнего тега
            commits_ahead_result = subprocess.run(
                ["git", "rev-list", "--count", f"{self.version}..HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.commits_ahead = int(commits_ahead_result.stdout.strip())

            # Получение сообщений коммитов между последним тегом и HEAD
            commit_messages_result = subprocess.run(
                [
                    "git",
                    "log",
                    "--oneline",
                    '--pretty=format:"%s"',
                    f"{self.version}..HEAD",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            raw_commit_messages = commit_messages_result.stdout.strip()

            # Убираем кавычки с каждой строки
            lines = raw_commit_messages.split("\n")
            cleaned_lines = [line.strip('"') for line in lines if line]
            self.commit_messages = "\n".join(cleaned_lines)

        finally:
            os.chdir(original_cwd)

    def deploy(self) -> None:
        """Deploy the repository by creating and pushing a new tag."""
        original_cwd = os.getcwd()
        try:
            os.chdir(self.local_path)

            # Определяем сообщение для тега
            tag_message = (
                self.modified_commit_messages
                if self.modified_commit_messages is not None
                else self.commit_messages
            )

            # Создаем новый тег с сообщением
            subprocess.run(
                ["git", "tag", "-a", self.new_version, "-m", tag_message],
                check=True,
                capture_output=True,
                text=True,
            )

            # Пушим тег
            subprocess.run(
                ["git", "push", "origin", self.new_version],
                check=True,
                capture_output=True,
                text=True,
            )

        finally:
            os.chdir(original_cwd)

    @property
    def new_version(self) -> str:
        version_parts = self.version.split(".")
        new_last_digit = int(version_parts[-1]) + 1
        new_version_parts = version_parts[:-1] + [str(new_last_digit)]
        return ".".join(new_version_parts)
