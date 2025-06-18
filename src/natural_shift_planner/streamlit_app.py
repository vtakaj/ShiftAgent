"""
Streamlit Web UI for Shift Scheduler - Job Management
"""

import asyncio
from datetime import datetime
from typing import Any

import httpx
import streamlit as st

# Configuration
API_BASE_URL = "http://localhost:8081"


# API Helper Functions
async def call_api(method: str, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Make an API call to the shift scheduler"""
    url = f"{API_BASE_URL}{endpoint}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json=data)
        elif method == "PATCH":
            response = await client.patch(url, json=data)
        elif method == "DELETE":
            response = await client.delete(url)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result


async def get_html_content(job_id: str) -> str:
    """Get HTML content for a job"""
    url = f"{API_BASE_URL}/api/shifts/solve/{job_id}/html"

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


def run_async(coro):
    """Helper to run async functions in Streamlit"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)


# Streamlit App
def main():
    st.set_page_config(
        page_title="シフトスケジューラー - ジョブ管理",
        page_icon="📅",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.title("📋 シフトスケジューラー - ジョブ管理")
    st.markdown("完了済みジョブのシフト表を表示・管理します")
    st.markdown("---")

    manage_jobs()


def manage_jobs():
    """Manage existing optimization jobs with HTML template display"""

    # Auto-load jobs on page load
    if "jobs_data" not in st.session_state:
        try:
            with st.spinner("ジョブ一覧を取得中..."):
                jobs_data = run_async(call_api("GET", "/api/jobs"))
            st.session_state.jobs_data = jobs_data
        except Exception as e:
            st.error(f"❌ API接続エラー: {str(e)}")
            st.info("FastAPI サーバーが起動していることを確認してください (make run)")
            return

    # Refresh button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 更新", type="secondary"):
            try:
                with st.spinner("更新中..."):
                    jobs_data = run_async(call_api("GET", "/api/jobs"))
                st.session_state.jobs_data = jobs_data
                st.rerun()
            except Exception as e:
                st.error(f"❌ エラー: {str(e)}")
                return

    jobs_data = st.session_state.jobs_data

    # Display job summary
    st.subheader(f"📊 総ジョブ数: {jobs_data['total']}")

    if not jobs_data["jobs"]:
        st.info("📝 完了済みジョブがありません")
        st.markdown("シフト最適化を実行すると、ここにジョブが表示されます")
        return

    # Filter only completed jobs
    completed_jobs = [
        job for job in jobs_data["jobs"] if job["status"] == "SOLVING_COMPLETED"
    ]

    if not completed_jobs:
        st.warning("🔄 完了済みのジョブがありません")
        st.markdown("最適化が完了したジョブのみシフト表を表示できます")
        return

    st.subheader(f"✅ 完了済みジョブ: {len(completed_jobs)}件")

    # Job selection with session state
    for i, job in enumerate(completed_jobs):
        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            created_at = (
                datetime.fromisoformat(job["created_at"].replace("Z", "+00:00"))
                if job.get("created_at")
                else None
            )
            created_str = (
                created_at.strftime("%Y-%m-%d %H:%M") if created_at else "不明"
            )
            st.write(f"**ジョブ {i + 1}**: `{job['job_id'][:8]}...`")
            st.caption(f"作成日時: {created_str}")

        with col2:
            if st.button(
                "📅 シフト表を表示", key=f"show_{job['job_id']}", type="primary"
            ):
                st.session_state.selected_job_id = job["job_id"]

        with col3:
            if st.button("🗑️", key=f"delete_{job['job_id']}", help="削除"):
                try:
                    # Delete from API
                    run_async(call_api("DELETE", f"/api/jobs/{job['job_id']}"))

                    # Clear selected job if it's the one being deleted
                    if (
                        hasattr(st.session_state, "selected_job_id")
                        and st.session_state.selected_job_id == job["job_id"]
                    ):
                        st.session_state.selected_job_id = None

                    # Refresh jobs data from API instead of manual removal
                    jobs_data = run_async(call_api("GET", "/api/jobs"))
                    st.session_state.jobs_data = jobs_data

                    st.success("削除しました")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 削除エラー: {str(e)}")

        st.markdown("---")

    # Display selected job's schedule on separate page
    if (
        hasattr(st.session_state, "selected_job_id")
        and st.session_state.selected_job_id
    ):
        st.switch_page("pages/schedule_view.py")


if __name__ == "__main__":
    main()
