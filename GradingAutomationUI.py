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
import json
import sys
from GradingAutomation import Grader


class GradingAutomationUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grading Automation")
        self.setMinimumSize(1200, 800)  # Sets minimum window size to 800x600 pixels

        # Initialize state
        self.state = {}
        self.load_state()

        if self.state.get("course_id", None) and self.state.get("canvas_token", None):
            self.grader = Grader(self.state["course_id"], self.state["canvas_token"])

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

        # Check if we need to show course selection or main interface
        if not self.is_course_connected():
            self.show_course_selection()
        else:
            self.show_main_interface()

    def is_course_connected(self):
        return self.state.get("course_id") and self.state.get("canvas_token")

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
        self.tabs.addTab(self.create_forms_management_tab(), "Forms & Quizzes")

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

            # Initialize grader with course ID only (assuming Grader class takes only course_id)
            self.grader = Grader(course_id, canvas_token)

            # Save to state
            self.state["course_id"] = course_id
            self.state["canvas_token"] = canvas_token
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
            folders = self.grader.get_folders_with_team(folder)

            # Setup progress bar
            self.verify_progress.setMaximum(len(folders))
            self.verify_progress.setValue(0)
            self.verify_progress.setVisible(True)

            # Get failed projects (those with errors)
            failed_projects = dict(self.grader.verify_all_projects(folders))

            # Update results table with all folders
            self.verify_results.setRowCount(len(folders))
            for i, folder_path in enumerate(folders):
                self.verify_progress.setValue(i + 1)

                folder_item = QTableWidgetItem(folder_path)
                errors = failed_projects.get(folder_path, None)
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
                        self.pages_table.setItem(i, 2, QTableWidgetItem("Not Created"))
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
        # Implementation for creating selected pages
        print("**create_pages")

    def add_forms_quizzes(self):
        # Implementation for adding forms/quizzes
        print("add_forms_quizzes")

    def remove_forms_quizzes(self):
        # Implementation for removing forms/quizzes
        print("remove_forms_quizzes")

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
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Folder column stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Status column fixed
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Errors column expands to fill available space
        self.verify_results.setColumnWidth(1, 100)  # Status column width in pixels

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
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Fixed width for checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Page path stretches
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Fixed width for status

        self.pages_table.setColumnWidth(0, 50)  # Narrow checkbox column
        self.pages_table.setColumnWidth(2, 100)  # Status column width

        # Make table read-only
        self.pages_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Center align the checkbox column
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

        self.forms_table = QTableWidget()
        self.forms_table.setColumnCount(3)
        self.forms_table.setHorizontalHeaderLabels(["Page", "Add Form/Quiz", "Remove Form/Quiz"])
        self.forms_table.horizontalHeader().setStretchLastSection(True)

        button_layout = QHBoxLayout()
        add_forms_button = QPushButton("Add Forms/Quizzes")
        add_forms_button.clicked.connect(self.add_forms_quizzes)
        remove_forms_button = QPushButton("Remove Forms/Quizzes")
        remove_forms_button.clicked.connect(self.remove_forms_quizzes)

        button_layout.addWidget(add_forms_button)
        button_layout.addWidget(remove_forms_button)

        forms_layout.addWidget(self.forms_table)
        forms_layout.addLayout(button_layout)
        forms_group.setLayout(forms_layout)
        layout.addWidget(forms_group)

        return tab

    def update_pages_table(self):
        """Update the pages table with available pages"""
        try:
            pages_to_create = self.grader.get_pages_to_create(
                folders=[
                    item.text()
                    for item in self.pages_table.findItems("", Qt.MatchFlag.MatchContains)
                    if item.column() == 1
                ]
            )  # Returns a list of strings ( which pages need to be created )

            # update the 3rd column based on this list
            for i, page in enumerate(pages_to_create):
                self.pages_table.setItem(i, 2, QTableWidgetItem("Not Created"))
        except Exception as e:
            self.show_error(str(e))

    def save_ui_state(self):
        """Save the current state of UI elements"""
        # Save folder path
        self.state["last_folder"] = self.folder_path.text()

        # Save selected pages
        selected_pages = []
        for i in range(self.pages_table.rowCount()):
            checkbox = self.pages_table.cellWidget(i, 1)
            if checkbox and isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                page_item = self.pages_table.item(i, 0)
                if page_item:
                    selected_pages.append(page_item.text())
        self.state["selected_pages"] = selected_pages

        self.save_state()

    def closeEvent(self, event):
        """Handle application closure"""
        self.save_ui_state()
        super().closeEvent(event)

    def on_tab_changed(self, index):
        # Check if the new tab is Pages Management (index 1)
        if index == 1:  # Pages Management tab
            self.on_pages_management_selected()

    def on_pages_management_selected(self):
        # Add your logic here for what should happen when switching to Pages Management
        print("Switched to Pages Management tab")
        # For example, you could refresh the pages table:
        self.update_pages_table()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GradingAutomationUI()
    window.show()
    sys.exit(app.exec())
