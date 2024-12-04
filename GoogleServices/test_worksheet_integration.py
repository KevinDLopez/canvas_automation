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


def test_read_worksheet(google_services: GoogleServicesManager, test_spreadsheet_id: str):
    """Test reading worksheet data"""
    spreadsheet = google_services.open_spreadsheet_by_id(test_spreadsheet_id)
    worksheet_data = google_services.read_worksheet(spreadsheet.get_worksheet(1))
    assert isinstance(worksheet_data, list)
    # Verify the worksheet has the expected structure
    if worksheet_data:
        assert isinstance(worksheet_data[0], dict)


@pytest.mark.skip(reason="This test will erase all data in the worksheet")
def test_update_worksheet_from_records(google_services: GoogleServicesManager, test_spreadsheet_id: str):
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
    spreadsheet = google_services.open_spreadsheet_by_id(test_spreadsheet_id)
    google_services.update_worksheet_from_records(spreadsheet.get_worksheet(1), test_records, append_only=False)

    updated_data = google_services.read_worksheet(spreadsheet.get_worksheet(1))
    assert len(updated_data) == 1
    assert updated_data[0]["Names"] == "Test Student"
    assert updated_data[0]["Team_Name"] == "Test Team"


def test_append_records(google_services: GoogleServicesManager, test_spreadsheet_id: str):
    """Test appending records to worksheet"""
    append_record = [
        {
            "Team_Name": "Append Team",
            "Names": "Append Student",
            "Email": "append@student.csulb.edu",
            "Student_ID": 1000,
            "Google_Form_ID": "append123",
        }
    ]
    spreadsheet = google_services.open_spreadsheet_by_id(test_spreadsheet_id)

    # Append the record
    google_services.update_worksheet_from_records(spreadsheet.get_worksheet(1), append_record, append_only=True)

    # Verify the append
    updated_data = google_services.read_worksheet(spreadsheet.get_worksheet(1))
    assert len(updated_data) > 1
    # The appended record should be the last one
    assert any(record["Names"] == "Append Student" for record in updated_data)
