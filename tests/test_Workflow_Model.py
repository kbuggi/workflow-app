# to run:  pytest test_Workflow_Model.py

import pytest
from Workflow_Model import WorkflowStream, Task, Checklist, Helper, Live
import jsonc


def test_task_creation():
    """Test basic task creation and attribute setting"""
    task_dict = {
        "Title": "Test_Task",
        "Type": "Active",
        "Stakes": "Low",
        "Steps": ["Step 1", "Step 2"],
        "DurationSeconds": 60,
    }
    task = Task("TestTask", task_dict)
    assert task.title == "Test_Task"
    assert task.duration == 60
    assert task.steps == ["Step 1", "Step 2"]
    assert task.stakes == "Low"
    assert task.type == "Active"


def test_task_validation():
    """Test task name validation"""
    task_dict = {"Title": "Test"}
    with pytest.raises(ValueError):
        Task("Invalid Name!", task_dict)  # Invalid character !


def test_checklist_creation():
    """Test checklist creation and validation"""
    checklist_dict = {"Description": "Test Checklist", "Steps": ["Check 1", "Check 2"]}
    checklist = Checklist("Test_Checklist", checklist_dict)
    assert checklist.name == "Test_Checklist"
    assert checklist.description == "Test Checklist"


def test_live_state():
    """Test Live class state management"""
    live = Live()
    live.remaining_time = 60
    live.duration = 60
    live.extend_count = 0

    assert live.remaining_time == 60
    assert live.duration == 60
    assert live.extend_count == 0


def test_helper_validation():
    """Test Helper class validation methods"""
    assert Helper._is_name_OK("Valid_Name") == True
    assert Helper._is_name_OK("Invalid Name") == False
    assert Helper._is_name_OK("Invalid!Name") == False


def test_workflow_validation():
    """Test workflow validation"""
    invalid_workflow = {
        "Identity": {"Type": "Recipe", "Name": "Test Recipe"}
        # Missing required GoStream
    }
    with pytest.raises(ValueError):
        WorkflowStream("test.jsonc", invalid_workflow)


def test_workflow_creation():
    """Test basic workflow creation"""
    workflow_dict = {
        "Identity": {"Type": "Recipe", "Name": "Test Recipe"},
        "GoStream": "MainStream",
        "PreFlight": {"Description": "Test PreFlight"},
        "PostFlight": {"Description": "Test PostFlight"},
        "Streams": {"MainStream": {"Settings": {"Title": "Main Stream"}}},
    }
    workflow = WorkflowStream("test.jsonc", workflow_dict)
    assert workflow.name == "Test Recipe"
    assert workflow.go_stream_name == "MainStream"
