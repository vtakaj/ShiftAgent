# PDF Report Migration Guide

This document outlines the migration from HTML to PDF reports in the Natural Shift Planner.

## Overview

As part of issue #12, PDF report generation has been added to provide better formatted, printable reports. The PDF functionality builds on the existing HTML templates while adding PDF-specific optimizations.

## What's New

### New Dependencies
- `weasyprint>=60.1` - HTML to PDF conversion
- `cairocffi>=1.6.1` - Required by WeasyPrint for rendering

### New API Endpoints

| Endpoint | Description | Response Type |
|----------|-------------|---------------|
| `GET /api/shifts/demo/pdf` | Demo schedule as PDF | PDF download |
| `GET /api/shifts/solve/{job_id}/pdf` | Optimization result as PDF | PDF download |
| `POST /api/shifts/solve-sync/pdf` | Synchronous solve with PDF output | PDF download |

### New MCP Tools

| Tool | Description | Returns |
|------|-------------|---------|
| `get_demo_schedule_pdf()` | Get demo schedule as PDF | PDF bytes |
| `get_schedule_pdf_report(job_id)` | Get completed schedule as PDF | PDF bytes |
| `solve_schedule_sync_pdf()` | Solve and return PDF in one step | PDF bytes |

## PDF Features

### Optimized for Print
- A4 page size with proper margins
- Page break handling for tables and sections
- Print-friendly fonts and sizing
- Removal of hover effects and animations

### Consistent Formatting
- Same visual design as HTML reports
- Professional layout suitable for sharing
- Timestamp-based filenames
- Automatic download headers

### Performance
- Reuses existing HTML templates
- Minimal overhead over HTML generation
- Streaming response for large files

## Migration Path

### Phase 1: Coexistence (Current)
Both HTML and PDF endpoints are available:
- HTML: `/api/shifts/demo/html`, `/api/shifts/solve/{job_id}/html`, `/api/shifts/solve-sync/html`
- PDF: `/api/shifts/demo/pdf`, `/api/shifts/solve/{job_id}/pdf`, `/api/shifts/solve-sync/pdf`

### Phase 2: Client Migration (Future)
Clients should migrate to PDF endpoints for:
- Reports that need to be saved or shared
- Formal documentation purposes
- Printing requirements

### Phase 3: HTML Deprecation (Future)
HTML endpoints may be deprecated if PDF fully meets all use cases.

## Usage Examples

### API Usage
```bash
# Get demo schedule as PDF
curl -o demo_schedule.pdf http://localhost:8081/api/shifts/demo/pdf

# Get optimization result as PDF
curl -o schedule.pdf http://localhost:8081/api/shifts/solve/{job_id}/pdf

# Synchronous solve with PDF output
curl -X POST -H "Content-Type: application/json" \
  -d @schedule_request.json \
  -o optimized_schedule.pdf \
  http://localhost:8081/api/shifts/solve-sync/pdf
```

### MCP Usage
```python
# Get demo PDF
pdf_bytes = await get_demo_schedule_pdf(ctx)

# Get completed schedule PDF
pdf_bytes = await get_schedule_pdf_report(ctx, job_id)

# Solve and get PDF in one step
pdf_bytes = await solve_schedule_sync_pdf(ctx, employees, shifts)
```

## Technical Details

### PDF Generation Process
1. Generate HTML using existing templates
2. Apply PDF-specific CSS modifications
3. Convert HTML to PDF using WeasyPrint
4. Return PDF bytes for streaming

### File Naming Convention
- Demo schedules: `demo_shift_schedule_{timestamp}.pdf`
- Optimization results: `shift_schedule_{job_id}_{timestamp}.pdf`
- Synchronous solves: `optimized_shift_schedule_{timestamp}.pdf`

### Error Handling
PDF generation errors are handled gracefully:
- Invalid schedule data → 500 error with details
- Missing jobs → 404 error
- WeasyPrint errors → 500 error with technical details

## Testing

The implementation includes comprehensive tests:
- Basic PDF generation from demo data
- PDF generation with optimization scores
- Empty schedule handling
- Stream compatibility
- Format validation

Run tests with:
```bash
make test
# or
uv run pytest tests/test_pdf_reports.py -v
```

## Dependencies Installation

The new dependencies are automatically installed with:
```bash
make setup
# or
uv sync
```

## Troubleshooting

### Common Issues

1. **WeasyPrint Installation Errors**
   - Ensure system dependencies are installed (Cairo, Pango)
   - Check Python version compatibility (3.11+)

2. **PDF Generation Fails**
   - Verify schedule data format
   - Check WeasyPrint logs for HTML/CSS issues

3. **Large File Performance**
   - PDF generation is memory-intensive for large schedules
   - Consider pagination for very large schedules

### System Requirements
- Python 3.11+
- Cairo graphics library
- Pango text rendering library
- Sufficient memory for PDF rendering

## Future Enhancements

Potential improvements for PDF reports:
- Custom page headers/footers
- Multi-page table headers
- Chart/graph integration
- Custom styling options
- Batch PDF generation

## Support

For issues with PDF generation:
1. Check this migration guide
2. Review error logs for WeasyPrint messages
3. Test with demo data to isolate issues
4. Verify dependencies are properly installed