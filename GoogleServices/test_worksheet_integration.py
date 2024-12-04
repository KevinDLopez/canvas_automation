import pytest
from GoogleServices.GoogleServices import GoogleServicesManager
import os
import json


@pytest.fixture(scope="module")
def google_services():
    return GoogleServicesManager()


@pytest.fixture(scope="module")
def test_spreadsheet_id():
    return "1tuuIobh2R4KQJBxCPR60E0EFVW_jr9_l6Aaj3lx6qaQ"


def test_open_spreadsheet_by_id(google_services, test_spreadsheet_id):
    """Test opening a spreadsheet by ID"""
    spreadsheet = google_services.open_spreadsheet_by_id(test_spreadsheet_id)
    assert spreadsheet is not None
    assert spreadsheet.id == test_spreadsheet_id


def test_read_worksheet(google_services, test_spreadsheet_id):
    """Test reading worksheet data"""
    spreadsheet = google_services.open_spreadsheet_by_id(test_spreadsheet_id)
    worksheet_data = google_services.read_worksheet(spreadsheet, "Sheet1")
    assert isinstance(worksheet_data, list)
    # Verify the worksheet has the expected structure
    if worksheet_data:
        assert isinstance(worksheet_data[0], dict)


def test_update_worksheet_from_records(google_services, test_spreadsheet_id):
    """Test updating worksheet with new records"""
    test_records = [
        {
            "Student Name": "Test Student",
            "Team Name": "Test Team",
            "Student Email": "test@student.csulb.edu",
            "ID": 999,
            "FormID": "test123",
        }
    ]

    # Update the worksheet
    google_services.update_worksheet_from_records(test_spreadsheet_id, "Sheet1", test_records, append_only=False)

    # Verify the update
    spreadsheet = google_services.open_spreadsheet_by_id(test_spreadsheet_id)
    updated_data = google_services.read_worksheet(spreadsheet, "Sheet1")
    assert len(updated_data) == 1
    assert updated_data[0]["Student Name"] == "Test Student"
    assert updated_data[0]["Team Name"] == "Test Team"


def test_append_records(google_services, test_spreadsheet_id):
    """Test appending records to worksheet"""
    append_record = [
        {
            "Student Name": "Append Student",
            "Team Name": "Append Team",
            "Student Email": "append@student.csulb.edu",
            "ID": 1000,
            "FormID": "append123",
        }
    ]

    # Append the record
    google_services.update_worksheet_from_records(test_spreadsheet_id, "Sheet1", append_record, append_only=True)

    # Verify the append
    spreadsheet = google_services.open_spreadsheet_by_id(test_spreadsheet_id)
    updated_data = google_services.read_worksheet(spreadsheet, "Sheet1")
    assert len(updated_data) > 1
    # The appended record should be the last one
    assert any(record["Student Name"] == "Append Student" for record in updated_data)
