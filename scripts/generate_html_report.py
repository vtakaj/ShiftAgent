#!/usr/bin/env python3
"""
Simple script to generate HTML report from completed job
"""

import asyncio
import sys
import webbrowser
from pathlib import Path

import httpx


async def generate_html_report(job_id: str, api_url: str = "http://localhost:8081"):
    """Generate HTML report and save to file"""
    try:
        url = f"{api_url}/api/shifts/solve/{job_id}/html"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            html_content = response.text

        # Save to file
        output_path = Path(f"shift_report_{job_id}.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"✅ HTML report saved to: {output_path.absolute()}")

        # Ask if user wants to open in browser
        try:
            open_browser = input("Open in browser? (y/N): ").lower().strip()
            if open_browser in ["y", "yes"]:
                webbrowser.open(f"file://{output_path.absolute()}")
                print("🌐 Opened in browser")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")

        return str(output_path.absolute())

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print(f"❌ Error: Job {job_id} not found")
        elif e.response.status_code == 400:
            print(f"❌ Error: Job {job_id} not completed yet")
        else:
            print(f"❌ Error: API returned {e.response.status_code}")
    except httpx.ConnectError:
        print(f"❌ Error: Cannot connect to API at {api_url}")
        print("   Make sure the shift scheduler API is running")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_html_report.py <job_id>")
        print("Example: python generate_html_report.py abc123-def456")
        sys.exit(1)

    job_id = sys.argv[1]
    print(f"📊 Generating HTML report for job: {job_id}")

    asyncio.run(generate_html_report(job_id))


if __name__ == "__main__":
    main()
