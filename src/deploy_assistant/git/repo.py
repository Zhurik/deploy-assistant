import os
import subprocess


class LocalRepo:
    def __init__(self, local_path: str, name: str) -> None:
        self.local_path = local_path
        self.name = name
        self.modified_commit_messages = None

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
