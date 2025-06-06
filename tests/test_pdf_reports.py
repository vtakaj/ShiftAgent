"""
Tests for PDF report generation functionality
"""

import io

import pytest

from src.natural_shift_planner.api.converters import convert_domain_to_response
from src.natural_shift_planner.templates.pdf_renderer import generate_schedule_pdf
from src.natural_shift_planner.utils.demo_data import create_demo_schedule


def test_pdf_generation_basic():
    """Test basic PDF generation from demo data"""
    # Create demo schedule
    schedule = create_demo_schedule()
    schedule_data = convert_domain_to_response(schedule)
    score = str(schedule.score) if schedule.score else None

    # Generate PDF
    pdf_content = generate_schedule_pdf(schedule_data, score)

    # Verify PDF content
    assert isinstance(pdf_content, bytes)
    assert len(pdf_content) > 0

    # Check PDF magic bytes (PDF files start with %PDF)
    assert pdf_content.startswith(b"%PDF")


def test_pdf_generation_with_score():
    """Test PDF generation with optimization score"""
    schedule = create_demo_schedule()
    schedule_data = convert_domain_to_response(schedule)
    score = "Hard: 0, Medium: -5, Soft: -123"

    pdf_content = generate_schedule_pdf(schedule_data, score)

    assert isinstance(pdf_content, bytes)
    assert len(pdf_content) > 0
    assert pdf_content.startswith(b"%PDF")


def test_pdf_generation_empty_schedule():
    """Test PDF generation with minimal schedule data"""
    minimal_data = {
        "employees": [],
        "shifts": [],
        "statistics": {
            "total_employees": 0,
            "total_shifts": 0,
            "assigned_shifts": 0,
            "unassigned_shifts": 0,
        },
    }

    pdf_content = generate_schedule_pdf(minimal_data)

    assert isinstance(pdf_content, bytes)
    assert len(pdf_content) > 0
    assert pdf_content.startswith(b"%PDF")


def test_pdf_stream_handling():
    """Test that PDF content can be handled as stream"""
    schedule = create_demo_schedule()
    schedule_data = convert_domain_to_response(schedule)

    pdf_content = generate_schedule_pdf(schedule_data)

    # Test creating BytesIO stream
    pdf_stream = io.BytesIO(pdf_content)
    assert pdf_stream.getvalue() == pdf_content

    # Test stream positioning
    pdf_stream.seek(0)
    first_chunk = pdf_stream.read(4)
    assert first_chunk == b"%PDF"


@pytest.mark.parametrize("include_score", [True, False])
def test_pdf_content_variations(include_score):
    """Test PDF generation with and without scores"""
    schedule = create_demo_schedule()
    schedule_data = convert_domain_to_response(schedule)

    score = "Test Score: -100" if include_score else None
    pdf_content = generate_schedule_pdf(schedule_data, score)

    assert isinstance(pdf_content, bytes)
    assert len(pdf_content) > 0
    assert pdf_content.startswith(b"%PDF")


if __name__ == "__main__":
    pytest.main([__file__])
