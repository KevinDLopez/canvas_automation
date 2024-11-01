import pprint
from typing import List, Tuple, TypedDict, Optional, Literal, Union
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QCheckBox,
    QProgressBar,
    QTabWidget,
    QGroupBox,
    QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import json
import sys
from Canvas.schemas import PageSchema
from GradingAutomation import Grader
from schemas import TeamInfo


# Define valid color strings


class QuizTableRowData(TypedDict, total=False):
    LocalPath: str
    PageName: str
    Status: str
    StatusColor: Optional[Literal["red", "green", "gray", "yellow", "white"]]  # Now accepts string literals


class GradingAutomationUI(QMainWindow):
    # Color mapping dictionary
    _COLOR_MAP = {
        "red": Qt.GlobalColor.red,
        "green": Qt.GlobalColor.green,
        "gray": Qt.GlobalColor.lightGray,
        "yellow": Qt.GlobalColor.yellow,
        "white": Qt.GlobalColor.white,
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grading Automation")
        self.setMinimumSize(1200, 800)  # Sets minimum window size to 800x600 pixels

        # Initialize state
        self.state = {}
        self.load_state()

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QVBoxLayout(main_widget)

        # Error display area at top
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setVisible(False)
        self.main_layout.addWidget(self.error_label)

        # Initialize tabs but don't create them yet
        self.tabs = QTabWidget()
        self.pages_created: List[PageSchema] = []

        # Check if we need to show course selection or main interface
        if not self.is_course_connected():
            self.show_course_selection()
        else:
            self.grader = Grader(self.state["course_id"], self.state["module_title"], self.state["canvas_token"])
            self.show_main_interface()

    def is_course_connected(self):
        return self.state.get("course_id") and self.state.get("canvas_token") and self.state.get("module_title")

    def show_course_selection(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Course Connection")
        group_layout = QVBoxLayout()

        # Course ID input
        self.course_id_input = QLineEdit()
        if self.state.get("course_id"):
            self.course_id_input.setText(str(self.state["course_id"]))
        group_layout.addWidget(QLabel("Course ID:"))
        group_layout.addWidget(self.course_id_input)

        # Canvas API Token input
        self.token_input = QLineEdit()
        if self.state.get("canvas_token"):
            self.token_input.setText(self.state["canvas_token"])

        group_layout.addWidget(QLabel("Canvas API Token:"))
        group_layout.addWidget(self.token_input)

        # Add Module Title input
        self.module_title_input = QLineEdit()
        if self.state.get("module_title"):
            self.module_title_input.setText(self.state["module_title"])
        group_layout.addWidget(QLabel("Presentations Module Title:"))
        group_layout.addWidget(self.module_title_input)

        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_course)
        group_layout.addWidget(self.connect_button)

        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()

        # Clear main layout and add course selection
        self.clear_main_layout()
        self.main_layout.addWidget(widget)

    def show_main_interface(self):
        # Create and add tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_project_verification_tab(), "Project Verification")
        self.tabs.addTab(self.create_pages_management_tab(), "Pages Management")
        self.tabs.addTab(self.create_forms_management_tab(), "Forms and Quizzes")

        # Connect the tab changed signal
        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.clear_main_layout()
        self.main_layout.addWidget(self.tabs)

    def clear_main_layout(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def connect_to_course(self):
        try:
            course_id = int(self.course_id_input.text())
            canvas_token = self.token_input.text()
            module_title = self.module_title_input.text()  # Get module title

            # Initialize grader
            self.grader = Grader(course_id, module_title, canvas_token)

            # Save to state
            self.state["course_id"] = course_id
            self.state["canvas_token"] = canvas_token
            self.state["module_title"] = module_title  # Save module title to state
            self.save_state()

            # Switch to main interface
            self.show_main_interface()

        except Exception as e:
            error_message = str(e)
            # Create new error label since the old one might have been deleted
            self.error_label = QLabel(error_message)
            self.error_label.setStyleSheet("color: red;")
            self.main_layout.insertWidget(0, self.error_label)
            self.error_label.setVisible(True)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.folder_path.setText(folder)

    def verify_projects(self):
        try:
            folder = self.folder_path.text()
            folders_with_team = self.grader.get_folders_with_team(folder)

            # Setup progress bar
            self.verify_progress.setMaximum(len(folders_with_team))
            self.verify_progress.setValue(0)
            self.verify_progress.setVisible(True)

            # Get failed projects (those with errors)
            self.local_projects_info: dict[str, tuple[TeamInfo | None, List[str], PageSchema | None]] = {
                folder_path: (team, errors, None)
                for folder_path, team, errors in self.grader.verify_all_projects(folders_with_team)
            }  # Dict[dict[str, tuple[TeamInfo | None, List[str]]]. PATH, (team, errors)

            # Update results table with all folders
            self.verify_results.setRowCount(len(folders_with_team))
            for i, folder_path in enumerate(folders_with_team):
                self.verify_progress.setValue(i + 1)

                folder_item = QTableWidgetItem(folder_path)
                errors = self.local_projects_info[folder_path][1]
                status = "Failed" if errors else "Passed"
                # add the projects that did not fail to self.pages_to_create
                if not errors:
                    print(f"Adding {folder_path} to pages_to_create")
                    # Check if the item has not been added yet
                    if not any(
                        folder_item_.text() == folder_path
                        for folder_item_ in self.pages_table.findItems(folder_path, Qt.MatchFlag.MatchExactly)
                    ):
                        self.pages_table.insertRow(i)
                        # Add checkbox in column 0
                        checkbox = QTableWidgetItem()
                        checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                        checkbox.setCheckState(Qt.CheckState.Checked)
                        self.pages_table.setItem(i, 0, checkbox)
                        # Move folder path to column 1
                        self.pages_table.setItem(i, 1, QTableWidgetItem(folder_path))
                        # Status in column 2
                        status_item = QTableWidgetItem("**")
                        status_item.setBackground(Qt.GlobalColor.green)
                        self.pages_table.setItem(i, 2, status_item)
                status_item = QTableWidgetItem(status)
                error_item = QTableWidgetItem("\n".join(errors) if errors else "")

                # Make error text wrap and expand row height as needed
                error_item.setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

                # Set background colors
                status_item.setBackground(Qt.GlobalColor.red if errors else Qt.GlobalColor.green)

                self.verify_results.setItem(i, 0, folder_item)
                self.verify_results.setItem(i, 1, status_item)
                self.verify_results.setItem(i, 2, error_item)

                # Adjust row height to fit content
                self.verify_results.resizeRowToContents(i)

            # Enable text wrapping for the error column
            self.verify_results.setWordWrap(True)
            self.verify_results.resizeColumnsToContents()

            self.verify_progress.setVisible(False)
        except Exception as e:
            self.show_error(str(e))

    def create_pages(self):
        try:
            # Get the pages to create from the table
            pages_to_create = [
                self.pages_table.item(i, 1).text()
                for i in range(self.pages_table.rowCount())
                if self.pages_table.item(i, 0).checkState() == Qt.CheckState.Checked
            ]
            print(f"pages_to_create: {pages_to_create}")
            self.grader.create_multiple_canvas_pages_based_on_folder(pages_to_create)

            # Update status in pages table for created pages
            for i in range(self.pages_table.rowCount()):
                folder_path = self.pages_table.item(i, 1).text()
                if folder_path in pages_to_create:
                    # Update status
                    status_item = QTableWidgetItem("Created")
                    status_item.setBackground(Qt.GlobalColor.green)
                    self.pages_table.setItem(i, 2, status_item)

                    # Update checkbox
                    checkbox_item = self.pages_table.item(i, 0)
                    if checkbox_item:
                        checkbox_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Remove ItemIsUserCheckable
                        checkbox_item.setCheckState(Qt.CheckState.Unchecked)
                        checkbox_item.setToolTip("Cannot create page: Page already exists")

        except Exception as e:
            self.show_error(str(e))

    def add_forms_quizzes(self):
        try:
            form_quizzes_to_create = []  # Contains folder paths

            # Get all checked rows to add forms/quizzes and retrieve their folder paths
            for i in range(self.quizzes_table.rowCount()):
                checkbox_item = self.quizzes_table.item(i, 0)  # Get the checkbox item

                if checkbox_item is not None and checkbox_item.checkState() == Qt.CheckState.Checked:
                    folder_path_item = self.quizzes_table.item(i, 1)  # Folder data column
                    if folder_path_item is not None:  # Ensure the items exist
                        folder_path = folder_path_item.text()
                        form_quizzes_to_create.append((folder_path, i))

            # Add forms and quizzes to each page
            for folder_path, row_index in form_quizzes_to_create:
                # Get page schema
                page = self.local_projects_info[folder_path][2]
                if not page:
                    raise Exception(f"Page {page} not found in local projects")
                print(f"\n\n1**page = {pprint.pformat(page.model_dump())}\n\n")
                try:
                    page = self.grader.add_google_forms_and_create_quiz(page, folder_path)
                    print(f"page = {pprint.pformat(page.model_dump())}")
                    status_item = QTableWidgetItem("Quiz and Feedback added")
                    status_item.setBackground(Qt.GlobalColor.yellow)
                    self.quizzes_table.setItem(row_index, 3, status_item)
                except Exception as inner_e:  # Set "Status" column as an error
                    print(inner_e)
                    status_item = QTableWidgetItem("Failed")
                    status_item.setBackground(Qt.GlobalColor.red)
                    self.quizzes_table.setItem(row_index, 3, status_item)

        except Exception as e:
            self.show_error(str(e))

    def remove_forms_quizzes(self):

        print("hello")

    def load_state(self):
        """Load application state from state.json"""
        try:
            with open("state.json", "r") as f:
                self.state = json.load(f)
        except FileNotFoundError:
            self.state = {}
        except json.JSONDecodeError:
            self.state = {}

    def save_state(self):
        """Save current application state to state.json"""
        with open("state.json", "w") as f:
            json.dump(self.state, f)

    def show_error(self, message):
        """Display error message in the UI"""
        self.error_label.setText(message)
        self.error_label.setVisible(True)

    def create_project_verification_tab(self):
        """Create the project verification tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Folder selection group
        folder_group = QGroupBox("Project Folder Selection")
        folder_layout = QHBoxLayout()

        self.folder_path = QLineEdit()
        if self.state.get("last_folder"):
            self.folder_path.setText(self.state["last_folder"])

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_folder)

        folder_layout.addWidget(self.folder_path)
        folder_layout.addWidget(browse_button)
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)

        # Verification group
        verify_group = QGroupBox("Project Verification")
        verify_layout = QVBoxLayout()

        verify_button = QPushButton("Verify Selected Projects")
        verify_button.clicked.connect(self.verify_projects)

        self.verify_progress = QProgressBar()
        self.verify_progress.setVisible(False)

        self.verify_results = QTableWidget()
        self.verify_results.setColumnCount(3)  # Changed from 2 to 3
        self.verify_results.setHorizontalHeaderLabels(["Folder", "Status", "Errors"])
        self.verify_results.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Make table read-only

        # Set column widths
        header = self.verify_results.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Folder column stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Status
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Errors column
        # self.verify_results.setColumnWidth(1, 100)  # Status column width in pixels

        self.verify_results.setMinimumWidth(400)  # Set minimum width for the table
        self.verify_results.setColumnWidth(0, 200)  # Minimum width for Folder column
        self.verify_results.setColumnWidth(2, 150)  # Minimum width for Errors column

        verify_layout.addWidget(verify_button)
        verify_layout.addWidget(self.verify_progress)
        verify_layout.addWidget(self.verify_results)
        verify_group.setLayout(verify_layout)
        layout.addWidget(verify_group)
        return tab

    def create_pages_management_tab(self):
        """pages management"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Pages selection group
        pages_group = QGroupBox("Available Pages")
        pages_layout = QVBoxLayout()

        self.pages_table = QTableWidget()
        self.pages_table.setColumnCount(3)
        self.pages_table.setHorizontalHeaderLabels(["Select", "Page", "Status"])

        # Set column widths and behaviors
        header = self.pages_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)

        self.pages_table.setColumnWidth(0, 50)
        self.pages_table.setColumnWidth(2, 100)

        self.pages_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.pages_table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        create_pages_button = QPushButton("Create Selected Pages")
        create_pages_button.clicked.connect(self.create_pages)

        pages_layout.addWidget(self.pages_table)
        pages_layout.addWidget(create_pages_button)
        pages_group.setLayout(pages_layout)
        layout.addWidget(pages_group)

        return tab

    def create_forms_management_tab(self):
        """Create the forms and quizzes management tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Forms and quizzes group
        forms_group = QGroupBox("Forms and Quizzes Management")
        forms_layout = QVBoxLayout()

        self.quizzes_table = QTableWidget()
        self.quizzes_table.setColumnCount(4)  # Changed to 4 columns
        self.quizzes_table.setHorizontalHeaderLabels(["Select", "Local Path", "Page Name", "Status"])

        header = self.quizzes_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Checkbox column
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Local Path
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Page Name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Status column

        self.quizzes_table.setColumnWidth(0, 50)  # Checkbox column
        self.quizzes_table.setColumnWidth(3, 100)  # Status column

        self.quizzes_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Connect the checkbox state change signal to the slot
        self.quizzes_table.cellChanged.connect(self.onCheckBoxChanged)

        button_layout = QHBoxLayout()
        add_forms_button = QPushButton("Add Forms/Quizzes")
        add_forms_button.clicked.connect(self.add_forms_quizzes)
        remove_forms_button = QPushButton("Close and Grade")
        remove_forms_button.setToolTip(
            "This will remove the quizzes/feedback form, post a image of the feedback and post grades"
        )
        remove_forms_button.clicked.connect(self.remove_forms_quizzes)

        button_layout.addWidget(add_forms_button)
        button_layout.addWidget(remove_forms_button)

        forms_layout.addWidget(self.quizzes_table)
        forms_layout.addLayout(button_layout)
        forms_group.setLayout(forms_layout)
        layout.addWidget(forms_group)

        return tab

    def save_ui_state(self):
        """Save the current state of UI elements"""
        # Save folder path
        self.state["last_folder"] = self.folder_path.text()

        self.save_state()

    def closeEvent(self, event):
        """Handle application closure"""
        self.save_ui_state()
        super().closeEvent(event)

    def on_tab_changed(self, index):
        # Check if the new tab is Pages Management (index 1)
        if index == 1:  # Pages Management tab
            self.on_pages_management_selected()
        elif index == 2:  # Forms and Quizzes tab
            self.on_forms_quizzes_management_selected()

    def on_forms_quizzes_management_selected(self):
        # Clear existing rows if they exist
        self.quizzes_table.setRowCount(0)

        print("Switched to Forms and Quizzes Management tab")
        # Update the forms table, all the pages that are created should be added here and get the status of the page using self.grader.get_page_status( page )
        # From all the pages in the module folder
        folder = self.folder_path.text()
        folders_with_team = self.grader.get_folders_with_team(folder)
        self.local_projects_info: dict[str, tuple[TeamInfo | None, List[str], PageSchema | None]] = {
            folder_path: (team, errors, None)
            for folder_path, team, errors in self.grader.verify_all_projects(folders_with_team)
        }  # Dict[dict[str, tuple[TeamInfo | None, List[str]]]. PATH, (team, errors)

        pages_posted_in_module = self.grader.get_pages_posted_in_module()  # List[PageSchema]

        for path, (team, errors, page) in self.local_projects_info.items():
            # print(f"path: {path}, team: {team}, errors: {errors}")
            if not team:
                continue
            if any(team.team_name == page.title for page in pages_posted_in_module):
                page = [page for page in pages_posted_in_module if page.title == team.team_name][0]
                status = self.grader.get_page_status(page)  # Literal['Created', 'Quiz and Feedback added', 'Done']
                color = "green" if status == "Done" else "yellow" if status == "Quiz and Feedback added" else "gray"
                self._add_quiz_table_row(
                    {"LocalPath": path, "PageName": page.title, "Status": status, "StatusColor": color}
                )
                # add this to self.local_projects_info
                self.local_projects_info[path] = (team, errors, page)
            else:
                print(f"Page {path} is not posted in the module")
                self._add_quiz_table_row(
                    {"LocalPath": path, "PageName": team.team_name, "Status": "Not Added", "StatusColor": "white"}
                )
        # check for pages that are not in the module but in the folder
        local_team_names = {team.team_name for _, (team, _, _) in self.local_projects_info.items() if team}
        # Find pages that exist in Canvas but not locally
        for page in pages_posted_in_module:
            if page.title not in local_team_names:
                self._add_quiz_table_row(
                    {
                        "LocalPath": "",
                        "PageName": page.title,
                        "Status": "No Local Files",
                        "StatusColor": "red",
                    }
                )

    def on_pages_management_selected(self):
        # Add your logic here for what should happen when switching to Pages Management
        print("Switched to Pages Management tab")
        # For example, you could refresh the pages table:
        """Update the pages table with available pages"""
        try:
            pages_to_create = self.grader.get_pages_to_create(
                folders=[
                    item.text()
                    for item in self.pages_table.findItems("", Qt.MatchFlag.MatchContains)
                    if item.column() == 1
                ]
            )  # Returns a list of strings ( which pages need to be created )

            # Update each row in the table
            for i in range(self.pages_table.rowCount()):
                folder_item = self.pages_table.item(i, 1)  # Get folder path from column 1
                if folder_item:
                    folder_path = folder_item.text()
                    # If the page needs to be created
                    if folder_path in pages_to_create:
                        status_item = QTableWidgetItem("Not Created")
                        checkbox_item = self.pages_table.item(i, 0)
                        if checkbox_item:
                            checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                            checkbox_item.setCheckState(Qt.CheckState.Checked)
                            checkbox_item.setToolTip("")  # Clear any existing tooltip
                            # checkbox_item.setBackground(Qt.GlobalColor.white)  # Reset background
                    else:
                        # Page is already created
                        status_item = QTableWidgetItem("Created")
                        status_item.setBackground(Qt.GlobalColor.green)
                        checkbox_item = self.pages_table.item(i, 0)
                        if checkbox_item:
                            checkbox_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Remove ItemIsUserCheckable
                            checkbox_item.setCheckState(Qt.CheckState.Unchecked)
                            checkbox_item.setToolTip("Cannot create page: Page already exists")
                            # checkbox_item.setBackground(Qt.GlobalColor.lightGray)  # Gray out the checkbox cell

                    self.pages_table.setItem(i, 2, status_item)

        except Exception as e:
            self.show_error(str(e))

    def _add_quiz_table_row(self, data: QuizTableRowData) -> None:
        """
        Protected method to add a row to the quizzes table.

        Args:
            data: Dictionary containing the row data with predefined types

        Example:
            ```python
            self._add_quiz_table_row({
                "LocalPath": "/path/to/quiz",
                "PageName": "Team 1 Quiz",
                "Status": "Not Added",
                "StatusColor": "red"  # Optional: "red", "green", "gray", "yellow", "white"
            })
            ```
        """
        row = self.quizzes_table.rowCount()
        self.quizzes_table.insertRow(row)

        # Add checkbox
        checkbox = QTableWidgetItem()
        checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)

        # Only enable checkbox if status isn't "Done" and has local files
        if data.get("Status") != "Done" and data.get("Status") != "No Local Files" and data.get("LocalPath"):
            checkbox.setCheckState(Qt.CheckState.Unchecked)
        else:
            checkbox.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Disable checkbox
            checkbox.setCheckState(Qt.CheckState.Unchecked)

        self.quizzes_table.setItem(row, 0, checkbox)

        # Add other columns (shifted by 1)
        self.quizzes_table.setItem(row, 1, QTableWidgetItem(str(data.get("LocalPath", ""))))
        self.quizzes_table.setItem(row, 2, QTableWidgetItem(str(data.get("PageName", ""))))

        status_item = QTableWidgetItem(str(data.get("Status", "")))
        if "StatusColor" in data and data["StatusColor"] in self._COLOR_MAP:
            status_item.setBackground(self._COLOR_MAP[data["StatusColor"]])
        self.quizzes_table.setItem(row, 3, status_item)

    def onCheckBoxChanged(self, row, column):
        item = self.quizzes_table.item(row, column)
        lastState = item.data(Qt.ItemDataRole.UserRole)
        currentState = item.checkState()
        if currentState != lastState:
            item.setData(Qt.ItemDataRole.UserRole, currentState)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GradingAutomationUI()
    window.show()
    sys.exit(app.exec())
