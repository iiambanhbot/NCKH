"""
Research Finder - Ứng dụng Streamlit tìm kiếm và tổng hợp tài liệu nghiên cứu kinh tế.
Giao diện kết nối trực tiếp với pipeline, ui, selection và export; không chứa logic nghiệp vụ.
"""

from __future__ import annotations

from pathlib import Path
import threading
import time
from typing import Any

import streamlit as st

from core import SelectionStore, get_store, papers_to_excel_bytes
from core.settings import DEFAULT_YEAR_FROM
from search import load_more, run_first_search
from ui import render_load_more, render_paper_card, render_roadmap_page

# Cấu hình giao diện Streamlit (layout rộng, ẩn sidebar)
st.set_page_config(
    page_title="Research Finder",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Nạp toàn bộ CSS giao diện từ file ui/style.css
_css_path = Path(__file__).parent / "ui" / "style.css"
if _css_path.is_file():
    st.markdown(f"<style>{_css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# Banner thương hiệu hiện đại
st.markdown(
    """
    <div class="rf-banner">
        <div class="rf-banner-inner">
            <div>
                <div class="rf-banner-title">
                    <span>📚 Research Finder</span>
                    <span class="rf-banner-pill">AI Academic</span>
                </div>
                <div class="rf-banner-desc">
                    Hệ thống tìm kiếm, sàng lọc và trích xuất tài liệu nghiên cứu kinh tế học thuật thông minh
                </div>
            </div>
            <div class="rf-creator-credit">
                <span>Dự án của: <strong>Nguyễn Huy Hoàng Lân</strong></span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


def render_search_page(store: SelectionStore) -> None:
    """Render trang tìm kiếm, sàng lọc và trích xuất tài liệu nghiên cứu."""
    # =========================================================================
    # PHẦN TRÊN: KHUNG ĐỀ TÀI NGHIÊN CỨU & BỘ LỌC
    # =========================================================================
    with st.container(border=True):
        st.markdown("#### 🎯 Đề tài nghiên cứu")

        with st.form("search_form", border=False):
            # Hàng 1: Ô nhập đề tài & Nút Tìm bài (màu xanh blue nổi bật)
            col_topic, col_find = st.columns([0.85, 0.15])
            with col_topic:
                topic_input = st.text_input(
                    "Nhập đề tài nghiên cứu:",
                    value=store.topic,
                    placeholder="Ví dụ: fintech monetary policy, kinh tế xanh Việt Nam...",
                    label_visibility="collapsed",
                )
            with col_find:
                find_clicked = st.form_submit_button("🔎 Tìm bài", type="primary", use_container_width=True)

            # Hàng 2: Ô năm bắt đầu, Số bài tìm kiếm & Nút Đặt lại nằm ngang hàng
            col_yr, col_limit, col_spacer, col_reset = st.columns([0.22, 0.28, 0.35, 0.15])
            with col_yr:
                year_from = st.number_input(
                    "Năm bắt đầu:",
                    min_value=1900,
                    max_value=2030,
                    value=int(DEFAULT_YEAR_FROM),
                    step=1,
                    help="Giới hạn năm xuất bản bài báo học thuật cần tìm kiếm",
                )
            with col_limit:
                target_options = [5, 10, 15, 20]
                current_target = getattr(store, "target_count", 10)
                default_idx = target_options.index(current_target) if current_target in target_options else 1
                target_count = st.selectbox(
                    "Số bài tìm kiếm:",
                    options=target_options,
                    index=default_idx,
                    format_func=lambda x: f"{x} bài",
                    help="Chọn số lượng bài báo cần tìm kiếm và phân tích chuyên sâu (5, 10, 15 hoặc 20 bài)",
                )
            with col_reset:
                # Canh lề trên để nút Đặt lại nằm ngang bằng với ô điền số năm bắt đầu
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                reset_clicked = st.form_submit_button("🔄 Đặt lại", use_container_width=True)

        if reset_clicked:
            store.reset()
            for k in list(st.session_state.keys()):
                if "Nhập đề tài" in str(k):
                    st.session_state[k] = ""
            st.rerun()

        # Sau khi nhập đề tài: Hiển thị thông tin đề tài & từ khóa AI gợi ý
        if store.topic:
            st.markdown("---")
            col_topic_info, col_kw_info = st.columns([0.4, 0.6])
            with col_topic_info:
                st.markdown(
                    f"""
                    <div class="rf-topic-card">
                        <div class="rf-topic-label">📌 Đề tài đang tra cứu:</div>
                        <div class="rf-topic-val">{store.topic}</div>
                        <div class="rf-topic-sub">Kho ứng viên chờ xem thêm: <strong>{store.pool_size()} bài báo</strong></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_kw_info:
                if store.keywords:
                    pri_en = store.keywords.get("primary_en", "")
                    extra_en = store.keywords.get("en", [])
                    extra_vi = store.keywords.get("vi", [])

                    kw_html: list[str] = []
                    if pri_en:
                        kw_html.append(f'<span class="rf-kw-badge rf-kw-primary">🏷️ {pri_en}</span>')
                    for k in extra_en[:3]:
                        kw_html.append(f'<span class="rf-kw-badge">🌐 {k}</span>')
                    for k in extra_vi[:2]:
                        kw_html.append(f'<span class="rf-kw-badge">🇻🇳 {k}</span>')

                    if kw_html:
                        st.markdown(
                            f"""
                            <div class="rf-kw-box">
                                <div class="rf-kw-title">Gợi ý từ khóa AI đa chiều:</div>
                                <div class="rf-kw-list">{" ".join(kw_html)}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # PHẦN DƯỚI: KẾT QUẢ NGHIÊN CỨU (FULL WIDTH)
    # =========================================================================
    st.subheader("📄 Kết quả nghiên cứu")

    # Xử lý khi bấm nút "Tìm bài"
    if find_clicked:
        cleaned_topic = topic_input.strip()
        if cleaned_topic:
            # Khung thanh tiến trình tìm kiếm hiển thị cố định, rõ ràng với radar pulse animation
            status_box = st.container(border=True)
            with status_box:
                st.markdown(
                    """
                    <div class="rf-progress-title">
                        <div class="rf-pulse-dot"></div>
                        <span>Đang tìm kiếm & xử lý tài liệu học thuật</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                step_text = st.empty()
                progress_bar = st.progress(0.0)

            state: dict[str, Any] = {
                "stage": "Phân tích đề tài & sinh từ khóa học thuật...",
                "results": None,
                "error": None,
                "done": False,
            }

            def progress_callback(pct: float, msg: str) -> None:
                state["stage"] = msg

            def worker_thread() -> None:
                try:
                    state["results"] = run_first_search(
                        cleaned_topic,
                        store,
                        year_from=int(year_from),
                        on_progress=progress_callback,
                        batch_size=int(target_count),
                    )
                except Exception as exc:
                    state["error"] = exc
                finally:
                    state["done"] = True

            thread = threading.Thread(target=worker_thread, daemon=True)
            thread.start()

            # Vòng lặp tăng tiến độ mượt mà, liên tục từ 0% tới ~92% trong khi chờ kết quả
            prog = 0.02
            while not state["done"]:
                time.sleep(0.05)
                # Tăng đều liên tục: mượt mà, không khựng, tiệm cận 92% nếu chờ lâu
                if prog < 0.25:
                    prog += 0.008
                elif prog < 0.60:
                    prog += 0.005
                elif prog < 0.85:
                    prog += 0.003
                else:
                    prog = min(0.92, prog + (0.93 - prog) * 0.03)

                pct_val = max(0.0, min(1.0, prog))
                pct_int = int(pct_val * 100)
                current_msg = state.get("stage", "Đang xử lý tài liệu...")
                step_text.markdown(f"**{current_msg}** (`{pct_int}%`)")
                progress_bar.progress(pct_val)

            thread.join(timeout=1.0)

            # Lướt đều, mượt mà từ vị trí hiện tại lên thẳng 100% khi xử lý xong
            while prog < 1.0:
                time.sleep(0.02)
                prog = min(1.0, prog + 0.03)
                pct_int = int(prog * 100)
                final_count = len(state["results"]) if state["results"] else 0
                step_text.markdown(f"**Hoàn tất! Đã tìm thấy {final_count} bài báo đầu tiên.** (`{pct_int}%`)")
                progress_bar.progress(prog)

            time.sleep(0.4)
            status_box.empty()

            if state["error"]:
                st.error(f"Lỗi AI trong quá trình xử lý: {state['error']}")
            elif not state["results"]:
                st.info("Không tìm thấy bài báo nào phù hợp với đề tài trên.")
            else:
                st.rerun()
        else:
            st.warning("Vui lòng nhập đề tài nghiên cứu ở khung phía trên trước khi bấm Tìm bài.")

    displayed_papers = store.get_all()
    selected_papers = store.get_selected()

    # Cảnh báo khi có bài chưa được tóm tắt bằng AI
    if displayed_papers:
        unanalyzed_with_abs = [
            p for p in displayed_papers
            if not getattr(p, "analyzed", False) and bool((p.abstract or "").strip())
        ]
        if unanalyzed_with_abs:
            st.warning(
                f"Có {len(unanalyzed_with_abs)} bài báo chưa được tóm tắt bằng AI (do hết hạn mức hoặc sai key). "
                "Các bài báo vẫn được hiển thị đầy đủ bên dưới. Bạn có thể bấm 'Tóm tắt bằng AI' ở từng bài để thử lại."
            )

        # Thanh tác vụ: Thống kê & Nút "Xuất Excel" chỉ xuất bài đã chọn
        col_summary, col_roadmap_tip, col_export = st.columns([0.48, 0.22, 0.30])

        with col_summary:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; height: 100%; padding: 6px 0;">
                    <span style="font-size: 0.95rem; color: #94a3b8;">
                        Đang hiển thị: <strong style="color: #f8fafc;">{len(displayed_papers)}</strong> bài &nbsp;•&nbsp; 
                        Đã chọn: <strong style="color: #38bdf8;">{len(selected_papers)}</strong> bài
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_roadmap_tip:
            st.markdown(
                """
                <div style="display: flex; align-items: center; justify-content: center; height: 100%;">
                    <span style="background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.35); color: #a5b4fc; font-size: 0.78rem; font-weight: 600; padding: 4px 10px; border-radius: 8px;">
                        🗺️ Tab trên: Lộ trình & Sơ đồ NCKH
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_export:
            if selected_papers:
                excel_bytes = papers_to_excel_bytes(selected_papers)
                st.download_button(
                    label=f"📥 Xuất Excel ({len(selected_papers)} bài đã chọn)",
                    data=excel_bytes,
                    file_name="tai_lieu_nghien_cuu.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True,
                )
            else:
                st.button(
                    "📥 Xuất Excel",
                    disabled=True,
                    use_container_width=True,
                    help="Vui lòng tích chọn ít nhất 1 bài báo để xuất Excel",
                )

        # Hiện các ô bằng ui.paper_card có đánh số thứ tự từng bài (Bài #1, #2, ...)
        for idx, paper in enumerate(displayed_papers, 1):
            render_paper_card(paper, store, index=idx)

        # Nút "Thêm 5 bài" (ui.load_more) → pipeline.load_more
        st.markdown("---")
        col_center = st.columns([0.35, 0.3, 0.35])[1]
        with col_center:
            if render_load_more():
                with st.spinner("Đang tải thêm bài tiếp theo..."):
                    try:
                        new_batch = load_more(store, year_from=int(year_from))
                        if new_batch:
                            st.success(f"Đã tải thêm {len(new_batch)} bài báo mới!")
                        else:
                            st.info("Không còn bài báo nào mới trong kho ứng viên hoặc nguồn tìm kiếm.")
                        st.rerun()
                    except Exception as exc:
                        st.warning(f"Lỗi khi tải thêm bài: {exc}")

    elif store.topic:
        st.markdown(
            f"""<div class="rf-empty-search-card">
<div class="rf-empty-icon">🔎</div>
<div class="rf-empty-title">Chưa tìm thấy bài báo phù hợp</div>
<div class="rf-empty-sub">Đề tài đang tra cứu: <span class="rf-empty-topic">{store.topic}</span></div>
<div class="rf-empty-hints">
<span>💡 <strong>Gợi ý cải thiện kết quả:</strong></span>
<ul>
<li>Rút gọn đề tài thành cụm từ khóa trọng tâm (ví dụ: <em>kinh tế số xuất khẩu nông sản</em>).</li>
<li>Giảm năm bắt đầu để mở rộng khoảng thời gian tìm kiếm.</li>
<li>Thử dùng các thuật ngữ học thuật tiếng Anh tương đương.</li>
<li>Chuyển sang tab <strong>🗺️ Đề xuất lộ trình & Bảng tiến trình</strong> để lập khung kế hoạch nghiên cứu trước.</li>
</ul>
</div>
</div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """<div class="rf-welcome-hero">
<div class="rf-welcome-top-glow"></div>
<div class="rf-welcome-content">
<div class="rf-welcome-badge"><span class="rf-welcome-sparkle">✦</span><span>HỆ THỐNG TRA CỨU HỌC THUẬT & PHÂN TÍCH AI CHUYÊN SÂU</span></div>
<h3 class="rf-welcome-heading">Sẵn sàng khám phá & tổng quan tài liệu nghiên cứu</h3>
<p class="rf-welcome-desc">Nhập đề tài hoặc câu hỏi nghiên cứu vào ô bên trên và bấm nút <span class="rf-highlight-btn">🔎 Tìm bài</span>. Hệ thống sẽ tự động mở rộng từ khóa song ngữ, truy vấn kho dữ liệu học thuật mở toàn cầu <strong>OpenAlex</strong> (hơn 250M+ ấn phẩm), trích xuất phương pháp - kết quả và phân tích hạn chế của tài liệu đối với đề tài.</p>
<div class="rf-feature-grid">
<div class="rf-feature-card">
<div class="rf-feature-icon-wrapper" style="background: rgba(56, 189, 248, 0.12); border-color: rgba(56, 189, 248, 0.3); color: #38bdf8;">🌐</div>
<div class="rf-feature-title">Kho dữ liệu 250M+ bài báo</div>
<div class="rf-feature-text">Truy vấn dữ liệu học thuật toàn diện từ OpenAlex với đầy đủ tạp chí, tác giả, chỉ số trích dẫn và liên kết Open Access.</div>
</div>
<div class="rf-feature-card">
<div class="rf-feature-icon-wrapper" style="background: rgba(99, 102, 241, 0.14); border-color: rgba(99, 102, 241, 0.35); color: #a5b4fc;">🧠</div>
<div class="rf-feature-title">Phân tích & Chỉ rõ hạn chế</div>
<div class="rf-feature-text">Mô hình AI trích xuất phương pháp, kết quả chính và chỉ rõ hạn chế/khoảng trống của bài báo đối với đề tài cụ thể.</div>
</div>
<div class="rf-feature-card">
<div class="rf-feature-icon-wrapper" style="background: rgba(16, 185, 129, 0.12); border-color: rgba(16, 185, 129, 0.3); color: #34d399;">📊</div>
<div class="rf-feature-title">Xuất Excel 18 cột NCKH</div>
<div class="rf-feature-text">Lựa chọn các bài báo tâm đắc và xuất bảng tổng quan tài liệu chuẩn hóa 18 cột cho đề tài nghiên cứu khoa học.</div>
</div>
</div>
<div class="rf-welcome-tip">
<div class="rf-tip-badge">💡 MẸO NHỎ</div>
<div class="rf-tip-text">Bạn có thể chuyển giữa 2 trang mục ở tab phía trên: <strong>📚 Tìm kiếm tài liệu</strong> và <strong>🗺️ Đề xuất lộ trình & Bảng tiến trình</strong> để quản lý toàn diện đề tài NCKH.</div>
</div>
</div>
</div>""",
            unsafe_allow_html=True,
        )


# Lấy SelectionStore singleton
store = get_store()

# Phân chia trang mục: Tab Tìm kiếm & Tab Đề xuất lộ trình NCKH
tab_search, tab_roadmap = st.tabs(
    [
        "📚 Tìm kiếm & Tổng hợp tài liệu",
        "🗺️ Đề xuất lộ trình & Bảng tiến trình",
    ]
)

with tab_search:
    render_search_page(store)

with tab_roadmap:
    render_roadmap_page(store)
