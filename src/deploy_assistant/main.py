from deploy_assistant.git.load import Loader
from deploy_assistant.config.constants import CONFIG_FILE
from deploy_assistant.elements.listview.listview import CollapsibleListViewApp


def main():
    repos = Loader.initialize_repos(CONFIG_FILE)
    app = CollapsibleListViewApp(repos)
    app.run()


if __name__ == "__main__":
    main()
