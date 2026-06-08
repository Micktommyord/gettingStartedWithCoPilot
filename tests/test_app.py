import copy
import sys
from pathlib import Path
from urllib.parse import quote

from fastapi.testclient import TestClient
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from app import app, activities  # noqa: E402


@pytest.fixture(autouse=True)
def preserve_activities():
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


def test_get_activities_returns_activities():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"
    assert data["Chess Club"]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_for_activity_adds_participant():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    email = "teststudent@mergington.edu"
    encoded_activity = quote(activity_name, safe="")

    # Act
    response = client.post(f"/activities/{encoded_activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_existing_participant_returns_400():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]
    encoded_activity = quote(activity_name, safe="")

    # Act
    response = client.post(f"/activities/{encoded_activity}/signup", params={"email": existing_email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_remove_participant_success():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    removable_email = activities[activity_name]["participants"][0]
    encoded_activity = quote(activity_name, safe="")
    encoded_email = quote(removable_email, safe="")

    # Act
    response = client.delete(f"/activities/{encoded_activity}/participants/{encoded_email}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {removable_email} from {activity_name}"}
    assert removable_email not in activities[activity_name]["participants"]


def test_remove_nonexistent_participant_returns_404():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    encoded_activity = quote(activity_name, safe="")
    encoded_email = quote("missingstudent@mergington.edu", safe="")

    # Act
    response = client.delete(f"/activities/{encoded_activity}/participants/{encoded_email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
