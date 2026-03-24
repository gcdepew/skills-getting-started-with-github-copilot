"""
Comprehensive test suite for Mergington High School Activities API.
Tests follow the Arrange-Act-Assert (AAA) pattern.
"""

import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """
        Arrange: Client is ready
        Act: Make GET request to /activities
        Assert: Response status is 200 and contains all activities
        """
        # Arrange
        expected_activity_count = 9

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == expected_activity_count

    def test_get_activities_response_contains_required_fields(self, client, reset_activities):
        """
        Arrange: Client is ready
        Act: Make GET request to /activities
        Assert: Each activity has required fields (description, schedule, max_participants, participants)
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")

        # Assert
        activities = response.json()
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(activity_data.keys())

    def test_get_activities_participants_is_list(self, client, reset_activities):
        """
        Arrange: Client is ready
        Act: Make GET request to /activities
        Assert: Participants field is always a list (even if empty)
        """
        # Arrange & Act
        response = client.get("/activities")

        # Assert
        activities = response.json()
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["participants"], list)
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)

    def test_get_activities_availability_calculation(self, client, reset_activities):
        """
        Arrange: Chess Club has max_participants=12 and 2 current participants
        Act: Make GET request to /activities
        Assert: Can calculate spots left as max_participants - participants count
        """
        # Arrange
        expected_chess_club_max = 12
        expected_chess_club_participants = 2

        # Act
        response = client.get("/activities")

        # Assert
        activities = response.json()
        chess_club = activities["Chess Club"]
        assert chess_club["max_participants"] == expected_chess_club_max
        assert len(chess_club["participants"]) == expected_chess_club_participants
        spots_left = chess_club["max_participants"] - len(chess_club["participants"])
        assert spots_left == 10


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_successful_adds_participant(self, client, reset_activities):
        """
        Arrange: Select an activity and a new email
        Act: POST to signup endpoint with email
        Assert: Response status is 200, participant is added to activity
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        original_count = len(client.get("/activities").json()[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
        
        # Verify participant was actually added
        updated_activities = client.get("/activities").json()
        assert len(updated_activities[activity_name]["participants"]) == original_count + 1
        assert new_email in updated_activities[activity_name]["participants"]

    def test_signup_duplicate_email_returns_400(self, client, reset_activities):
        """
        Arrange: Try to signup with an email already in an activity
        Act: POST to signup endpoint with existing email
        Assert: Response status is 400 with appropriate error message
        """
        # Arrange
        activity_name = "Chess Club"
        duplicate_email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": duplicate_email}
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """
        Arrange: Try to signup for an activity that doesn't exist
        Act: POST to signup endpoint with fake activity name
        Assert: Response status is 404 with appropriate error message
        """
        # Arrange
        fake_activity = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{fake_activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_increments_participant_count(self, client, reset_activities):
        """
        Arrange: Get initial participant count for an activity
        Act: Signup 3 new participants one by one
        Assert: Participant count increases by 3
        """
        # Arrange
        activity_name = "Debate Team"
        new_emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        original_activities = client.get("/activities").json()
        original_count = len(original_activities[activity_name]["participants"])

        # Act
        for email in new_emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200

        # Assert
        updated_activities = client.get("/activities").json()
        final_count = len(updated_activities[activity_name]["participants"])
        assert final_count == original_count + 3

    def test_signup_response_message_format(self, client, reset_activities):
        """
        Arrange: Prepare valid signup data
        Act: POST to signup endpoint
        Assert: Response contains properly formatted success message
        """
        # Arrange
        activity_name = "Art Studio"
        email = "artlover@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert activity_name in data["message"]
        assert email in data["message"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participant endpoint."""

    def test_remove_participant_successful(self, client, reset_activities):
        """
        Arrange: Select an activity with existing participants
        Act: DELETE request to remove a participant
        Assert: Response status is 200, participant is removed
        """
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        original_count = len(client.get("/activities").json()[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participant",
            params={"email": email_to_remove}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email_to_remove} from {activity_name}"
        
        # Verify participant was actually removed
        updated_activities = client.get("/activities").json()
        assert len(updated_activities[activity_name]["participants"]) == original_count - 1
        assert email_to_remove not in updated_activities[activity_name]["participants"]

    def test_remove_nonexistent_participant_returns_400(self, client, reset_activities):
        """
        Arrange: Try to remove a participant who isn't in the activity
        Act: DELETE request with non-existent email
        Assert: Response status is 400 with appropriate error message
        """
        # Arrange
        activity_name = "Chess Club"
        nonexistent_email = "nothere@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participant",
            params={"email": nonexistent_email}
        )

        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_remove_from_nonexistent_activity_returns_404(self, client, reset_activities):
        """
        Arrange: Try to remove from an activity that doesn't exist
        Act: DELETE request with fake activity name
        Assert: Response status is 404 with appropriate error message
        """
        # Arrange
        fake_activity = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{fake_activity}/participant",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_remove_decrements_participant_count(self, client, reset_activities):
        """
        Arrange: Get initial participant count
        Act: Remove 2 participants from an activity
        Assert: Participant count decreases by 2
        """
        # Arrange
        activity_name = "Art Studio"
        emails_to_remove = ["grace@mergington.edu", "ethan@mergington.edu"]
        original_activities = client.get("/activities").json()
        original_count = len(original_activities[activity_name]["participants"])

        # Act
        for email in emails_to_remove:
            response = client.delete(
                f"/activities/{activity_name}/participant",
                params={"email": email}
            )
            assert response.status_code == 200

        # Assert
        updated_activities = client.get("/activities").json()
        final_count = len(updated_activities[activity_name]["participants"])
        assert final_count == original_count - 2

    def test_remove_then_readd_participant(self, client, reset_activities):
        """
        Arrange: Select a participant to remove then re-add
        Act: DELETE then POST the same participant
        Assert: Both operations succeed, participant is re-added
        """
        # Arrange
        activity_name = "Drama Club"
        email = "isabella@mergington.edu"

        # Act - Remove
        remove_response = client.delete(
            f"/activities/{activity_name}/participant",
            params={"email": email}
        )

        # Assert remove succeeded
        assert remove_response.status_code == 200
        activities_after_remove = client.get("/activities").json()
        assert email not in activities_after_remove[activity_name]["participants"]

        # Act - Re-add
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert re-add succeeded
        assert signup_response.status_code == 200
        activities_after_readd = client.get("/activities").json()
        assert email in activities_after_readd[activity_name]["participants"]


class TestRootRedirect:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_static_index(self, client):
        """
        Arrange: Client is ready
        Act: Make GET request to root path
        Assert: Response redirects to /static/index.html
        """
        # Arrange & Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]

    def test_root_redirect_follows_to_success(self, client):
        """
        Arrange: Client is ready
        Act: Make GET request to root path with redirect following
        Assert: Final response reaches the index page
        """
        # Arrange & Act
        response = client.get("/", follow_redirects=True)

        # Assert
        assert response.status_code == 200


class TestIntegrationScenarios:
    """Integration tests for complex scenarios combining multiple operations."""

    def test_full_signup_and_removal_workflow(self, client, reset_activities):
        """
        Arrange: Select an activity
        Act: Signup, verify, remove, verify again
        Assert: All operations succeed and state is correct
        """
        # Arrange
        activity_name = "Tennis Club"
        new_email = "tennisplayer@mergington.edu"
        original_activities = client.get("/activities").json()
        original_count = len(original_activities[activity_name]["participants"])

        # Act & Assert - Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        assert signup_response.status_code == 200
        activities_after_signup = client.get("/activities").json()
        assert len(activities_after_signup[activity_name]["participants"]) == original_count + 1
        assert new_email in activities_after_signup[activity_name]["participants"]

        # Act & Assert - Remove
        remove_response = client.delete(
            f"/activities/{activity_name}/participant",
            params={"email": new_email}
        )
        assert remove_response.status_code == 200
        activities_after_removal = client.get("/activities").json()
        assert len(activities_after_removal[activity_name]["participants"]) == original_count
        assert new_email not in activities_after_removal[activity_name]["participants"]

    def test_multiple_activities_independent_state(self, client, reset_activities):
        """
        Arrange: Select two different activities
        Act: Add participant to first activity, verify second is unaffected
        Assert: State changes are isolated per activity
        """
        # Arrange
        activity1 = "Chess Club"
        activity2 = "Basketball Team"
        email = "versatile@mergington.edu"
        
        activities_before = client.get("/activities").json()
        count_activity1_before = len(activities_before[activity1]["participants"])
        count_activity2_before = len(activities_before[activity2]["participants"])

        # Act - Add to activity 1
        response = client.post(
            f"/activities/{activity1}/signup",
            params={"email": email}
        )

        # Assert - Activity 1 changed, Activity 2 unchanged
        assert response.status_code == 200
        activities_after = client.get("/activities").json()
        assert len(activities_after[activity1]["participants"]) == count_activity1_before + 1
        assert len(activities_after[activity2]["participants"]) == count_activity2_before
