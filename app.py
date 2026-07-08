import json
import os
import uuid
from datetime import datetime

import streamlit as st

DATA_FILE = "todos.json"
CATEGORIES = ["업무", "개인", "공부"]
CATEGORY_COLORS = {
    "업무": "#3b6fe0",
    "개인": "#1f9d6b",
    "공부": "#a15be0",
}

st.set_page_config(page_title="할 일 관리", page_icon="✅", layout="centered")

st.markdown(
    """
    <style>
    .block-container { max-width: 640px; }
    .todo-text-done { text-decoration: line-through; color: #999; }
    .category-tag {
        padding: 3px 9px;
        border-radius: 999px;
        font-size: 11.5px;
        font-weight: 600;
        white-space: nowrap;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_todos():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("todos", [])
    except (json.JSONDecodeError, OSError):
        return []


def save_todos(todos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"todos": todos}, f, ensure_ascii=False, indent=2)


if "todos" not in st.session_state:
    st.session_state.todos = load_todos()

if "editing_id" not in st.session_state:
    st.session_state.editing_id = None

if "confirm_delete_id" not in st.session_state:
    st.session_state.confirm_delete_id = None


def add_todo(text, category):
    text = text.strip()
    if not text:
        return False
    st.session_state.todos.append(
        {
            "id": str(uuid.uuid4()),
            "text": text,
            "category": category,
            "done": False,
            "createdAt": datetime.now().isoformat(),
        }
    )
    save_todos(st.session_state.todos)
    return True


def update_todo_text(todo_id, new_text):
    new_text = new_text.strip()
    if not new_text:
        return
    for todo in st.session_state.todos:
        if todo["id"] == todo_id:
            todo["text"] = new_text
            break
    save_todos(st.session_state.todos)


def delete_todo(todo_id):
    st.session_state.todos = [t for t in st.session_state.todos if t["id"] != todo_id]
    save_todos(st.session_state.todos)


def toggle_done(todo_id, done):
    for todo in st.session_state.todos:
        if todo["id"] == todo_id:
            todo["done"] = done
            break
    save_todos(st.session_state.todos)


def category_badge(category, extra_style=""):
    color = CATEGORY_COLORS[category]
    return (
        f"<span class='category-tag' style='background:{color}22;color:{color};{extra_style}'>"
        f"{category}</span>"
    )


st.title("✅ 할 일 관리")

todos = st.session_state.todos
total = len(todos)
done_count = sum(1 for t in todos if t["done"])
percent = int(done_count / total * 100) if total else 0

st.markdown(f"**전체 진행률: {done_count}/{total} ({percent}%)**")
st.progress(percent / 100)

cat_cols = st.columns(len(CATEGORIES))
for col, category in zip(cat_cols, CATEGORIES):
    items = [t for t in todos if t["category"] == category]
    cat_done = sum(1 for t in items if t["done"])
    with col:
        st.markdown(
            category_badge(category, "font-size:12px;")
            + f" {cat_done}/{len(items)}",
            unsafe_allow_html=True,
        )

st.divider()

with st.form("add_form", clear_on_submit=True):
    input_col, cat_col, btn_col = st.columns([3, 1, 1])
    with input_col:
        new_text = st.text_input(
            "할 일", placeholder="할 일을 입력하세요", label_visibility="collapsed"
        )
    with cat_col:
        new_category = st.selectbox(
            "카테고리", CATEGORIES, index=1, label_visibility="collapsed"
        )
    with btn_col:
        submitted = st.form_submit_button("추가", use_container_width=True)

    if submitted and not add_todo(new_text, new_category):
        st.warning("할 일 내용을 입력해주세요.")

filter_choice = st.radio(
    "필터", ["전체"] + CATEGORIES, horizontal=True, label_visibility="collapsed"
)

filtered = (
    todos if filter_choice == "전체" else [t for t in todos if t["category"] == filter_choice]
)
filtered_sorted = sorted(filtered, key=lambda t: t["done"])  # 완료 항목은 안정 정렬로 하단 배치

if not filtered_sorted:
    st.info("표시할 할 일이 없습니다.")

for todo in filtered_sorted:
    todo_id = todo["id"]
    is_editing = st.session_state.editing_id == todo_id
    is_confirming_delete = st.session_state.confirm_delete_id == todo_id

    with st.container(border=True):
        row = st.columns([0.6, 1.3, 4.5, 1, 1])

        with row[0]:
            checked = st.checkbox(
                "완료", value=todo["done"], key=f"check_{todo_id}", label_visibility="collapsed"
            )
            if checked != todo["done"]:
                toggle_done(todo_id, checked)
                st.rerun()

        with row[1]:
            st.markdown(category_badge(todo["category"]), unsafe_allow_html=True)

        with row[2]:
            if is_editing:
                st.text_input(
                    "수정",
                    value=todo["text"],
                    key=f"edit_input_{todo_id}",
                    label_visibility="collapsed",
                )
            else:
                css_class = "todo-text-done" if todo["done"] else ""
                st.markdown(f"<span class='{css_class}'>{todo['text']}</span>", unsafe_allow_html=True)

        with row[3]:
            if is_editing:
                if st.button("저장", key=f"save_{todo_id}", use_container_width=True):
                    update_todo_text(todo_id, st.session_state[f"edit_input_{todo_id}"])
                    st.session_state.editing_id = None
                    st.rerun()
            elif is_confirming_delete:
                if st.button("취소", key=f"cancel_del_{todo_id}", use_container_width=True):
                    st.session_state.confirm_delete_id = None
                    st.rerun()
            else:
                if st.button("수정", key=f"edit_{todo_id}", use_container_width=True):
                    st.session_state.editing_id = todo_id
                    st.rerun()

        with row[4]:
            if is_editing:
                if st.button("취소", key=f"cancel_edit_{todo_id}", use_container_width=True):
                    st.session_state.editing_id = None
                    st.rerun()
            elif is_confirming_delete:
                if st.button("삭제확정", key=f"confirm_delete_{todo_id}", use_container_width=True):
                    delete_todo(todo_id)
                    st.session_state.confirm_delete_id = None
                    st.rerun()
            else:
                if st.button("삭제", key=f"delete_{todo_id}", use_container_width=True):
                    st.session_state.confirm_delete_id = todo_id
                    st.rerun()

        if is_confirming_delete:
            st.caption("정말 삭제할까요? 다시 한번 '삭제확정'을 눌러주세요.")
