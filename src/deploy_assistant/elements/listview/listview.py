from textual.app import App, ComposeResult
from textual.widgets import (
    ListView,
    ListItem,
    Collapsible,
    Footer,
    Header,
    TextArea,
    Label,
)
from textual.reactive import reactive
from deploy_assistant.git import LocalRepo
from deploy_assistant.elements.modal.modal import SelectedItemsScreen

from deploy_assistant.git import LocalRepo
from deploy_assistant.elements.modal.modal import SelectedItemsScreen


class CollapsibleListViewApp(App):
    """Список, который схлопывается и редачится."""

    CSS_PATH = "listview.tcss"

    BINDINGS = [
        ("q", "quit", "Выход"),
        ("space", "toggle_collapsible", "Раскрыть элемент"),
        ("d", "display_selected", "Деплой"),
        ("a", "toggle_all", "Выбрать все"),
        ("e", "collapse_or_expand(False)", "Раскрыть все"),
        ("c", "collapse_or_expand(True)", "Схлопнуть все"),
    ]

    def __init__(self, services: list[LocalRepo]):
        self.services = services
        self.selected_items = set()
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create the layout."""
        yield Footer()
        yield Header()

        repo_info_list = []
        max_name_len = 0
        max_version_len = 0
        max_commits_len = 0

        for service in self.services:
            # Get repository info
            repo_info_list.append(
                (
                    service.name,
                    service.version,
                    service.commits_ahead,
                    service.commit_messages,
                    getattr(service, "pipeline_status", None),
                    getattr(service, "pipeline_url", None),
                ),
            )

            # Track maximum lengths for alignment
            max_name_len = max(max_name_len, len(service.name))
            max_version_len = max(max_version_len, len(service.version))
            max_commits_len = max(max_commits_len, len(str(service.commits_ahead)))

        # Create collapsible items with service data
        items = []
        for i, (
            name,
            version,
            commits_ahead,
            commit_messages,
            pipeline_status,
            pipeline_url,
        ) in enumerate(repo_info_list):
            # Create formatted title with aligned columns
            padded_name = name.ljust(max_name_len)
            padded_version = version.ljust(max_version_len)
            padded_commits = str(commits_ahead).rjust(max_commits_len)

            # Add pipeline status to title if available
            title_parts = [f"{padded_name} | {padded_version} | {padded_commits}"]
            if pipeline_status:
                title_parts.append(f" | Pipeline: {pipeline_status}")

            title_text = "".join(title_parts)

            # Create content with both commit messages and pipeline info
            content_widgets = []

            # Add commit messages
            commit_text_area = TextArea(
                commit_messages, id=f"commit-messages-{i}", language="markdown"
            )
            commit_text_area.styles.height = 10
            commit_text_area.read_only = False
            content_widgets.append(Label("Commit Messages:"))
            content_widgets.append(commit_text_area)

            # Add pipeline info if available
            if pipeline_status is not None:
                pipeline_info = f"Pipeline Status: {pipeline_status}"
                if pipeline_url:
                    pipeline_info += f"\nPipeline URL: {pipeline_url}"
                pipeline_label = Label(pipeline_info)
                pipeline_label.styles.margin = (1, 0, 0, 0)

                # Add CSS class based on pipeline status
                if pipeline_status.lower() == "success":
                    pipeline_label.add_class("pipeline-success")
                elif pipeline_status.lower() == "failed":
                    pipeline_label.add_class("pipeline-failed")
                elif pipeline_status.lower() in ["running", "pending"]:
                    pipeline_label.add_class("pipeline-running")

                content_widgets.append(Label("Pipeline Info:"))
                content_widgets.append(pipeline_label)

            collapsible = Collapsible(
                *content_widgets,
                collapsed=True,
                title=title_text,
            )

            if int(commits_ahead) == 0:
                collapsible.add_class("clean")

            list_item = ListItem(collapsible, id=f"item-{i}")
            items.append(list_item)

        # Create the ListView with all items
        list_view = ListView(*items, id="main-list-view")

        yield list_view

    def on_mount(self) -> None:
        self.title = "Deploy Assistant"
        self.sub_title = "Раскатим все вдвое быстрее"

    """
    Collapse actions
    """

    def action_toggle_collapsible(self) -> None:
        """Toggle the currently highlighted collapsible item."""
        list_view = self.query_one(ListView)
        if list_view.highlighted_child is not None:
            collapsible = list_view.highlighted_child.query_one(Collapsible)
            if collapsible is not None:
                collapsible.collapsed = not collapsible.collapsed

    def action_collapse_or_expand(self, expand: bool) -> None:
        """Expand all collapsible items."""
        list_view = self.query_one(ListView)
        if list_view is not None:
            for item in list_view.children:
                if item is not None:
                    collapsible = item.query_one(Collapsible)
                    if collapsible is not None:
                        collapsible.collapsed = expand

    """
    Select actions
    """

    def action_toggle_all(self) -> None:
        """Toggle selection of all items."""
        list_view = self.query_one(ListView)
        if list_view is None:
            return

        all_selected = len(self.selected_items) == len(self.services)

        self.selected_items.clear()

        for item in list_view.children:
            if item is not None:
                try:
                    collapsible = item.query_one(Collapsible)
                    if collapsible is not None:
                        collapsible.remove_class("selected")
                except Exception:
                    pass

        if not all_selected:
            for service in self.services:
                self.selected_items.add(service)

            for item in list_view.children:
                if item is not None:
                    try:
                        collapsible = item.query_one(Collapsible)
                        if collapsible is not None:
                            collapsible.add_class("selected")
                    except Exception:
                        pass

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Called when an item in the ListView is selected."""
        # Проверяем, что item не None
        if event.item is None:
            return

        # Проверяем, что item.id не None
        if event.item.id is None:
            return

        item_id = event.item.id
        item_index = int(item_id.split("-")[-1])

        if self.services[item_index] in self.selected_items:
            self.selected_items.remove(self.services[item_index])
            # Получаем collapsible через query, проверяя на None
            try:
                collapsible = event.item.query_one(Collapsible)
                if collapsible is not None:
                    collapsible.remove_class("selected")
            except Exception:
                # Если не удалось получить collapsible, просто продолжаем
                pass
        else:
            self.selected_items.add(self.services[item_index])
            # Получаем collapsible через query, проверяя на None
            try:
                collapsible = event.item.query_one(Collapsible)
                if collapsible is not None:
                    collapsible.add_class("selected")
            except Exception:
                # Если не удалось получить collapsible, просто продолжаем
                pass

    """
    Text actions
    """

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text area content changes."""
        if event.text_area.id and event.text_area.id.startswith("commit-messages-"):
            try:
                index = int(event.text_area.id.split("-")[-1])
                if 0 <= index < len(self.services):
                    self.services[index].modified_commit_messages = event.text_area.text
            except (ValueError, IndexError):
                pass

    """
    Deploy actions
    """

    def action_display_selected(self) -> None:
        """Display the names of selected items with version upgrade info."""
        self.push_screen(SelectedItemsScreen(list(self.selected_items)))

    def refresh_pipeline_statuses(self) -> None:
        """Refresh the display with updated pipeline statuses."""
        list_view = self.query_one("#main-list-view", ListView)
        if list_view is None:
            return

        max_name_len = 0
        max_version_len = 0
        max_commits_len = 0

        # Calculate max lengths for alignment
        for service in self.services:
            max_name_len = max(max_name_len, len(service.name))
            max_version_len = max(max_version_len, len(service.version))
            max_commits_len = max(max_commits_len, len(str(service.commits_ahead)))

        # Update each item's title
        for i, item in enumerate(list_view.children):
            if i >= len(self.services):
                break

            service = self.services[i]
            collapsible = item.query_one(Collapsible)
            if collapsible is None:
                continue

            # Create formatted title with aligned columns
            padded_name = service.name.ljust(max_name_len)
            padded_version = service.version.ljust(max_version_len)
            padded_commits = str(service.commits_ahead).rjust(max_commits_len)

            # Add pipeline status to title if available
            title_parts = [f"{padded_name} | {padded_version} | {padded_commits}"]
            if hasattr(service, "pipeline_status") and service.pipeline_status:
                title_parts.append(f" | Pipeline: {service.pipeline_status}")

            title_text = "".join(title_parts)
            collapsible.title = title_text
