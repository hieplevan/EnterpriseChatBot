import sys
from pathlib import Path
import streamlit as st

# Dam bao import thu muc frontend
sys.path.append(str(Path(__file__).resolve().parent.parent))

from frontend.client import RAGBackendClient

st.set_page_config(
    page_title="Hệ thống Trợ lý Tri thức Doanh nghiệp",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS phong cach Gemini / Messenger / Zalo Dark Mode hien dai
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #131314 !important;
        color: #e3e3e3 !important;
    }

    code, pre, .mono, [class*="line-num"] {
        font-family: 'JetBrains Mono', monospace !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1440px;
    }

    /* Thanh dieu huong tren cung (Top Navigation Bar) */
    .gemini-top-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #1e1f20;
        border: 1px solid #2e3135;
        border-radius: 12px;
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
    }
    .gemini-title {
        font-size: 1rem;
        font-weight: 700;
        color: #f0f4f9;
        letter-spacing: -0.2px;
    }
    .badge-status-online {
        background: rgba(46, 160, 67, 0.15);
        color: #3fb950;
        border: 1px solid rgba(46, 160, 67, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-role {
        background: rgba(11, 87, 208, 0.15);
        color: #a8c7fa;
        border: 1px solid rgba(11, 87, 208, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 0.4rem;
    }

    /* Khung chat tin nhan phong cach Zalo / Messenger / Gemini */
    div[data-testid="stChatMessage"] {
        border-radius: 16px !important;
        padding: 1rem 1.25rem !important;
        margin-bottom: 0.75rem !important;
        border: 1px solid #2a2b2e !important;
        background-color: #1e1f20 !important;
    }

    /* Khung tin nhan nguoi dung */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background-color: #1a4971 !important;
        border: 1px solid #2a6f97 !important;
        margin-left: 8% !important;
        border-radius: 18px 18px 4px 18px !important;
    }

    /* Khung tin nhan tro ly AI */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
        background-color: #1e1f20 !important;
        border: 1px solid #2e3135 !important;
        margin-right: 4% !important;
        border-radius: 18px 18px 18px 4px !important;
    }

    /* The trich dan (Citation Chip) */
    .citation-chip {
        display: inline-block;
        background: #2a2b2e;
        color: #a8c7fa;
        border: 1px solid #3c4043;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.78rem;
        margin: 3px 4px 3px 0;
        text-decoration: none;
        transition: all 0.2s;
    }
    .citation-chip:hover {
        background: #333538;
        border-color: #a8c7fa;
    }

    /* The canh bao PII */
    .pii-alert-box {
        background: rgba(217, 119, 6, 0.12);
        border: 1px solid rgba(217, 119, 6, 0.35);
        color: #fbbf24;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 0.78rem;
        margin-top: 0.5rem;
    }

    /* Khung xem tai lieu goc & Boi den (Document Viewer) */
    .doc-viewer-card {
        background: #18191a;
        border: 1px solid #2e3135;
        border-radius: 12px;
        padding: 1.25rem;
        height: 720px;
        overflow-y: auto;
    }
    .doc-viewer-header {
        font-size: 0.82rem;
        color: #a8c7fa;
        font-weight: 600;
        padding-bottom: 0.6rem;
        margin-bottom: 0.8rem;
        border-bottom: 1px solid #2e3135;
        display: flex;
        justify-content: space-between;
    }
    .document-viewer-container {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        line-height: 1.65;
        white-space: pre-wrap;
    }
    .doc-line {
        display: flex;
        padding: 2px 6px;
        border-radius: 3px;
    }
    .line-normal {
        color: #c4c7c5;
    }
    .line-highlighted {
        background: rgba(234, 134, 46, 0.18);
        border-left: 3px solid #ea862e;
    }
    .line-num {
        color: #5e6266;
        user-select: none;
        margin-right: 1.2rem;
        width: 36px;
        text-align: right;
        display: inline-block;
    }
    .line-text {
        flex: 1;
        word-break: break-word;
    }
    .doc-highlight-span {
        background: rgba(234, 134, 46, 0.5) !important;
        color: #ffffff !important;
        padding: 2px 4px;
        border-radius: 4px;
        font-weight: 600;
        box-shadow: 0 0 10px rgba(234, 134, 46, 0.6);
    }

    /* Thong ke KPI */
    .metric-box {
        background: #1e1f20;
        border: 1px solid #2e3135;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #a8c7fa;
    }
    .metric-label {
        font-size: 0.78rem;
        color: #8e918f;
        margin-top: 0.25rem;
    }

    /* Nut bam Streamlit phong cach hien dai */
    .stButton>button {
        background-color: #282a2d;
        color: #e3e3e3;
        border: 1px solid #3c4043;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 500;
        padding: 0.4rem 0.8rem;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #333538;
        border-color: #a8c7fa;
        color: #ffffff;
    }

    /* Nut Tao cuoc tro chuyen moi */
    .new-chat-btn>button {
        background-color: #0b57d0 !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 20px !important;
        padding: 0.55rem 1rem !important;
    }
    .new-chat-btn>button:hover {
        background-color: #1a73e8 !important;
    }

    /* Hop nhap cau hoi duoi cung */
    div[data-testid="stChatInput"] {
        border-radius: 24px !important;
    }
    div[data-testid="stChatInput"] textarea {
        background-color: #1e1f20 !important;
        color: #e3e3e3 !important;
        border: 1px solid #3c4043 !important;
        border-radius: 24px !important;
        padding: 0.75rem 1.25rem !important;
        font-size: 0.9rem !important;
    }
    div[data-testid="stChatInput"] textarea:focus {
        border-color: #a8c7fa !important;
        box-shadow: 0 0 0 1px #a8c7fa !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Khoi tao client ket noi Backend
client = RAGBackendClient()

# Kiem tra ket noi backend
health_info = client.check_health()
is_backend_online = health_info.get("status") == "healthy"

# Load danh sach nguoi dung he thong
users_list = client.get_users() if is_backend_online else []
role_name_map = {
    "ADMIN": "Quản trị viên (Toàn quyền)",
    "LEGAL": "Pháp chế (Tra cứu văn bản pháp luật)",
    "HR": "Nhân sự (Quy chế & Chính sách nội bộ)",
    "FINANCE": "Kế toán (Tài chính & Chi tiêu)",
    "EMPLOYEE": "Nhân viên (Quy định & Hướng dẫn chung)",
}
user_display_options = {}
for u in users_list:
    display_title = f"{u['full_name']} - {role_name_map.get(u['role'], u['role'])}"
    user_display_options[display_title] = u

# Khoi tao session state
if "active_user" not in st.session_state:
    st.session_state.active_user = users_list[0] if users_list else {"id": 1, "username": "admin", "full_name": "Quản trị viên", "role": "ADMIN", "department": "ALL"}
if "current_conv_id" not in st.session_state:
    st.session_state.current_conv_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_citation" not in st.session_state:
    st.session_state.selected_citation = None
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

active_u = st.session_state.active_user
user_role_label = role_name_map.get(active_u.get("role", "EMPLOYEE"), active_u.get("role", "EMPLOYEE"))

# ================= THANH DIEU HUONG TREN CUNG (TOP BAR) =================
status_tag = '<span class="badge-status-online">Trực tuyến</span>' if is_backend_online else '<span class="tag-badge" style="color:#f87171;">Mất kết nối Backend</span>'

st.markdown(
    f"""
    <div class="gemini-top-bar">
        <div>
            <span class="gemini-title">Trợ lý Tri thức Doanh nghiệp</span>
            <span class="badge-role">{active_u.get('full_name', 'Người dùng')} ({active_u.get('role', 'EMPLOYEE')})</span>
        </div>
        <div>
            {status_tag}
            <span class="tag-badge" style="background:#282a2d; padding:4px 8px; border-radius:6px; font-size:0.75rem; color:#8e918f;">Ollama + ChromaDB</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not is_backend_online:
    st.error("Máy chủ Backend FastAPI đang tắt. Vui lòng chạy file 'run_backend.bat' hoặc 'run_full_stack.bat'.")

# ================= THANH BEN (SIDEBAR) =================
with st.sidebar:
    st.markdown("### Trò chuyện")
    
    # Nut Cuoc tro chuyen moi to va dep
    st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
    if st.button("+ Cuộc trò chuyện mới", use_container_width=True):
        res = client.create_conversation(user_id=active_u.get("id", 1), title="Cuộc trò chuyện mới")
        st.session_state.current_conv_id = res.get("id")
        st.session_state.messages = []
        st.session_state.selected_citation = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Lịch sử trò chuyện")
    if is_backend_online:
        conv_list = client.get_conversations(user_id=active_u.get("id", 1))
        if conv_list:
            for c in conv_list[:8]:
                is_cur = c["id"] == st.session_state.current_conv_id
                title_short = c["title"][:24] + ("..." if len(c["title"]) > 24 else "")
                prefix = "> " if is_cur else ""

                
                col_item, col_del = st.columns([4, 1])
                with col_item:
                    if st.button(f"{prefix}{title_short}", key=f"conv_{c['id']}", use_container_width=True):
                        st.session_state.current_conv_id = c["id"]
                        msgs_res = client.get_conversation_messages(c["id"])
                        st.session_state.messages = msgs_res.get("messages", [])
                        st.session_state.selected_citation = None
                        st.rerun()
                with col_del:
                    if st.button("x", key=f"del_{c['id']}"):
                        client.delete_conversation(c["id"])
                        if st.session_state.current_conv_id == c["id"]:
                            st.session_state.current_conv_id = None
                            st.session_state.messages = []
                        st.rerun()
        else:
            st.caption("Chưa có phiên trò chuyện nào.")

    st.markdown("---")
    st.markdown("### Tài khoản & Quyền hạn")
    if user_display_options:
        selected_label = st.selectbox(
            "Chọn vai trò trải nghiệm:",
            options=list(user_display_options.keys()),
            index=0,
            label_visibility="collapsed",
        )
        selected_u = user_display_options[selected_label]
        if selected_u["id"] != st.session_state.active_user.get("id"):
            st.session_state.active_user = selected_u
            st.session_state.current_conv_id = None
            st.session_state.messages = []
            st.rerun()

    # Tùy chỉnh nâng cao
    with st.expander("Tùy chỉnh tra cứu & An toàn dữ liệu"):
        use_rag = st.toggle("Kích hoạt tìm kiếm tri thức (RAG)", value=True)
        use_hybrid = st.toggle("Tìm kiếm kết hợp (Từ khóa + Ngữ nghĩa)", value=True)
        use_rerank = st.toggle("Tinh chỉnh độ liên quan (Re-ranking)", value=True)
        mask_pii = st.toggle("Tự động che thông tin cá nhân (CCCD, SĐT, Email)", value=True)
        top_k = st.slider("Số đoạn trích dẫn tham khảo (Top K)", min_value=1, max_value=8, value=4)
        temperature = st.slider("Độ sáng tạo câu trả lời", min_value=0.0, max_value=1.0, value=0.3, step=0.05)

    # Chế độ Kỹ thuật dành riêng cho Quản trị viên & Lập trình viên (Dev Mode)
    is_admin = active_u.get("role") == "ADMIN"
    can_manage_docs = active_u.get("role") in ["ADMIN", "LEGAL", "HR"]
    show_dev_tools = False

    if is_admin:
        st.markdown("---")
        st.markdown("### Dành cho Kỹ thuật viên (Dev)")
        show_dev_tools = st.toggle("Bật công cụ Giám sát & Benchmark", value=False)


# ================= KHU VỰC CHÍNH (ĐIỀU HƯỚNG THEO VAI TRÒ NGƯỜI DÙNG) =================
# Xac dinh danh sach tabs hien thi theo quyen han thuc te
tab_titles = ["Trò chuyện & Đối chiếu"]

if can_manage_docs:
    tab_titles.append("Quản lý kho tài liệu")

if show_dev_tools:
    tab_titles.extend(["Nhật ký & Giám sát (Dev)", "Đo lường chất lượng (Benchmark)"])

# Khoi tao tabs dua tren danh sach quyen han
tabs_created = st.tabs(tab_titles) if len(tab_titles) > 1 else [st.container()]
tab_chat = tabs_created[0]
tab_docs = tabs_created[1] if can_manage_docs and len(tabs_created) > 1 else None
tab_audit = tabs_created[tab_titles.index("Nhật ký & Giám sát (Dev)")] if show_dev_tools else None
tab_eval = tabs_created[tab_titles.index("Đo lường chất lượng (Benchmark)")] if show_dev_tools else None

# ---------------- PHÂN HỆ 1: TRÒ CHUYỆN & ĐỐI CHIẾU ----------------
with tab_chat:

    col_chat, col_doc = st.columns([1, 1], gap="large")

    # CỘT TRÁI: KHUNG TRÒ CHUYỆN
    with col_chat:
        st.markdown(f"**Khung hội thoại** | *Quyền truy cập: {user_role_label}*")

        # Gợi ý câu hỏi nhanh nếu chưa có tin nhắn
        if not st.session_state.messages:
            st.caption("Chọn nhanh câu hỏi mẫu theo các quy định hiện hành:")
            q1, q2 = st.columns(2)
            with q1:
                if st.button("Mức phạt vượt đèn đỏ xe máy & ô tô (Nghị định 100)", use_container_width=True):
                    st.session_state.pending_query = "Mức phạt tiền và hình thức tước bằng lái khi vượt đèn đỏ đối với xe máy và ô tô theo Nghị định 100 là bao nhiêu?"
                    st.rerun()
                if st.button("Mức phạt nồng độ cồn mới nhất (Nghị định 100)", use_container_width=True):
                    st.session_state.pending_query = "Các khung xử phạt vi phạm nồng độ cồn đối với người lái xe máy và ô tô theo Nghị định 100 quy định thế nào?"
                    st.rerun()
                if st.button("Tiền lương làm thêm giờ ngày lễ (Bộ luật Lao động)", use_container_width=True):
                    st.session_state.pending_query = "Tiền lương làm thêm giờ vào ngày nghỉ lễ, tết theo Bộ luật Lao động 2019 tính như thế nào?"
                    st.rerun()
            with q2:
                if st.button("Lỗi không mang bằng lái, bảo hiểm xe máy (Nghị định 100)", use_container_width=True):
                    st.session_state.pending_query = "Không mang theo Giấy phép lái xe, Cà vẹt xe và Bảo hiểm bắt buộc TNDS xe máy bị phạt bao nhiêu tiền theo Nghị định 100?"
                    st.rerun()
                if st.button("11 quyền cơ bản của chủ thể dữ liệu (Nghị định 13)", use_container_width=True):
                    st.session_state.pending_query = "Theo Nghị định 13/2023/NĐ-CP, chủ thể dữ liệu cá nhân có 11 quyền cơ bản nào?"
                    st.rerun()
                if st.button("Thời hạn góp vốn công ty TNHH (Luật Doanh nghiệp)", use_container_width=True):
                    st.session_state.pending_query = "Thời hạn góp vốn thành lập công ty TNHH hai thành viên trở lên là bao nhiêu ngày theo Luật Doanh nghiệp 2020?"
                    st.rerun()


        # Hiển thị lịch sử tin nhắn
        for msg_idx, msg in enumerate(st.session_state.messages):
            role_label = "Bạn" if msg["role"] == "user" else "Trợ lý Doanh nghiệp"
            with st.chat_message(msg["role"]):
                st.markdown(f"**{role_label}**")
                st.markdown(msg["content"])

                # Hiển thị các đoạn trích dẫn kèm nút xem văn bản
                if "citations" in msg and msg["citations"]:
                    st.markdown("<div style='margin-top:0.6rem; font-size:0.8rem; font-weight:600; color:#a8c7fa;'>Nguồn tài liệu trích dẫn xác thực:</div>", unsafe_allow_html=True)
                    for cit_idx, cit in enumerate(msg["citations"], 1):
                        source = cit.get("source", "Tài liệu")
                        line_s = cit.get("line_start", 1)
                        line_e = cit.get("line_end", 1)
                        score = cit.get("score", 0.0)

                        c_info, c_btn = st.columns([3, 2])
                        with c_info:
                            st.caption(f"[{cit_idx}] {source} (Dòng {line_s} - {line_e})")
                        with c_btn:
                            btn_name = f"Xem văn bản gốc #{cit_idx}"
                            if st.button(btn_name, key=f"cit_msg_{msg_idx}_{cit_idx}"):
                                st.session_state.selected_citation = cit
                                st.rerun()

                # Nút đánh giá chất lượng phản hồi
                if msg["role"] == "assistant" and "id" in msg:
                    f1, f2, f3 = st.columns([2, 2, 4])
                    with f1:
                        if st.button("Hài lòng", key=f"like_{msg['id']}"):
                            client.submit_feedback(message_id=msg["id"], rating=1, user_id=active_u.get("id", 1))
                            st.toast("Cảm ơn bạn đã đánh giá câu trả lời chính xác.")
                    with f2:
                        if st.button("Chưa chuẩn", key=f"dislike_{msg['id']}"):
                            client.submit_feedback(message_id=msg["id"], rating=-1, user_id=active_u.get("id", 1))
                            st.toast("Đã ghi nhận phản hồi để hoàn thiện mô hình.")

        # Khung nhập câu hỏi
        user_input = st.chat_input("Nhập câu hỏi của bạn về luật, quy chế, chính sách doanh nghiệp...")
        query_to_send = st.session_state.pending_query or user_input

        if query_to_send:
            st.session_state.pending_query = None
            st.session_state.messages.append({"role": "user", "content": query_to_send})

            with st.chat_message("user"):
                st.markdown("**Bạn**")
                st.markdown(query_to_send)

            with st.chat_message("assistant"):
                st.markdown("**Trợ lý Doanh nghiệp**")
                with st.spinner("Đang tra cứu cơ sở dữ liệu và đối chiếu điều khoản văn bản..."):
                    chat_hist = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages[:-1]
                    ]
                    resp = client.query(
                        prompt=query_to_send,
                        chat_history=chat_hist,
                        use_rag=use_rag,
                        use_hybrid=use_hybrid,
                        use_rerank=use_rerank,
                        top_k=top_k,
                        temperature=temperature,
                        user_id=active_u.get("id", 1),
                        user_role=active_u.get("role", "EMPLOYEE"),
                        conversation_id=st.session_state.current_conv_id,
                        mask_pii=mask_pii,
                    )

                    ans = resp.get("answer", "")
                    cits = resp.get("citations", [])
                    msg_id = resp.get("message_id")
                    st.session_state.current_conv_id = resp.get("conversation_id")

                    st.markdown(ans)

                    # Thông báo nếu có thông tin cá nhân đã được che
                    pii_list = resp.get("pii_detected", [])
                    if pii_list:
                        st.markdown(
                            f'<div class="pii-alert-box">'
                            f'Bảo vệ an toàn thông tin: Đã tự động che dữ liệu nhạy cảm ({", ".join(pii_list)})'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                    # Hiển thị trích dẫn
                    if cits:
                        st.session_state.selected_citation = cits[0]
                        st.markdown("<div style='margin-top:0.6rem; font-size:0.8rem; font-weight:600; color:#a8c7fa;'>Nguồn tài liệu trích dẫn xác thực:</div>", unsafe_allow_html=True)
                        for cit_idx, cit in enumerate(cits, 1):
                            source = cit.get("source", "Tài liệu")
                            line_s = cit.get("line_start", 1)
                            line_e = cit.get("line_end", 1)
                            c_info, c_btn = st.columns([3, 2])
                            with c_info:
                                st.caption(f"[{cit_idx}] {source} (Dòng {line_s} - {line_e})")
                            with c_btn:
                                if st.button(f"Xem văn bản gốc #{cit_idx}", key=f"cit_live_{cit_idx}"):
                                    st.session_state.selected_citation = cit
                                    st.rerun()

                    asst_msg_obj = {
                        "id": msg_id,
                        "role": "assistant",
                        "content": ans,
                        "citations": cits,
                    }
                    st.session_state.messages.append(asst_msg_obj)
                    st.rerun()

    # CỘT PHẢI: KHUNG ĐỐI CHIẾU VĂN BẢN GỐC & TÔ SÁNG
    with col_doc:
        st.markdown("**Văn bản gốc & Vị trí trích dẫn xác thực**")

        cur_cit = st.session_state.selected_citation
        if cur_cit:
            doc_name = cur_cit.get("source")
            l_start = cur_cit.get("line_start")
            l_end = cur_cit.get("line_end")
            c_start = cur_cit.get("char_start")
            c_end = cur_cit.get("char_end")
            score = cur_cit.get("score", 0.0)

            with st.spinner(f"Đang tải và làm nổi bật văn bản {doc_name}..."):
                try:
                    hl_data = client.get_document_highlight(
                        file_name=doc_name,
                        char_start=c_start,
                        char_end=c_end,
                        line_start=l_start,
                        line_end=l_end,
                    )
                    hl_html = hl_data.get("highlighted_html", "")
                    total_lines = hl_data.get("total_lines", 0)

                    st.markdown(
                        f"""
                        <div class="doc-viewer-card">
                            <div class="doc-viewer-header">
                                <div>Tài liệu: {doc_name} | Dòng {l_start} - {l_end} (Tổng {total_lines} dòng)</div>
                                <div>Độ tin cậy: {score:.3f}</div>
                            </div>
                            {hl_html}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                except Exception as e:
                    st.error(f"Không thể hiển thị văn bản: {e}")
        else:
            st.markdown(
                """
                <div class="doc-viewer-card" style="display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;">
                    <div style="color:#8e918f; font-size:0.95rem; font-weight:500;">Chưa có đoạn trích dẫn nào được chọn.</div>
                    <div style="color:#5e6266; font-size:0.8rem; margin-top:0.4rem; max-width:380px;">
                        Hãy đặt câu hỏi ở khung bên trái hoặc nhấn nút "Xem văn bản gốc" dưới câu trả lời của AI để xem đoạn điều khoản được tô màu trực tiếp tại đây.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------- TAB 2: QUẢN LÝ & TẢI LÊN TÀI LIỆU ----------------
if tab_docs is not None:
    with tab_docs:
        st.markdown("### Quản lý kho tài liệu tri thức")
        st.caption("Tải lên tài liệu mới (TXT, Markdown, PDF) để hệ thống tự động lập chỉ mục và phân quyền truy cập.")

        col_up, col_inventory = st.columns([1, 2], gap="large")

        with col_up:
            st.markdown("**Tải lên tài liệu mới**")
            uploaded_file = st.file_uploader(
                "Chọn file tài liệu:",
                type=["txt", "md", "pdf"],
                label_visibility="collapsed",
            )
            
            dept_options = {
                "GENERAL": "Chung (Tất cả nhân viên xem được)",
                "LEGAL": "Pháp chế (Chỉ phòng Pháp chế & Quản trị)",
                "HR": "Nhân sự (Chỉ phòng Nhân sự & Quản trị)",
                "FINANCE": "Kế toán (Chỉ phòng Kế toán & Quản trị)",
            }
            class_options = {
                "PUBLIC": "Công khai (Tất cả mọi người)",
                "INTERNAL": "Nội bộ (Nhân viên chính thức)",
                "CONFIDENTIAL": "Bảo mật (Chỉ cấp quản lý)",
                "RESTRICTED": "Tối mật (Chỉ Ban Giám đốc & Quản trị)",
            }

            up_dept_key = st.selectbox("Phòng ban áp dụng:", list(dept_options.keys()), format_func=lambda k: dept_options[k])
            up_class_key = st.selectbox("Cấp độ bảo mật:", list(class_options.keys()), format_func=lambda k: class_options[k])

            if st.button("Lập chỉ mục ngay", use_container_width=True, disabled=(uploaded_file is None)):
                if uploaded_file is not None:
                    with st.spinner("Đang tách đoạn, tính toán tọa độ dòng và tạo vector chỉ mục..."):
                        file_bytes = uploaded_file.read()
                        res = client.upload_document(
                            file_bytes=file_bytes,
                            filename=uploaded_file.name,
                            department=up_dept_key,
                            classification=up_class_key,
                            uploaded_by=active_u.get("username", "admin"),
                        )
                        st.success(f"Đã lập chỉ mục thành công file {uploaded_file.name} với {res.get('chunks_indexed', 0)} đoạn dữ liệu.")
                        st.rerun()

            st.markdown("---")
            if st.button("Đồng bộ lại toàn bộ 8 tài liệu mẫu", use_container_width=True):
                with st.spinner("Đang đồng bộ dữ liệu mẫu..."):
                    res = client.ingest_samples()
                    st.success(f"Đã đồng bộ thành công {res.get('total_chunks_indexed', 0)} đoạn văn bản.")
                    st.rerun()

        with col_inventory:
            st.markdown("**Danh mục tài liệu trong hệ thống**")
            if is_backend_online:
                doc_data = client.list_documents()
                docs = doc_data.get("documents", [])
                st.caption(f"Tổng số tài liệu: {len(docs)} | Tổng số đoạn trích dẫn đã vector hóa: {doc_data.get('total_chunks', 0)}")

                for d in docs:
                    c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
                    with c1:
                        st.markdown(f"**{d['name']}**")
                        st.caption(f"Kích thước: {d['size_bytes']:,} bytes | Số dòng: {d.get('lines', 0)} | Số đoạn: {d['chunks']}")
                    with c2:
                        st.markdown(f'<span class="badge-role">{d.get("classification", "INTERNAL")}</span>', unsafe_allow_html=True)
                    with c3:
                        st.markdown(f'<span class="tag-badge" style="background:#282a2d; padding:3px 8px; border-radius:6px; font-size:0.75rem;">Phòng: {d.get("department", "GENERAL")}</span>', unsafe_allow_html=True)
                    with c4:
                        if st.button("Xóa", key=f"del_doc_{d['name']}"):
                            client.delete_document(d["name"])
                            st.rerun()
                    st.markdown("<hr style='border: 0; border-top: 1px solid #232528; margin: 6px 0;' />", unsafe_allow_html=True)


# ---------------- TAB 3: NHẬT KÝ & GIÁM SÁT HỆ THỐNG (CHỈ DÀNH CHO DEV/ADMIN) ----------------
if tab_audit is not None:
    with tab_audit:
        st.markdown("### Nhật ký kiểm toán & Giám sát vận hành (Audit Trail)")
        st.caption("Khu vực dành riêng cho Quản trị viên & Kỹ sư hệ thống để theo dõi an toàn dữ liệu và hiệu năng.")

        if is_backend_online:
            metrics = client.get_audit_metrics()

            # Thẻ chỉ số tổng quan
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                st.markdown(f'<div class="metric-box"><div class="metric-value">{metrics.get("total_queries", 0)}</div><div class="metric-label">Tổng lượt truy vấn</div></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="metric-box"><div class="metric-value">{metrics.get("avg_latency_ms", 0.0):.1f} ms</div><div class="metric-label">Thời gian phản hồi TB</div></div>', unsafe_allow_html=True)
            with m3:
                st.markdown(f'<div class="metric-box"><div class="metric-value">{metrics.get("pii_violations_prevented", 0)}</div><div class="metric-label">Thông tin cá nhân đã che</div></div>', unsafe_allow_html=True)
            with m4:
                st.markdown(f'<div class="metric-box"><div class="metric-value">{metrics.get("positive_feedbacks", 0)} / {metrics.get("negative_feedbacks", 0)}</div><div class="metric-label">Hài lòng / Chưa hài lòng</div></div>', unsafe_allow_html=True)
            with m5:
                st.markdown(f'<div class="metric-box"><div class="metric-value">{metrics.get("total_documents", 0)}</div><div class="metric-label">Tài liệu đã lưu trữ</div></div>', unsafe_allow_html=True)

            st.markdown("<br />", unsafe_allow_html=True)
            col_hdr, col_ref = st.columns([4, 1])
            with col_hdr:
                st.markdown("**Nhật ký hoạt động gần nhất**")
            with col_ref:
                if st.button("Làm mới nhật ký", use_container_width=True):
                    st.rerun()

            logs = client.get_audit_logs(limit=25)
            if logs:
                for l in logs:
                    c_time, c_user, c_action, c_query, c_lat = st.columns([2, 2, 2, 5, 2])
                    with c_time:
                        st.caption(l.get("created_at", ""))
                    with c_user:
                        st.markdown(f"<span style='font-size:0.8rem;'>{l.get('username', '')} ({l.get('role', '')})</span>", unsafe_allow_html=True)
                    with c_action:
                        act_text = l.get("action", "")
                        if "BLOCK" in act_text:
                            badge_style = "color:#f87171; background:rgba(248,113,113,0.15);"
                        else:
                            badge_style = "color:#3fb950; background:rgba(63,185,80,0.15);"
                        st.markdown(f'<span style="padding:2px 8px; border-radius:4px; font-size:0.75rem; {badge_style}">{act_text}</span>', unsafe_allow_html=True)
                    with c_query:
                        q_text = str(l.get("query_text", ""))
                        st.markdown(f"<span style='font-size:0.8rem;'>{q_text[:75]}..</span>", unsafe_allow_html=True)
                    with c_lat:
                        st.caption(f"{l.get('latency_ms', 0):.1f} ms")
                    st.markdown("<hr style='border: 0; border-top: 1px solid #232528; margin: 4px 0;' />", unsafe_allow_html=True)
            else:
                st.caption("Chưa có nhật ký kiểm toán nào.")


# ---------------- TAB 4: ĐO LƯỜNG CHẤT LƯỢNG (CHỈ DÀNH CHO DEV/ADMIN) ----------------
if tab_eval is not None:
    with tab_eval:
        st.markdown("### Đo lường chất lượng hệ thống RAG Triad")
        st.caption("Khu vực kiểm thử dành cho Kỹ thuật viên (Dev) để đánh giá độ trung thực và độ tương quan ngữ cảnh.")

        if st.button("Chạy bài kiểm thử chất lượng", use_container_width=False):
            with st.spinner("Đang chạy kiểm thử qua các bộ luật và quy chế..."):
                res = client.run_benchmark()
                st.success("Hoàn tất đánh giá chất lượng mô hình.")

                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    st.markdown(f'<div class="metric-box"><div class="metric-value">{res.get("avg_faithfulness", 0.0):.2f}</div><div class="metric-label">Độ trung thực (Faithfulness)</div></div>', unsafe_allow_html=True)
                with b2:
                    st.markdown(f'<div class="metric-box"><div class="metric-value">{res.get("avg_context_relevance", 0.0):.2f}</div><div class="metric-label">Độ tương quan (Context Relevance)</div></div>', unsafe_allow_html=True)
                with b3:
                    st.markdown(f'<div class="metric-box"><div class="metric-value">{res.get("avg_latency_ms", 0.0):.1f} ms</div><div class="metric-label">Độ trễ trung bình</div></div>', unsafe_allow_html=True)
                with b4:
                    st.markdown(f'<div class="metric-box"><div class="metric-value">{res.get("total_evaluations", 0)}</div><div class="metric-label">Số bài kiểm thử</div></div>', unsafe_allow_html=True)

                st.markdown("<br />", unsafe_allow_html=True)
                st.markdown("**Chi tiết kết quả từng câu hỏi:**")
                for item in res.get("details", []):
                    with st.expander(f"Câu hỏi: {item.get('query')}"):
                        st.markdown(f"**Độ trung thực:** `{item.get('faithfulness'):.2f}` | **Độ tương quan:** `{item.get('context_relevance'):.2f}` | **Thời gian:** `{item.get('latency_ms'):.1f} ms`")
                        st.markdown(f"**Câu trả lời của AI:**\n{item.get('answer')}")

