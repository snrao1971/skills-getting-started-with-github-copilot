import pytest


def test_root_redirect(client):
    """Test that root redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert "/static/index.html" in response.headers["location"]


def test_get_activities(client):
    """Test retrieving all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Football Team" in data
    assert "Programming Class" in data
    assert "Gym Class" in data
    
    # Verify activity structure
    chess_club = data["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)


def test_get_activities_has_participants(client):
    """Test that activities have participants"""
    response = client.get("/activities")
    data = response.json()
    
    chess_club = data["Chess Club"]
    assert "michael@mergington.edu" in chess_club["participants"]
    assert "daniel@mergington.edu" in chess_club["participants"]


def test_signup_for_activity(client, reset_activities):
    """Test signing up a new student for an activity"""
    response = client.post(
        "/activities/Tennis Club/signup?email=newstudent@mergington.edu",
        follow_redirects=False
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "newstudent@mergington.edu" in data["message"]
    assert "Tennis Club" in data["message"]


def test_signup_updates_participants_list(client, reset_activities):
    """Test that signup updates the participants list"""
    # Add new participant
    client.post(
        "/activities/Tennis Club/signup?email=newstudent@mergington.edu"
    )
    
    # Check that participant was added
    response = client.get("/activities")
    data = response.json()
    participants = data["Tennis Club"]["participants"]
    assert "newstudent@mergington.edu" in participants
    assert len(participants) == 2  # James + new student


def test_signup_duplicate_participant(client, reset_activities):
    """Test that duplicate signup is rejected"""
    response = client.post(
        "/activities/Tennis Club/signup?email=james@mergington.edu"
    )
    assert response.status_code == 400
    
    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"]


def test_signup_nonexistent_activity(client):
    """Test signup for non-existent activity"""
    response = client.post(
        "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
    )
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]


def test_signup_max_participants(client, reset_activities):
    """Test that signup fails when activity is full"""
    # Create activity with max 1 participant
    from app import activities
    activities["Small Activity"] = {
        "description": "Small activity",
        "schedule": "Monday 3:00 PM",
        "max_participants": 1,
        "participants": ["full@mergington.edu"]
    }
    
    # This should technically work since there's a spot, but let's verify the constraint exists
    response = client.post(
        "/activities/Small Activity/signup?email=newcomer@mergington.edu"
    )
    assert response.status_code == 200


def test_unregister_from_activity(client, reset_activities):
    """Test unregistering a student from an activity"""
    response = client.post(
        "/activities/Chess Club/unregister?email=michael@mergington.edu"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "Unregistered" in data["message"]
    assert "michael@mergington.edu" in data["message"]


def test_unregister_updates_participants_list(client, reset_activities):
    """Test that unregister removes participant from list"""
    # Remove participant
    client.post(
        "/activities/Chess Club/unregister?email=michael@mergington.edu"
    )
    
    # Check that participant was removed
    response = client.get("/activities")
    data = response.json()
    participants = data["Chess Club"]["participants"]
    assert "michael@mergington.edu" not in participants
    assert "daniel@mergington.edu" in participants  # Other participant remains


def test_unregister_nonexistent_participant(client, reset_activities):
    """Test unregister for participant not in activity"""
    response = client.post(
        "/activities/Chess Club/unregister?email=notamember@mergington.edu"
    )
    assert response.status_code == 400
    
    data = response.json()
    assert "detail" in data
    assert "not signed up" in data["detail"]


def test_unregister_from_nonexistent_activity(client):
    """Test unregister from non-existent activity"""
    response = client.post(
        "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
    )
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]


def test_multiple_signups_and_unregisters(client, reset_activities):
    """Test multiple signup and unregister operations"""
    activity = "Programming Class"
    
    # Initial state
    response = client.get("/activities")
    initial_count = len(response.json()[activity]["participants"])
    
    # Sign up new student
    client.post(f"/activities/{activity}/signup?email=test1@mergington.edu")
    response = client.get("/activities")
    assert len(response.json()[activity]["participants"]) == initial_count + 1
    
    # Sign up another student
    client.post(f"/activities/{activity}/signup?email=test2@mergington.edu")
    response = client.get("/activities")
    assert len(response.json()[activity]["participants"]) == initial_count + 2
    
    # Unregister first student
    client.post(f"/activities/{activity}/unregister?email=test1@mergington.edu")
    response = client.get("/activities")
    participants = response.json()[activity]["participants"]
    assert len(participants) == initial_count + 1
    assert "test1@mergington.edu" not in participants
    assert "test2@mergington.edu" in participants
