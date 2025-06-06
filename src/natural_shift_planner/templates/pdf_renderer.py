"""
PDF report renderer for schedule reports using WeasyPrint
"""

import io
from datetime import datetime
from typing import Any, Dict

import weasyprint

from .renderer import ScheduleReportRenderer


class SchedulePDFRenderer:
    """PDF report renderer for shift schedules"""

    def __init__(self):
        self.html_renderer = ScheduleReportRenderer()

    def generate_pdf(self, schedule_data: Dict[str, Any], score: str = None) -> bytes:
        """
        Generate PDF from schedule data

        Args:
            schedule_data: Schedule data from convert_domain_to_response
            score: Optional optimization score

        Returns:
            PDF content as bytes
        """
        # First render as HTML
        html_content = self.html_renderer.render_schedule_report(schedule_data, score)

        # Apply PDF-specific CSS modifications
        pdf_html = self._modify_html_for_pdf(html_content)

        # Generate PDF using WeasyPrint
        html_doc = weasyprint.HTML(string=pdf_html)
        pdf_bytes = html_doc.write_pdf()

        return pdf_bytes

    def _modify_html_for_pdf(self, html_content: str) -> str:
        """
        Modify HTML content for better PDF rendering

        Args:
            html_content: Original HTML content

        Returns:
            Modified HTML content optimized for PDF
        """
        # Add PDF-specific CSS
        pdf_css = """
        <style>
        /* PDF-specific styles */
        @page {
            size: A4;
            margin: 1cm;
        }
        
        body {
            background-color: white !important;
        }
        
        .container {
            max-width: none;
            margin: 0;
            box-shadow: none;
            border-radius: 0;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            page-break-inside: avoid;
        }
        
        .stats-grid {
            page-break-inside: avoid;
        }
        
        .section {
            page-break-inside: avoid;
        }
        
        .section h2 {
            page-break-after: avoid;
        }
        
        .employee-card {
            page-break-inside: avoid;
            margin-bottom: 10px;
        }
        
        .schedule-table {
            page-break-inside: auto;
        }
        
        .schedule-table thead {
            display: table-header-group;
        }
        
        .schedule-table tr {
            page-break-inside: avoid;
        }
        
        /* Ensure readable text in PDF */
        body {
            font-size: 10pt;
            line-height: 1.4;
        }
        
        .header h1 {
            font-size: 24pt;
        }
        
        .stat-value {
            font-size: 18pt;
        }
        
        .section h2 {
            font-size: 14pt;
        }
        
        /* Remove hover effects for PDF */
        .schedule-table tr:hover {
            background: inherit;
        }
        
        /* Better table spacing for PDF */
        .schedule-table th,
        .schedule-table td {
            padding: 8px;
            font-size: 9pt;
        }
        
        /* Responsive adjustments for PDF */
        @media print {
            .stats-grid {
                grid-template-columns: repeat(4, 1fr);
            }
            
            .employees-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        </style>
        """

        # Insert PDF CSS before the closing </head> tag
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", pdf_css + "\n</head>")

        return html_content


# Create a singleton instance
pdf_renderer = SchedulePDFRenderer()


def generate_schedule_pdf(schedule_data: Dict[str, Any], score: str = None) -> bytes:
    """
    Convenience function to generate PDF from schedule data

    Args:
        schedule_data: Schedule data from convert_domain_to_response
        score: Optional optimization score

    Returns:
        PDF content as bytes
    """
    return pdf_renderer.generate_pdf(schedule_data, score)
