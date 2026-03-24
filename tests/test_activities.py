import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


class TestGetActivities:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities_with_correct_structure(self, client, fresh_activities):
        """
        Arrange: Activities are loaded in the app
        Act: Make GET request to /activities
        Assert: Response returns all activities with correct structure
        """
        # Arrange
        expected_activity_count = len(fresh_activities)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == expected_activity_count
        
        # Verify structure of first activity
        data = response.json()
        first_activity = data["Chess Club"]
        assert "description" in first_activity
        assert "schedule" in first_activity
        assert "max_participants" in first_activity
        assert "participants" in first_activity
        assert isinstance(first_activity["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_successful_signup(self, client, fresh_activities):
        """
        Arrange: A new student email and valid activity
        Act: Sign up for the activity
        Assert: Student is added to participants and success message returned
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in fresh_activities["Chess Club"]["participants"]
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    
    def test_signup_activity_not_found(self, client, fresh_activities):
        """
        Arrange: Non-existent activity name
        Act: Attempt to sign up
        Assert: 404 error returned
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_duplicate_email(self, client, fresh_activities):
        """
        Arrange: Student already signed up for activity
        Act: Attempt to sign up again
        Assert: 400 error returned
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_increments_participant_count(self, client, fresh_activities):
        """
        Arrange: Get initial participant count
        Act: Sign up a new student
        Assert: Participant count increments by 1
        """
        # Arrange
        activity_name = "Programming Class"
        email = "newstudent@mergington.edu"
        initial_count = len(fresh_activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert len(fresh_activities[activity_name]["participants"]) == initial_count + 1
    
    def test_signup_multiple_students_same_activity(self, client, fresh_activities):
        """
        Arrange: Multiple new student emails
        Act: Sign up multiple students to same activity
        Assert: All students added successfully in order
        """
        # Arrange
        activity_name = "Art Studio"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        initial_count = len(fresh_activities[activity_name]["participants"])
        
        # Act & Assert
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Assert final state
        assert len(fresh_activities[activity_name]["participants"]) == initial_count + len(emails)
        for email in emails:
            assert email in fresh_activities[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint."""
    
    def test_successful_unregister(self, client, fresh_activities):
        """
        Arrange: A student signed up for an activity
        Act: Unregister the student
        Assert: Student is removed and success message returned
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email not in fresh_activities["Chess Club"]["participants"]
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    
    def test_unregister_activity_not_found(self, client, fresh_activities):
        """
        Arrange: Non-existent activity name
        Act: Attempt to unregister
        Assert: 404 error returned
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "someone@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_participant_not_signed_up(self, client, fresh_activities):
        """
        Arrange: Student not signed up for activity
        Act: Attempt to unregister
        Assert: 400 error returned
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notstudent@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_decrements_participant_count(self, client, fresh_activities):
        """
        Arrange: Get initial participant count
        Act: Unregister a student
        Assert: Participant count decrements by 1
        """
        # Arrange
        activity_name = "Debate Club"
        email = "alex@mergington.edu"  # Already signed up
        initial_count = len(fresh_activities[activity_name]["participants"])
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert len(fresh_activities[activity_name]["participants"]) == initial_count - 1
    
    def test_unregister_then_re_signup(self, client, fresh_activities):
        """
        Arrange: Student signed up for activity
        Act: Unregister then sign up again
        Assert: Student can be re-added after removal
        """
        # Arrange
        activity_name = "Tennis Club"
        email = "natalie@mergington.edu"
        
        # Act - Unregister
        response1 = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        assert email not in fresh_activities[activity_name]["participants"]
        
        # Act - Re-signup
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response2.status_code == 200
        assert email in fresh_activities[activity_name]["participants"]
