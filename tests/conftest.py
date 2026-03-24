import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy


@pytest.fixture
def client():
    """Provide a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def fresh_activities():
    """
    Provide a fresh copy of activities for each test.
    Resets the module-level activities dict before and after each test.
    """
    # Save original activities
    original_activities = copy.deepcopy(activities)
    
    # Clear and reset to original state before test
    activities.clear()
    activities.update(original_activities)
    
    yield activities
    
    # Restore original activities after test
    activities.clear()
    activities.update(original_activities)
