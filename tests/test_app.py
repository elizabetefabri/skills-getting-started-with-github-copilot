"""
Tests for the FastAPI Mergington High School Activities application
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities(self):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        assert "Chess Club" in activities
        assert "Programming Class" in activities

    def test_activities_structure(self):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_details in activities.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_activities_participants(self):
        """Test that participants list contains expected values"""
        response = client.get("/activities")
        activities = response.json()
        
        chess_club = activities["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""

    def test_successful_signup(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Art Studio/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "newstudent@mergington.edu" in result["message"]
        assert "Art Studio" in result["message"]

    def test_signup_duplicate_email(self):
        """Test that duplicate signup is rejected"""
        # First signup
        response1 = client.post(
            "/activities/Tennis Club/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200

        # Duplicate signup attempt
        response2 = client.post(
            "/activities/Tennis Club/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        result = response2.json()
        assert "already signed up" in result["detail"]

    def test_signup_nonexistent_activity(self):
        """Test signup for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"]

    def test_signup_existing_participant(self):
        """Test signup for an existing participant"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"]


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister endpoint"""

    def test_successful_unregister(self):
        """Test successful unregister from an activity"""
        # First signup
        client.post("/activities/Drama Club/signup?email=testuser@mergington.edu")

        # Then unregister
        response = client.delete(
            "/activities/Drama Club/unregister?email=testuser@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "testuser@mergington.edu" in result["message"]
        assert "Drama Club" in result["message"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister from a non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"]

    def test_unregister_not_registered(self):
        """Test unregister for a student not registered in the activity"""
        response = client.delete(
            "/activities/Basketball Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        result = response.json()
        assert "not registered" in result["detail"]

    def test_unregister_existing_participant(self):
        """Test unregister an existing participant"""
        response = client.delete(
            "/activities/Basketball Team/unregister?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "alex@mergington.edu" not in activities["Basketball Team"]["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self):
        """Test that root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestIntegration:
    """Integration tests"""

    def test_full_signup_and_unregister_flow(self):
        """Test complete flow: signup and then unregister"""
        activity = "Debate Team"
        email = "integration@mergington.edu"

        # Get initial participant count
        response1 = client.get("/activities")
        initial_count = len(response1.json()[activity]["participants"])

        # Signup
        response2 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response2.status_code == 200

        # Check participant was added
        response3 = client.get("/activities")
        assert email in response3.json()[activity]["participants"]
        assert len(response3.json()[activity]["participants"]) == initial_count + 1

        # Unregister
        response4 = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response4.status_code == 200

        # Check participant was removed
        response5 = client.get("/activities")
        assert email not in response5.json()[activity]["participants"]
        assert len(response5.json()[activity]["participants"]) == initial_count

    def test_multiple_signups(self):
        """Test multiple students signing up for different activities"""
        signups = [
            ("Science Club", "student1@mergington.edu"),
            ("Science Club", "student2@mergington.edu"),
            ("Gym Class", "student3@mergington.edu"),
        ]

        for activity, email in signups:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200

        # Verify all signups were successful
        response = client.get("/activities")
        activities = response.json()
        assert "student1@mergington.edu" in activities["Science Club"]["participants"]
        assert "student2@mergington.edu" in activities["Science Club"]["participants"]
        assert "student3@mergington.edu" in activities["Gym Class"]["participants"]
