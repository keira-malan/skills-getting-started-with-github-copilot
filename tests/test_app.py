import copy
import urllib.parse

import pytest
from fastapi.testclient import TestClient

from src import app as application
from src.app import activities


client = TestClient(application.app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory `activities` mapping before each test so tests are isolated."""
    original = copy.deepcopy(activities)
    try:
        yield
    finally:
        activities.clear()
        activities.update(copy.deepcopy(original))


def get_activities():
    r = client.get("/activities")
    assert r.status_code == 200
    return r.json()


def test_get_activities_has_sample_keys():
    data = get_activities()
    assert "Chess Club" in data
    assert "Programming Class" in data


def test_signup_and_reflects_in_activities():
    email = "test_new_student@mergington.edu"
    activity = "Chess Club"

    # Ensure email not present
    act = get_activities()[activity]
    assert email not in act["participants"]

    # sign up
    url = f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(email)}"
    r = client.post(url)
    assert r.status_code == 200
    assert "Signed up" in r.json().get("message", "")

    # Confirm update visible via GET
    act2 = get_activities()[activity]
    assert email in act2["participants"]


def test_signup_duplicate_returns_400():
    email = "duplicate@mergington.edu"
    activity = "Programming Class"

    # first signup ok
    url = f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(email)}"
    r = client.post(url)
    assert r.status_code == 200

    # second signup should fail
    r2 = client.post(url)
    assert r2.status_code == 400
    assert "already signed up" in r2.json().get("detail", "")


def test_delete_participant_success():
    activity = "Chess Club"
    # existing participant from fixtures
    to_remove = activities[activity]["participants"][0]

    url = f"/activities/{urllib.parse.quote(activity)}/participants?email={urllib.parse.quote(to_remove)}"
    r = client.delete(url)
    assert r.status_code == 200
    assert "Removed" in r.json().get("message", "")

    # confirm removal
    assert to_remove not in get_activities()[activity]["participants"]


def test_delete_nonexistent_participant_returns_400():
    activity = "Soccer Team"
    email = "not_in_team@mergington.edu"
    url = f"/activities/{urllib.parse.quote(activity)}/participants?email={urllib.parse.quote(email)}"
    r = client.delete(url)
    assert r.status_code == 400
    assert "not signed up" in r.json().get("detail", "")


def test_signup_nonexistent_activity_is_404():
    activity = "Non Existent Activity"
    email = "someone@mergington.edu"
    url = f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(email)}"
    r = client.post(url)
    assert r.status_code == 404
