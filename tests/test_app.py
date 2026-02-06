"""Tests for the Mergington High School API."""

import pytest


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary of activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0

    def test_get_activities_contains_expected_activities(self, client):
        """Test that activities contain required fields."""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_details in activities.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_has_known_activities(self, client):
        """Test that specific known activities exist."""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Science Club",
        ]
        
        for activity in expected_activities:
            assert activity in activities


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_for_valid_activity(self, client):
        """Test successful signup for a valid activity."""
        email = "newstudent@mergington.edu"
        activity = "Basketball Team"
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity]["participants"].copy()
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
        
        # Verify participant was added
        verify_response = client.get("/activities")
        updated_participants = verify_response.json()[activity]["participants"]
        assert email in updated_participants
        assert len(updated_participants) == len(initial_participants) + 1

    def test_signup_already_registered(self, client):
        """Test signup fails for already registered student."""
        email = "alex@mergington.edu"  # Already registered for Basketball Team
        activity = "Basketball Team"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_for_invalid_activity(self, client):
        """Test signup fails for non-existent activity."""
        email = "student@mergington.edu"
        activity = "NonExistentActivity"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_multiple_different_activities(self, client):
        """Test a student can sign up for multiple activities."""
        email = "multistudent@mergington.edu"
        activities = ["Basketball Team", "Tennis Club"]
        
        for activity in activities:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify student is in both activities
        verify_response = client.get("/activities")
        activities_data = verify_response.json()
        
        for activity in activities:
            assert email in activities_data[activity]["participants"]


class TestUnregisterEndpoint:
    """Tests for POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_registered_participant(self, client):
        """Test successful unregistration of a participant."""
        email = "testunregister@mergington.edu"
        activity = "Drama Club"
        
        # First, sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Then unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        assert unregister_response.status_code == 200
        data = unregister_response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
        
        # Verify participant was removed
        verify_response = client.get("/activities")
        participants = verify_response.json()[activity]["participants"]
        assert email not in participants

    def test_unregister_not_registered_participant(self, client):
        """Test unregister fails for non-registered participant."""
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()

    def test_unregister_from_invalid_activity(self, client):
        """Test unregister fails for non-existent activity."""
        email = "student@mergington.edu"
        activity = "NonExistentActivity"
        
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_then_unregister_cycle(self, client):
        """Test complete signup and unregister cycle."""
        email = "cycletest@mergington.edu"
        activity = "Debate Team"
        
        # Initial state
        initial = client.get("/activities").json()[activity]["participants"].copy()
        assert email not in initial
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify signed up
        after_signup = client.get("/activities").json()[activity]["participants"]
        assert email in after_signup
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistered
        after_unregister = client.get("/activities").json()[activity]["participants"]
        assert email not in after_unregister
