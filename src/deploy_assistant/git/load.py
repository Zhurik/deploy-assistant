from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from typing import List, Optional

from .repo import LocalRepo
from deploy_assistant.config.config import Config


def process_repo_standalone(
    local_path: str, name: str, project_id: Optional[int] = None
):
    """Process a single repository in a separate process."""
    repo = LocalRepo(
        local_path=local_path,
        name=name,
        project_id=project_id,
    )
    repo.get_data()
    return repo


class Loader:
    @classmethod
    def initialize_repos(
        cls, config_file_path: Optional[str] = None
    ) -> List[LocalRepo]:
        """Initialize repositories from config file."""
        config = Config(config_file_path)

        repos_data = []
        with ProcessPoolExecutor(max_workers=4) as executor:
            future_to_service = {
                executor.submit(
                    process_repo_standalone,
                    service["local_path"],
                    service["name"],
                    service.get("id"),
                ): service
                for service in config.services
            }

            with tqdm(
                total=len(config.services), desc="Processing repositories"
            ) as progress_bar:
                for future in as_completed(future_to_service):
                    try:
                        repo_data = future.result()
                        repos_data.append(repo_data)
                        progress_bar.update(1)
                    except Exception as exc:
                        service = future_to_service[future]
                        print(
                            f"Service {service['name']} generated an exception: {exc}"
                        )
                        progress_bar.update(1)

        return repos_data
