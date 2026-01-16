from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import os

from deploy_assistant.git import LocalRepo
from deploy_assistant.config.config import Config
from deploy_assistant.elements.listview.listview import CollapsibleListViewApp


def process_repo_standalone(local_path, name):
    """Process a single repository in a separate process."""
    repo = LocalRepo(
        local_path=local_path,
        name=name,
    )
    repo.get_data()
    # Return serializable data instead of the repo object
    return {
        "name": repo.name,
        "local_path": repo.local_path,
        "version": getattr(repo, "version", ""),
        "commits_ahead": getattr(repo, "commits_ahead", 0),
        "commit_messages": getattr(repo, "commit_messages", ""),
    }


def main():
    config = Config()

    repos_data = []
    with ProcessPoolExecutor(max_workers=4) as executor:
        # Submit all tasks
        future_to_service = {
            executor.submit(
                process_repo_standalone, service["local_path"], service["name"]
            ): service
            for service in config.services
        }

        # Collect results in order with progress bar
        with tqdm(total=len(config.services), desc="Processing repositories") as pbar:
            for future in as_completed(future_to_service):
                try:
                    repo_data = future.result()
                    repos_data.append(repo_data)
                    pbar.update(1)
                except Exception as exc:
                    service = future_to_service[future]
                    print(f"Service {service['name']} generated an exception: {exc}")
                    pbar.update(1)

    # Sort repos to match the original order from config
    service_names = [service["name"] for service in config.services]
    repos_data.sort(key=lambda r: service_names.index(r["name"]))

    # Recreate repo objects from data
    repos = []
    for data in repos_data:
        repo = LocalRepo(local_path=data["local_path"], name=data["name"])
        repo.version = data["version"]
        repo.commits_ahead = data["commits_ahead"]
        repo.commit_messages = data["commit_messages"]
        repos.append(repo)

    app = CollapsibleListViewApp(repos)
    app.run()


if __name__ == "__main__":
    main()
