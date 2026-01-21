from deploy_assistant.git.load import Loader
from deploy_assistant.config.constants import CONFIG_FILE
from deploy_assistant.config.config import Config
from deploy_assistant.elements.listview.listview import CollapsibleListViewApp
import threading


def update_pipeline_statuses(repos, gitlab_addr, gitlab_token, app):
    """Update pipeline statuses for all repositories."""
    for repo in repos:
        # Устанавливаем конфигурацию GitLab для каждого репозитория
        if hasattr(repo, "project_id") and repo.project_id is not None:
            repo.set_gitlab_config(gitlab_addr, gitlab_token, repo.project_id)
            repo.fetch_pipeline_status()
        elif hasattr(repo, "gitlab_project_id") and repo.gitlab_project_id is not None:
            repo.set_gitlab_config(gitlab_addr, gitlab_token, repo.gitlab_project_id)
            repo.fetch_pipeline_status()

    # Обновляем отображение в UI
    if hasattr(app, "refresh_pipeline_statuses"):
        app.refresh_pipeline_statuses()


def main():
    config = Config(CONFIG_FILE)
    repos = Loader.initialize_repos(CONFIG_FILE)
    app = CollapsibleListViewApp(repos)

    if config.gitlab_addr and config.gitlab_token:
        pipeline_thread = threading.Thread(
            target=update_pipeline_statuses,
            args=(repos, config.gitlab_addr, config.gitlab_token, app),
            daemon=True,
        )
        pipeline_thread.start()

    app.run()


if __name__ == "__main__":
    main()
