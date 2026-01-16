from tqdm import tqdm

from deploy_assistant.git import LocalRepo
from deploy_assistant.config.config import Config
from deploy_assistant.elements.listview.listview import CollapsibleListViewApp

def main():
    config = Config()

    repos = []
    for service in tqdm(config.services):
        repo = LocalRepo(
            local_path=service["local_path"],
            name=service["name"],
        )
        repo.get_data()
        repos.append(repo)

    app = CollapsibleListViewApp(repos)
    app.run()


if __name__ == "__main__":
    main()
