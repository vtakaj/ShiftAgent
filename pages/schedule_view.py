"""
Schedule View Page - Display individual shift schedule
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

import httpx
import streamlit as st
import streamlit.components.v1 as components

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Configuration
API_BASE_URL = "http://localhost:8081"


# API Helper Functions
async def call_api(method: str, endpoint: str, data: dict = None) -> dict[str, Any]:
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
        return response.json()


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


# Main page content
def main():
    st.set_page_config(
        page_title="シフト表表示",
        page_icon="📅",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Check if job ID is available
    if (
        not hasattr(st.session_state, "selected_job_id")
        or not st.session_state.selected_job_id
    ):
        st.error("❌ ジョブが選択されていません")
        if st.button("📋 ジョブ一覧に戻る", type="primary"):
            st.switch_page("streamlit_main.py")
        return

    job_id = st.session_state.selected_job_id

    # Header with navigation
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← ジョブ一覧に戻る", type="secondary"):
            st.session_state.selected_job_id = None
            st.switch_page("streamlit_main.py")

    with col2:
        st.title(f"📅 シフト表: {job_id[:8]}...")

    st.markdown("---")

    try:
        with st.spinner("シフト表を生成中..."):
            # Get job data
            job_data = run_async(call_api("GET", f"/api/shifts/solve/{job_id}"))

            # Get HTML content
            html_content = run_async(get_html_content(job_id))

        # Display job summary
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("割当済みシフト", job_data.get("assigned_shifts", 0))

        with col2:
            st.metric("未割当シフト", job_data.get("unassigned_shifts", 0))

        with col3:
            total_shifts = job_data.get("assigned_shifts", 0) + job_data.get(
                "unassigned_shifts", 0
            )
            assignment_rate = (
                (job_data.get("assigned_shifts", 0) / total_shifts * 100)
                if total_shifts > 0
                else 0
            )
            st.metric("割当率", f"{assignment_rate:.1f}%")

        with col4:
            # Debug score display
            score_value = job_data.get("score", "取得中...")
            st.metric("最終スコア", score_value)
            # Debug info in expander
            with st.expander("デバッグ情報"):
                st.write("Job data keys:", list(job_data.keys()))
                st.write("Score value:", repr(score_value))
                st.write("Full job data:", job_data)

        st.markdown("---")

        # Display HTML schedule in full width
        st.subheader("🎯 シフト表")

        components.html(html_content, height=800, scrolling=True)

        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 3])

        with col1:
            # Download button for HTML
            st.download_button(
                label="💾 HTMLダウンロード",
                data=html_content.encode("utf-8"),
                file_name=f"shift_schedule_{job_id[:8]}.html",
                mime="text/html",
            )

        with col2:
            # Open in new tab button (show URL)
            if st.button("🌐 新しいタブで開く"):
                st.info(
                    f"以下のURLをコピーして新しいタブで開いてください:\n`http://localhost:8081/api/shifts/solve/{job_id}/html`"
                )

        # Raw data expander (optional)
        with st.expander("📋 生データ (JSON)"):
            st.json(job_data.get("solution", {}))

    except Exception as e:
        st.error(f"❌ シフト表の表示エラー: {str(e)}")
        if "404" in str(e):
            st.info("ジョブが見つかりません。削除された可能性があります。")
        elif "400" in str(e):
            st.info("ジョブがまだ完了していません。")
        else:
            st.info("APIサーバーが起動していることを確認してください。")

        # Return button on error
        if st.button("📋 ジョブ一覧に戻る", type="primary"):
            st.session_state.selected_job_id = None
            st.switch_page("streamlit_main.py")


if __name__ == "__main__":
    main()
