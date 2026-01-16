from deploy_assistant.git.load import Loader
from deploy_assistant.config.constants import CONFIG_FILE
from deploy_assistant.elements.listview.listview import CollapsibleListViewApp


def main():
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
