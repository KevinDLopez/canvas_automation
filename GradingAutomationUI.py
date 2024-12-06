import datetime
from enum import IntEnum
import os
import pprint
import pandas as pd
from typing import Callable, Dict, List, Tuple, TypedDict, Optional, Literal, Union
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
    QScrollArea,
    QTextEdit,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QKeySequence, QShortcut, QPalette
from pathlib import Path
import json
import sys
from Canvas.schemas import PageSchema
from GoogleServices.GoogleServices import get_id_from_url
from GoogleServices.schemas import Form
from GradingAutomation import Grader
from Logging import Print
from schemas import TeamInfo


class LogLevel(IntEnum):
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3


# Define valid color strings
base_path = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.abspath(".")
state_path = os.path.join(base_path, "state.json")


class QuizTableRowData(TypedDict, total=False):
    LocalPath: str
    PageName: str
    Status: str
    StatusColor: Optional[Literal["red", "green", "gray", "yellow", "white", "blue"]]  # Now accepts string literals
    FontColor: Optional[Literal["white", "black"]]


class GradingAutomationUI(QMainWindow):
    # Color mapping dictionary
    _COLOR_MAP = {
        "red": Qt.GlobalColor.red,
        "green": QColor(0, 240, 0, 200),
        "blue": QColor(0, 0, 255, 100),
        "gray": Qt.GlobalColor.lightGray,
        "yellow": Qt.GlobalColor.yellow,
        "white": Qt.GlobalColor.white,
        "black": Qt.GlobalColor.black,
    }

    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            """
            QPushButton {
                background-color: #2d89ef;
                border: none;
                padding: 5px 10px;
                color: white;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1e5fb4;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #2b2b2b;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle {
                background: #606060;
                border-radius: 6px;
            }
            QScrollBar::handle:hover {
                background: #787878;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                background: none;
            }
        """
        )

        # Set application icon
        icon_path = str(Path(__file__).parent / "assets" / "app_icon.png")
        app_icon = QIcon(icon_path)
        self.setWindowIcon(app_icon)
        QApplication.setWindowIcon(app_icon)
        self.setWindowTitle("Grading Automation")
        self.setMinimumSize(1200, 800)  # Sets minimum window size to 800x600 pixels
        self.logging_level: LogLevel = LogLevel.INFO
        # Initialize state
        self.state = {}
        self.load_state()

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QVBoxLayout(main_widget)

        # Initialize tabs but don't create them yet
        self.tabs = QTabWidget()
        self.pages_created: List[PageSchema] = []

        # Check if we need to show course selection or main interface
        self.create_main_interface()
        self.create_course_selection()

        if not self.is_course_connected():
            self.course_selection_container.setVisible(True)
            self.tabs.setVisible(False)
        else:
            self.grader = Grader(self.state["course_id"], self.state["module_title"], self.state["canvas_token"])
            self.course_selection_container.setVisible(False)
            self.tabs.setVisible(True)

        # Error display area at bottom
        self.log_text = QLabel()
        self.log_text.setVisible(True)
        self.log_text.setWordWrap(True)  # Enable word wrap for long error messages
        self.log_text.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)  # Align text to top-left
        self.log_text.setTextFormat(Qt.TextFormat.RichText)  # Enable rich text
        # Create a scroll area for the error label
        self.log_scroll_area = QScrollArea()
        self.log_scroll_area.setWidgetResizable(True)
        self.log_scroll_area.setMaximumHeight(100)  # Set maximum height to 200 pixels
        self.log_scroll_area.setWidget(self.log_text)
        self.log_scroll_area.setVisible(True)
        self.log_scroll_area.setStyleSheet("QScrollArea { border: 1px solid gray; border-radius: 10px; padding: 5px; }")

        self.main_layout.addWidget(self.log_scroll_area)

        # Set up keyboard shortcut for saving state
        save_sequence = QKeySequence("Ctrl+S")
        save_shortcut = QShortcut(save_sequence, self)
        save_shortcut.activated.connect(self.save_ui_state)

        # Functions to call at start up
        QApplication.processEvents()
        # if this is the first time running the program, if not then don't verify projects
        if self.state.get("worksheet_url"):
            self.verify_projects()
        else:
            Print("First time running ")

    def is_course_connected(self):
        return self.state.get("course_id") and self.state.get("canvas_token") and self.state.get("module_title")

    def create_course_selection(self):
        self.course_selection_container = QWidget()
        layout = QVBoxLayout(self.course_selection_container)

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

        self.main_layout.addWidget(self.course_selection_container)

    def create_main_interface(self):
        # Create and add tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_project_verification_tab(), "Project Verification")
        self.tabs.addTab(self.create_pages_management_tab(), "Pages Management")
        self.tabs.addTab(self.create_forms_management_tab(), "Forms and Quizzes")
        self.tabs.addTab(self.create_form_analysis_tab(), "Form Analysis")

        # Connect the tab changed signal
        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.main_layout.addWidget(self.tabs)

    def connect_to_course(self):
        try:
            course_id = int(self.course_id_input.text())
            self.log(f"Connecting to course {course_id}", "INFO")
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
            self.course_selection_container.setVisible(False)
            self.tabs.setVisible(True)
            self.log("Successfully connected to course", "INFO")

        except Exception as e:
            error_message = str(e)
            self.log(error_message, log_type="ERROR")

    def browse_folder(self):
        if self.folder_path.text():
            directory = self.folder_path.text()
        else:
            directory = self.state.get("last_folder", base_path)
        folder = QFileDialog.getExistingDirectory(self, caption="Select Project Folder", directory=directory)
        if folder:
            self.folder_path.setText(folder)

    def verify_projects(self):
        """Continues the verification process after worksheet ID is entered"""
        worksheet_id = get_id_from_url(self.worksheet_url.text())
        self.grader.set_worksheet(worksheet_id)
        self.grader.read_worksheet()
        Print(f"Worksheet ID set to {worksheet_id}", "INFO")
        folder = self.folder_path.text()
        self.log(f"Starting project verification in folder: {folder}", "INFO")
        # folders_with_team = self.grader.get_folders_with_team(folder)
        folders_with_team = []
        print(f"student_records = {self.grader.student_records}")
        seen_path = set()
        projects_to_download = []
        for record in self.grader.student_records:
            path = self.folder_path.text() + "/" + record["Team_Name"]
            if path in seen_path:
                print(f"skipping {path} because it was already seen")
                continue
            seen_path.add(path)
            if not os.path.exists(path):
                Print(
                    f"  Folder {path} does not exist, it would be downloaded, once download button is clicked",
                    log_type="INFO",
                )
                Print(f"This is the student_records = {self.grader.student_records}")
                projects_to_download.append((record["Team_Name"], path))
            # elif not self.grader.is_a_project_folder(path):
            #     Print(
            #         f" Folder {path} does not contain all files. If you would like to re-download it remove it from your files",
            #         log_type="WARN",
            #     )
            else:
                folders_with_team.append(path)
        self.log(f"Found {len(folders_with_team)} folders with teams", log_type="INFO")
        self.log(f"Found {len(projects_to_download)} folders to download", log_type="INFO")

        self.file_to_download_group.setVisible(len(projects_to_download) > 0)
        self.file_to_download.setRowCount(len(projects_to_download))
        for i, (team_name, folder_path) in enumerate(projects_to_download):
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox.setCheckState(Qt.CheckState.Checked)
            self.file_to_download.setItem(i, 0, checkbox)
            self.file_to_download.setItem(i, 1, QTableWidgetItem(team_name))
            # self.file_to_download.setItem(i, 2, QTableWidgetItem(folder_path))

        # Get failed projects (those with errors)
        self.local_projects_info: dict[str, tuple[List[str], PageSchema | None]] = {
            folder_path: (errors, None) for folder_path, errors in self.grader.verify_all_projects(folders_with_team)
        }  # Dict[dict[str, tuple[TeamInfo | None, List[str]]]. PATH, (team, errors)

        # Update results table with all folders
        self.verify_results.setRowCount(len(folders_with_team))
        for i, folder_path in enumerate(folders_with_team):

            folder_item = QTableWidgetItem(folder_path)
            errors = self.local_projects_info[folder_path][0]
            status = "Failed" if errors else "Passed"
            # add the projects that did not fail to self.pages_to_create
            if not errors:
                Print(f"Adding {folder_path} to pages_to_create")
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
                    status_item.setBackground(self._COLOR_MAP["green"])
                    status_item.setForeground(self._COLOR_MAP["white"])
                    self.pages_table.setItem(i, 2, status_item)
            status_item = QTableWidgetItem(status)
            error_item = QTableWidgetItem("\n".join(errors) if errors else "")

            # Make error text wrap and expand row height as needed
            error_item.setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

            # Set background colors
            status_item.setBackground(self._COLOR_MAP["red"] if errors else self._COLOR_MAP["green"])
            status_item.setForeground(self._COLOR_MAP["white"])

            self.verify_results.setItem(i, 0, folder_item)
            self.verify_results.setItem(i, 1, status_item)
            self.verify_results.setItem(i, 2, error_item)

            # Adjust row height to fit content
            self.verify_results.resizeRowToContents(i)

        # Enable text wrapping for the error column
        self.verify_results.setWordWrap(True)
        # self.verify_results.resizeColumnsToContents()

    def create_pages(self):
        try:
            # Get the pages to create from the table
            pages_to_create = [
                self.pages_table.item(i, 1).text()
                for i in range(self.pages_table.rowCount())
                if self.pages_table.item(i, 0).checkState() == Qt.CheckState.Checked
            ]
            Print(f"pages_to_create: {pages_to_create}")
            self.grader.create_multiple_canvas_pages_based_on_folder(pages_to_create)

            # Update status in pages table for created pages
            for i in range(self.pages_table.rowCount()):
                folder_path = self.pages_table.item(i, 1).text()
                if folder_path in pages_to_create:
                    # Update status
                    status_item = QTableWidgetItem("Created")
                    status_item.setBackground(self._COLOR_MAP["green"])
                    status_item.setForeground(self._COLOR_MAP["white"])
                    self.pages_table.setItem(i, 2, status_item)

                    # Update checkbox
                    checkbox_item = self.pages_table.item(i, 0)
                    if checkbox_item:
                        checkbox_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Remove ItemIsUserCheckable
                        checkbox_item.setCheckState(Qt.CheckState.Unchecked)
                        checkbox_item.setToolTip("Cannot create page: Page already exists")

        except Exception as e:
            self.log(str(e), log_type="ERROR")

    def add_forms_quizzes(self):
        try:
            form_quizzes_to_create = []  # Contains folder paths
            self.path_to_forms: Dict[str, Form] = {}
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
                page = self.local_projects_info[folder_path][1]
                if not page:
                    raise Exception(f"Page {page} not found in local projects")
                Print(f"\n\n1**page = {pprint.pformat(page.model_dump())}\n\n")
                try:
                    status = self.grader.get_page_status(page)
                    Print(f" ****status = {status}")
                    if status == "Done":
                        status_item = QTableWidgetItem("Done")
                        status_item.setBackground(self._COLOR_MAP["green"])
                        status_item.setForeground(self._COLOR_MAP["white"])
                        self.quizzes_table.setItem(row_index, 3, status_item)
                        continue
                    page, form = self.grader.add_google_forms_and_create_quiz(page, folder_path)
                    if page is None or form is None:
                        status_item = QTableWidgetItem("Quiz and Feedback added")
                        status_item.setBackground(self._COLOR_MAP["blue"])
                        status_item.setForeground(self._COLOR_MAP["white"])
                        self.quizzes_table.setItem(row_index, 3, status_item)
                    else:
                        self.path_to_forms[folder_path] = form
                        # create a form json file and store it under path
                        # json.dump(form, open(folder_path + "/form.json", "w"))
                        team_name = os.path.basename(folder_path)
                        # update the google.student_record_sheets to include the new form
                        for record in self.grader.student_records:
                            if record["Team_Name"] == team_name:
                                record["Google_Form_ID"] = form["formId"]
                        self.grader.update_worksheet()
                        # TODO: Might need to update the page object in self.local_projects_info
                        Print(f"page = {pprint.pformat(page.model_dump())}")
                        status_item = QTableWidgetItem("Quiz and Feedback added")
                        status_item.setBackground(self._COLOR_MAP["blue"])
                        status_item.setForeground(self._COLOR_MAP["white"])
                        self.quizzes_table.setItem(row_index, 3, status_item)
                except Exception as inner_e:  # Set "Status" column as an error
                    Print(inner_e)
                    status_item = QTableWidgetItem("Failed")
                    status_item.setBackground(self._COLOR_MAP["red"])
                    status_item.setForeground(self._COLOR_MAP["white"])
                    self.quizzes_table.setItem(row_index, 3, status_item)

        except Exception as e:
            self.log(str(e), log_type="ERROR")

    def remove_forms_quizzes_wrapper(self):
        def handle_ok(assignment_title: str):
            Print("assignment_title", assignment_title)
            self._remove_forms_quizzes(assignment_title)
            self.state["last_assignment_title_2"] = assignment_title
            self.save_state()

        self.__make_popup(  # Using a pop up to get the assignment title
            title="Enter Assignment Title",
            label_text="Assignment Title:",
            default_value=self.state.get("last_assignment_title_2", ""),
            ok_callback=handle_ok,  # Function call is done here
        )

    def _remove_forms_quizzes(self, assignment_title: str = "Presentation Grade"):
        # Implementation for removing forms/quizzes
        local_paths_selected = []
        for i in range(self.quizzes_table.rowCount()):
            checkbox_item = self.quizzes_table.item(i, 0)
            if checkbox_item is not None and checkbox_item.checkState() == Qt.CheckState.Checked:
                local_path_item = self.quizzes_table.item(i, 1)
                if local_path_item is not None:
                    local_paths_selected.append((local_path_item.text(), i))

        for local_path, row_index in local_paths_selected:
            errors, page = self.local_projects_info[local_path]
            team_name = os.path.basename(local_path)
            team = self.grader.convert_student_record_sheets_to_team_info(team_name)
            if not team:
                self.log("### not team -  HEY YOU NEED TO CREATE THE QUIZ FIRST ####", log_type="WARN")
                continue
            if not page:
                self.log("### not page - HEY YOU NEED TO CREATE THE QUIZ FIRST ####", log_type="WARN")
                continue
            status = self.grader.get_page_status(page)
            if status == "Created":
                self.log("### Created - HEY YOU NEED TO CREATE THE QUIZ FIRST ####", log_type="WARN")
                continue
            # form: Form = json.load(open(local_path + "/form.json"))
            # Read the form id from the google.student_record_sheets
            form_id = [
                record["Google_Form_ID"] for record in self.grader.student_records if record["Team_Name"] == team_name
            ][0]
            responses = self.grader.google.get_form_responses(form_id)
            if responses is None:
                self.log("### No responses - MAKE SURE PEOPLE HAVE RESPONDED ####", log_type="WARN")
                continue
            page = self.grader.remove_feedback_url_and_quiz(page)
            # add grate and create image
            emails = [team_member.email for team_member in team.team_members]
            image = local_path + "/" + team.team_name + ".png"
            try:
                self.grader.grade_presentation_project(
                    form_id=form_id, assignment_title=assignment_title, emails=emails, path_image=image
                )
                status_item = QTableWidgetItem("Done")
                status_item.setBackground(self._COLOR_MAP["green"])
                status_item.setForeground(self._COLOR_MAP["white"])
                self.quizzes_table.setItem(row_index, 3, status_item)
            except Exception as e:
                Print(f"Error grading project {local_path}: {e}", log_type="ERROR")
            page = self.grader.add_images_to_body(page, [image])

    def load_state(self):
        """Load application state from state.json"""
        try:
            with open(state_path, "r") as f:
                self.state = json.load(f)
        except FileNotFoundError:
            self.state = {}
        except json.JSONDecodeError:
            self.state = {}

    def save_state(self):
        """Save current application state to state.json"""
        with open(state_path, "w") as f:
            json.dump(self.state, f)

    def log(self, *args, log_type: Literal["INFO", "ERROR", "DEBUG", "WARN"] = "DEBUG"):
        """Display log message in the UI. Multiple arguments will be joined with spaces."""
        if LogLevel[log_type] < self.logging_level:
            print("***log_type", log_type)
            return
        message = " ".join(str(arg) for arg in args)
        previous_text = self.log_text.text()
        colors = {"INFO": "black", "ERROR": "red", "DEBUG": "gray", "WARN": "orange"}
        left_padding = "-" * ((10 - len(log_type)) // 2)
        right_padding = "-" * ((9 - len(log_type)) // 2)
        formatted_message = f'<span style="font-family: Courier New; font-size: 12px; color: {colors[log_type]};">[ {left_padding}{log_type}{right_padding} ] - {datetime.datetime.now().strftime("%I:%M:%S %p")} - {message}</span>'
        # print(formatted_message)
        new_text = f"{previous_text}<br>{formatted_message}" if previous_text else formatted_message
        self.log_text.setText(new_text)
        self.log_text.setVisible(True)
        QApplication.processEvents()
        self.log_scroll_area.verticalScrollBar().setValue(self.log_scroll_area.verticalScrollBar().maximum())

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

        worksheet_url_group = QGroupBox("Spreadsheet URL")
        worksheet_url_layout = QHBoxLayout()
        self.worksheet_url = QLineEdit()
        self.worksheet_url.setText(
            self.state.get(
                "worksheet_url",
                "https://docs.google.com/spreadsheets/u/0/d/1tuuIobh2R4KQJBxCPR60E0EFVW_jr9_l6Aaj3lx6qaQ/htmlview",
            )
        )
        worksheet_url_layout.addWidget(self.worksheet_url)
        worksheet_url_group.setLayout(worksheet_url_layout)
        layout.addWidget(worksheet_url_group)
        layout.addWidget(folder_group)

        # Verification group
        verify_group = QGroupBox("Project Verification")
        verify_layout = QVBoxLayout()

        verify_button = QPushButton("Verify Selected Projects")
        verify_button.clicked.connect(self.verify_projects)

        self.verify_results = QTableWidget()
        self.verify_results.setColumnCount(3)
        self.verify_results.setHorizontalHeaderLabels(["Folder", "Status", "Errors"])
        self.verify_results.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Make table read-only

        self.file_to_download_group = QGroupBox("Files to Download")
        self.file_to_download_layout = QVBoxLayout()
        self.file_to_download = QTableWidget()
        self.file_to_download.setColumnCount(2)  # Checkbox and team_name
        self.file_to_download.setHorizontalHeaderLabels(["Select", "Folder"])
        self.file_to_download.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Make table read-only

        download_button = QPushButton("Download")
        download_button.clicked.connect(self.download_folder_click)

        self.file_to_download_group.setLayout(self.file_to_download_layout)
        self.file_to_download_layout.addWidget(download_button)
        self.file_to_download_layout.addWidget(self.file_to_download)
        self.file_to_download_group.setVisible(False)

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
        verify_layout.addWidget(self.verify_results)
        verify_group.setLayout(verify_layout)
        layout.addWidget(self.file_to_download_group)
        layout.addWidget(verify_group)
        return tab

    def __make_popup(
        self,
        title: str,
        label_text: str,
        default_value: str = "",
        ok_callback: Optional[Callable[[str], None]] = None,
        initial_size=(400, 150),
    ):
        """Create a reusable popup dialog with input field and OK/Cancel buttons.

        Args:
            title: Window title for the popup
            label_text: Label text for the input field
            default_value: Optional default value for input field
            ok_callback: Callback function to execute when OK is clicked, receives input text as parameter
        """
        Print(f"Creating popup with title: {title}, label_text: {label_text}, default_value: {default_value}")
        dialog = QWidget()
        dialog.setWindowTitle(title)
        dialog_layout = QVBoxLayout()
        dialog.resize(*initial_size)  # Set initial size for popup

        # Add input field
        input_field = QLineEdit()
        if default_value:
            input_field.setText(default_value)
        dialog_layout.addWidget(QLabel(label_text))
        dialog_layout.addWidget(input_field)

        # Add buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        dialog_layout.addLayout(button_layout)

        dialog.setLayout(dialog_layout)

        # Handle button clicks
        def on_ok():
            if ok_callback:
                ok_callback(input_field.text())
            dialog.close()

        def on_cancel():
            dialog.close()

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(on_cancel)

        dialog.show()

    def download_folder_click(self):
        def handle_ok(assignment_title: str):
            Print("assignment_title", assignment_title)
            for checked_row in range(self.file_to_download.rowCount()):
                if self.file_to_download.item(checked_row, 0).checkState() == Qt.CheckState.Checked:
                    # Get the students emails from the self.grader.google.get_student_emails(student_id)
                    team_name = self.file_to_download.item(checked_row, 1).text()
                    for student_record in self.grader.student_records:
                        if student_record["Team_Name"] == self.file_to_download.item(checked_row, 1).text():
                            student_email = student_record["Email"]
                            student_id = self.grader.canvas.get_student_id_by_email(student_email)
                            if not student_id:
                                Print(f"Student ID not found for {student_email}", log_type="ERROR")
                                continue
                            files_downloaded = self.grader.canvas.download_student_submission_attachments(
                                assignment_id=self.grader.canvas.get_assignment_by_title(assignment_title),
                                download_dir=self.folder_path.text() + "/" + team_name,
                                user_id=student_id,
                            )
                            if files_downloaded:
                                self.log(f"Downloaded {len(files_downloaded)} files for {team_name}", log_type="INFO")
                                break  # No need to continue if any files for the team
            # Save to state
            self.state["last_assignment_title"] = assignment_title
            self.save_state()

        self.__make_popup(
            title="Enter Assignment Title",
            label_text="Assignment Title:",
            default_value=self.state.get("last_assignment_title", ""),
            ok_callback=handle_ok,
        )

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
        self.quizzes_table.setHorizontalHeaderLabels(["Select", "Local Path", "Team_Name", "Status"])

        header = self.quizzes_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Checkbox column
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Local Path
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Page Name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Status column

        self.quizzes_table.setColumnWidth(0, 50)  # Checkbox column
        self.quizzes_table.setColumnWidth(3, 200)  # Status column

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
        remove_forms_button.clicked.connect(self.remove_forms_quizzes_wrapper)

        button_layout.addWidget(add_forms_button)
        button_layout.addWidget(remove_forms_button)

        forms_layout.addWidget(self.quizzes_table)
        forms_layout.addLayout(button_layout)
        forms_group.setLayout(forms_layout)
        layout.addWidget(forms_group)

        return tab

    def create_form_analysis_tab(self):
        "Create the form analysis tab"
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Form Analysis group
        forms_analysis_group = QGroupBox("Analyze Responses")
        forms_analysis_layout = QVBoxLayout()

        # Horizontal layout for buttons
        button_layout = QHBoxLayout()
        aggregate_responses_btn = QPushButton("Aggregate Responses")
        aggregate_responses_btn.clicked.connect(self.aggregate_form_responses)
        analyze_form_response_btn = QPushButton("Analyze Google Responses")
        analyze_form_response_btn.clicked.connect(self.analyze_responses)

        button_layout.addWidget(aggregate_responses_btn)
        button_layout.addWidget(analyze_form_response_btn)
        forms_analysis_layout.addLayout(button_layout)
        forms_analysis_group.setLayout(forms_analysis_layout)

        # Dropdown group
        dropdown_group = QGroupBox("Form Analysis")
        dropdown_layout = QVBoxLayout()
        self.dropdown_menu = QComboBox()
        self.dropdown_menu.addItem("Grade Distribution for all presentations")
        self.dropdown_menu.addItem("Each student average grading for others")
        self.dropdown_menu.addItem("Top 3 Presentations")
        self.dropdown_menu.addItem("Student Outliers")

        # Connect dropdown selection change to handler
        self.dropdown_menu.currentIndexChanged.connect(self.handle_dropdown_change)
        dropdown_layout.addWidget(self.dropdown_menu)

        # Table group
        self.analysis_table = QTableWidget()
        self.analysis_table.setRowCount(0)
        self.analysis_table.setColumnCount(0)  # Start with 0 columns
        self.analysis_table.setHorizontalHeaderLabels([])  # No headers initially
        dropdown_layout.addWidget(self.analysis_table)

        dropdown_group.setLayout(dropdown_layout)
        layout.addWidget(forms_analysis_group)
        layout.addWidget(dropdown_group)
        return tab

    def aggregate_form_responses(self):
        "Aggregate all form responses for all groups into a single spreadsheet"

        output_folder = "grading"
        output_file = os.path.join(output_folder, "all_form_responses.xlsx")

        # Create the output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        spreadsheet_id = get_id_from_url(self.worksheet_url.text())
        if not spreadsheet_id:
            self.log(
                "Invalid spreadsheet URL, Make sure to enter a spreadsheet URL in the Project Verification Tab",
                log_type="ERROR",
            )
            return

        forms_ids = {}
        for record in self.grader.student_records:
            if record["Team_Name"] not in forms_ids and record["Google_Form_ID"]:
                forms_ids[record["Team_Name"]] = record["Google_Form_ID"]

        Print(f"forms_ids: {forms_ids}")
        # Retrieve all form responses from form_ids
        all_responses = []
        for team_name, form_id in forms_ids.items():
            try:
                # Get responses from google forms
                responses = self.grader.get_google_form_responses(form_id)  # DataFrame
                all_responses.append(responses)

                # Append an empty row as a separator
                all_responses.append(pd.DataFrame({"": []}))
            except Exception as e:
                Print(f"Error processing form ID {form_id}: {e}", log_type="ERROR")

        # Create Excel file containing all responses
        if all_responses:
            dataframe = pd.concat(all_responses, ignore_index=True)
            dataframe.to_excel(output_file, index=False)
            Print(f"Form responses successfully aggregated to {output_file}.", log_type="INFO")
        else:
            Print("No responses found.", log_type="ERROR")

    def analyze_responses(self):
        output_folder = "grading"
        spreadsheet_file = os.path.join(output_folder, "all_form_responses.xlsx")

        # Check if the file exists
        # if not os.path.exists(spreadsheet_file):
        #     self.log(f"Error: The file {spreadsheet_file} does not exist.", log_type="ERROR")
        #     return

        # Testing purpose (remove later)
        project_dir = os.getcwd()
        spreadsheet_file = os.path.join(project_dir, "S24-574-all-responses.xlsx")

        try:
            # Retrieve group averages, student averages, and top 3 presentations
            group_avg, student_avg, top_3_presentations, student_outliers = self.grader.process_form_responses(
                spreadsheet_file
            )

            # Store the DataFrames for reuse
            self.group_avg = group_avg
            self.student_avg = student_avg
            self.top_3_presentations = top_3_presentations
            self.student_outliers = student_outliers

            # Update table based on dropdown selection
            self.handle_dropdown_change()
        except (FileNotFoundError, ValueError) as e:
            self.log(str(e), log_type="ERROR")
            return

    def handle_dropdown_change(self):
        dropdown_selection = self.dropdown_menu.currentText()

        # Check if DataFrames are already loaded
        if (
            not hasattr(self, "group_avg")
            or not hasattr(self, "student_avg")
            or not hasattr(self, "top_3_presentations")
            or not hasattr(self, "student_outliers")
        ):
            self.log("Data not loaded. Please analyze responses first.", log_type="ERROR")
            return

        try:
            # Update the table based on the dropdown selection
            if dropdown_selection == "Grade Distribution for all presentations":
                self.update_analysis_table(self.group_avg)
            elif dropdown_selection == "Each student average grading for others":
                self.update_analysis_table(self.student_avg)
            elif dropdown_selection == "Top 3 Presentations":
                self.update_analysis_table(self.top_3_presentations)
            elif dropdown_selection == "Student Outliers":
                self.update_analysis_table(self.student_outliers)
        except Exception as e:
            self.log(str(e), log_type="ERROR")

    def update_analysis_table(self, data: pd.DataFrame):
        # Clear existing rows if they exist
        self.analysis_table.setRowCount(0)

        # Check if data is empty
        if data.empty:
            return

        # Set number of rows and columns dynamically based on data
        num_rows = len(data)
        num_columns = data.shape[1]
        row_position = 0

        self.analysis_table.setColumnCount(num_columns)

        # Set the header labels
        headers = list(data.columns)
        self.analysis_table.setHorizontalHeaderLabels(headers)

        # Convert DataFrame rows to table rows
        for _, row in data.iterrows():
            self.analysis_table.insertRow(row_position)  # Insert a new row
            # For each column in the row, create a QTableWidgetItem and insert into the table
            for col_index, value in enumerate(row):
                value = str(value) if isinstance(value, str) else f"{value:.2f}"
                table_item = QTableWidgetItem(str(value))
                self.analysis_table.setItem(row_position, col_index, table_item)
            row_position += 1

        # Update the table to show the contents
        self.analysis_table.resizeColumnsToContents()

    def save_ui_state(self):
        """Save the current state of UI elements"""
        # Save folder path
        Print("Saving UI state")
        self.state["last_folder"] = self.folder_path.text()
        self.state["worksheet_url"] = self.worksheet_url.text()
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

        Print("Switched to Forms and Quizzes Management tab")
        # Update the forms table, all the pages that are created should be added here and get the status of the page using self.grader.get_page_status( page )
        # From all the pages in the module folder
        folder = self.folder_path.text()
        folders_with_team = self.grader.get_folders_with_team(folder)
        self.local_projects_info: dict[str, tuple[List[str], PageSchema | None]] = {
            folder_path: (errors, None) for folder_path, errors in self.grader.verify_all_projects(folders_with_team)
        }  # Dict[dict[str, tuple[TeamInfo | None, List[str]]]. PATH, (team, errors)

        pages_posted_in_module = self.grader.get_pages_posted_in_module()  # List[PageSchema]

        for path, (errors, page) in self.local_projects_info.items():
            # Print(f"path: {path}, team: {team}, errors: {errors}")
            team_name = os.path.basename(path)
            team = self.grader.convert_student_record_sheets_to_team_info(team_name)  # TODO: Test this
            if not team:
                self.log("### not team - ? ####", log_type="WARN")
                continue
            if any(team.team_name == page.title for page in pages_posted_in_module):
                page = [page for page in pages_posted_in_module if page.title == team.team_name][0]
                status = self.grader.get_page_status(page)  # Literal['Created', 'Quiz and Feedback added', 'Done']
                Print(f" ###status = {status}")
                color = "green" if status == "Done" else "blue" if status == "Quiz and Feedback added" else "gray"
                self._add_quiz_table_row(
                    {
                        "LocalPath": path,
                        "PageName": page.title,
                        "Status": status,
                        "StatusColor": color,
                        "FontColor": "white",
                    }
                )
                # add this to self.local_projects_info
                self.local_projects_info[path] = (errors, page)
            else:
                self.log(f"Page {path} is not posted in the module", log_type="INFO")
                self._add_quiz_table_row(
                    {
                        "LocalPath": path,
                        "PageName": team.team_name,
                        "Status": "Not Added",
                        "StatusColor": "white",
                        "FontColor": "black",
                    }
                )
                # disable the checkbox
        # check for pages that are not in the module but in the folder
        # local_team_names = {team.team_name for _, (team, _, _) in self.local_projects_info.items() if team}
        # get local team names from spreadsheet self.grader.student_records ["Team_Name"]
        local_team_names = {record["Team_Name"] for record in self.grader.student_records}
        # Find pages that exist in Canvas but not locally
        for page in pages_posted_in_module:
            if page.title not in local_team_names:
                self._add_quiz_table_row(
                    {
                        "LocalPath": "",
                        "PageName": page.title,
                        "Status": "No Local Files",
                        "StatusColor": "red",
                        "FontColor": "white",
                    }
                )

    def on_pages_management_selected(self):
        # Add your logic here for what should happen when switching to Pages Management
        Print("Switched to Pages Management tab")
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
                        status_item.setBackground(self._COLOR_MAP["green"])
                        status_item.setForeground(self._COLOR_MAP["white"])
                        checkbox_item = self.pages_table.item(i, 0)
                        if checkbox_item:
                            checkbox_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Remove ItemIsUserCheckable
                            checkbox_item.setCheckState(Qt.CheckState.Unchecked)
                            checkbox_item.setToolTip("Cannot create page: Page already exists")
                            # checkbox_item.setBackground(Qt.GlobalColor.lightGray)  # Gray out the checkbox cell

                    self.pages_table.setItem(i, 2, status_item)

        except Exception as e:
            self.log(str(e), log_type="ERROR")

    def _add_quiz_table_row(self, data: QuizTableRowData) -> None:
        """Add a row to the quizzes table.

        Args:
            data: Dictionary containing the row data with predefined types.
                Must include:
                - LocalPath (str): Path to the quiz files
                - PageName (str): Name of the page
                - Status (str): Current status
                Optional:
                - StatusColor (str): Color for status ("red", "green", "gray", "yellow", "white")
                - FontColor (str): Color for text ("white", "black")

        Example:
            >>> self._add_quiz_table_row({
            ...     "LocalPath": "/path/to/quiz",
            ...     "PageName": "Team 1 Quiz",
            ...     "Status": "Not Added",
            ...     "StatusColor": "red",
            ...     "FontColor": "white"
            ... })
        """
        row = self.quizzes_table.rowCount()
        self.quizzes_table.insertRow(row)

        # Add checkbox
        checkbox = QTableWidgetItem()
        checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)

        # Only enable checkbox if status isn't "Done" and has local files
        if (
            data.get("Status") != "Done"
            and data.get("Status") != "No Local Files"
            and data.get("LocalPath")
            and data.get("Status") != "Not Added"
        ):
            checkbox.setCheckState(Qt.CheckState.Unchecked)
        else:  # or data['Status']=="Not Added"
            checkbox.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Disable checkbox
            checkbox.setCheckState(Qt.CheckState.Unchecked)

        self.quizzes_table.setItem(row, 0, checkbox)

        # Add other columns (shifted by 1)
        self.quizzes_table.setItem(row, 1, QTableWidgetItem(str(data.get("LocalPath", ""))))
        self.quizzes_table.setItem(row, 2, QTableWidgetItem(str(data.get("PageName", ""))))

        status_item = QTableWidgetItem(str(data.get("Status", "")))

        if "StatusColor" in data and "FontColor" in data:
            if data["StatusColor"] in self._COLOR_MAP and data["FontColor"] in self._COLOR_MAP:
                status_item.setBackground(self._COLOR_MAP[data["StatusColor"]])
                status_item.setForeground(self._COLOR_MAP[data["FontColor"]])
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
    window.logging_level = LogLevel.DEBUG
    #################################
    # running the log function after print
    original_print = Print

    def Print(*args, **kwargs):  # Overriding the Print function
        original_print(*args, **kwargs)
        window.log(*args, **kwargs)

    #################################

    sys.exit(app.exec())
