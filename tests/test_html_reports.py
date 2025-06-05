"""
Tests for HTML report generation
"""
import pytest
from datetime import datetime

from src.natural_shift_planner.templates.renderer import render_schedule_html


def test_render_schedule_html():
    """Test HTML report rendering with sample data"""
    # Sample schedule data that matches the API response format
    schedule_data = {
        "employees": [
            {
                "id": "emp1",
                "name": "Alice Smith",
                "skills": ["cashier", "customer_service"]
            },
            {
                "id": "emp2", 
                "name": "Bob Johnson",
                "skills": ["cook", "kitchen_prep"]
            }
        ],
        "shifts": [
            {
                "id": "shift1",
                "start_time": "2024-01-15T09:00:00",
                "end_time": "2024-01-15T17:00:00",
                "required_skills": ["cashier"],
                "location": "Front Desk",
                "priority": 3,
                "employee": {
                    "id": "emp1",
                    "name": "Alice Smith"
                }
            },
            {
                "id": "shift2",
                "start_time": "2024-01-15T10:00:00",
                "end_time": "2024-01-15T18:00:00", 
                "required_skills": ["cook"],
                "location": "Kitchen",
                "priority": 5,
                "employee": {
                    "id": "emp2",
                    "name": "Bob Johnson"
                }
            },
            {
                "id": "shift3",
                "start_time": "2024-01-15T14:00:00",
                "end_time": "2024-01-15T22:00:00",
                "required_skills": ["cashier"],
                "location": "Front Desk",
                "priority": 7,
                "employee": None  # Unassigned
            }
        ],
        "statistics": {
            "total_employees": 2,
            "total_shifts": 3,
            "assigned_shifts": 2,
            "unassigned_shifts": 1
        }
    }
    
    # Render HTML
    html = render_schedule_html(schedule_data, score="0hard/0medium/0soft")
    
    # Basic structure checks
    assert "<!DOCTYPE html>" in html
    assert "<title>Shift Schedule Report</title>" in html
    assert "Alice Smith" in html
    assert "Bob Johnson" in html
    assert "Front Desk" in html
    assert "Kitchen" in html
    assert "cashier" in html
    assert "cook" in html
    assert "Unassigned" in html
    
    # Statistics check
    assert "2" in html  # total employees
    assert "3" in html  # total shifts
    
    # CSS and styling
    assert "font-family:" in html
    assert ".container" in html
    assert ".stat-card" in html
    
    # Responsive design
    assert "@media (max-width: 768px)" in html


def test_render_empty_schedule():
    """Test rendering with minimal data"""
    schedule_data = {
        "employees": [],
        "shifts": [],
        "statistics": {
            "total_employees": 0,
            "total_shifts": 0,
            "assigned_shifts": 0,
            "unassigned_shifts": 0
        }
    }
    
    html = render_schedule_html(schedule_data)
    
    # Should still render properly
    assert "<!DOCTYPE html>" in html
    assert "Shift Schedule Report" in html
    assert "0" in html  # zero statistics


def test_render_with_score():
    """Test rendering with optimization score"""
    schedule_data = {
        "employees": [],
        "shifts": [],
        "statistics": {
            "total_employees": 0,
            "total_shifts": 0,
            "assigned_shifts": 0,
            "unassigned_shifts": 0
        }
    }
    
    score = "5hard/10medium/15soft"
    html = render_schedule_html(schedule_data, score)
    
    assert score in html
    assert "Optimization Score:" in html


if __name__ == "__main__":
    pytest.main([__file__])