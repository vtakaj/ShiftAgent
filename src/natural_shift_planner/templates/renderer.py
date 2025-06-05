"""
HTML template renderer for schedule reports
"""
import os
from datetime import datetime
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader


def format_datetime(dt_str: str) -> str:
    """Format datetime string for display"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception:
        return dt_str


def format_time(dt_str: str) -> str:
    """Format time string for display"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M')
    except Exception:
        return dt_str


def calculate_duration_hours(start_time: str, end_time: str) -> str:
    """Calculate duration in hours between start and end times"""
    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        duration = end - start
        hours = duration.total_seconds() / 3600
        return f"{hours:.1f}"
    except Exception:
        return "N/A"


def get_priority_class(priority: int) -> str:
    """Get CSS class for priority level"""
    if priority <= 3:
        return "high"
    elif priority <= 7:
        return "medium"
    else:
        return "low"


class ScheduleReportRenderer:
    """HTML report renderer for shift schedules"""
    
    def __init__(self):
        # Get the templates directory path
        templates_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=True
        )
        
        # Add custom filters
        self.env.filters['format_datetime'] = format_datetime
        self.env.filters['format_time'] = format_time
    
    def render_schedule_report(self, schedule_data: Dict[str, Any], score: str = None) -> str:
        """
        Render schedule data as HTML report
        
        Args:
            schedule_data: Schedule data from convert_domain_to_response
            score: Optional optimization score
            
        Returns:
            HTML string
        """
        # Get the template
        template = self.env.get_template('schedule_report.html')
        
        # Process shifts to add calculated fields
        processed_shifts = []
        for shift in schedule_data.get('shifts', []):
            processed_shift = shift.copy()
            processed_shift['duration_hours'] = calculate_duration_hours(
                shift['start_time'], 
                shift['end_time']
            )
            processed_shift['priority_class'] = get_priority_class(shift['priority'])
            processed_shifts.append(processed_shift)
        
        # Prepare template context
        context = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'employees': schedule_data.get('employees', []),
            'shifts': processed_shifts,
            'statistics': schedule_data.get('statistics', {}),
            'score': score
        }
        
        # Render and return HTML
        return template.render(**context)


# Create a singleton instance
renderer = ScheduleReportRenderer()


def render_schedule_html(schedule_data: Dict[str, Any], score: str = None) -> str:
    """
    Convenience function to render schedule data as HTML
    
    Args:
        schedule_data: Schedule data from convert_domain_to_response
        score: Optional optimization score
        
    Returns:
        HTML string
    """
    return renderer.render_schedule_report(schedule_data, score)