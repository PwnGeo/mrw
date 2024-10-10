import datetime
import random
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

# Configure the SQLite database
def init_sqlite_db():
    conn = sqlite3.connect('projects.db')  # đổi file database thành projects.db
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            description TEXT,
            status TEXT,
            priority TEXT,
            date_submitted TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_project_to_db(project_data):
    conn = sqlite3.connect('projects.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO projects (id, description, status, priority, date_submitted)
        VALUES (?, ?, ?, ?, ?)
    ''', project_data)
    conn.commit()
    conn.close()

def delete_project_from_db(project_id):
    conn = sqlite3.connect('projects.db')
    c = conn.cursor()
    c.execute('DELETE FROM projects WHERE id = ?', (project_id,))
    conn.commit()
    conn.close()

def load_projects_from_db():
    conn = sqlite3.connect('projects.db')
    df = pd.read_sql_query("SELECT * FROM projects", conn)
    conn.close()
    return df

# Initialize SQLite database
init_sqlite_db()

# Show app title and description
st.set_page_config(page_title="Hệ Thống Quản Lý Dự Án", page_icon="📊")
st.title("📊 Quản Lý Dự Án")
st.write("""
    Chào mừng bạn đến với hệ thống quản lý dự án của công ty Miraway! Hệ thống này được thiết kế để giúp bạn theo dõi và quản lý thông tin dự án một cách hiệu quả nhất.
""")

# Load existing projects from the database or create new projects
df = load_projects_from_db()

# Show a section to add a new project
st.header("Điền thông tin cần thiết như mô tả dự án và mức độ ưu tiên.")

with st.form("add_project_form"):
    description = st.text_area("Mô tả dự án")
    priority = st.selectbox("Mức độ ưu tiên", ["Cao", "Trung bình", "Thấp"])
    submitted = st.form_submit_button("Tạo mới")

if submitted:
    recent_project_number = len(df) + 1  # Tự động tăng số dự án dựa trên các dự án hiện có.
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    new_project_id = f"PROJECT-{recent_project_number}"
    
    # Add the new project to the database
    add_project_to_db((new_project_id, description, "Mở", priority, today))
    
    # Refresh the DataFrame
    df = load_projects_from_db()

    # Display success message
    st.write("Dự án đã được tạo mới! Dưới đây là thông tin dự án:")
    st.dataframe(pd.DataFrame([[new_project_id, description, "Mở", priority, today]],
                               columns=["ID", "Mô tả", "Tình trạng", "Mức độ ưu tiên", "Ngày gửi"]),
                 use_container_width=True, hide_index=True)

# Show section to view and edit existing projects in a table
st.header("Các dự án hiện có")
st.write(f"Số lượng dự án tham gia: `{len(df)}`")

st.info(
    "Bạn có thể chỉnh sửa các dự án bằng cách nhấp đúp vào một ô. Lưu ý rằng các biểu đồ bên dưới "
    "sẽ tự động cập nhật! Bạn cũng có thể sắp xếp bảng bằng cách nhấp vào tiêu đề cột.",
    icon="✍️",
)

# Show the projects dataframe with `st.data_editor`
edited_df = st.data_editor(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "status": st.column_config.SelectboxColumn(
            "Tình trạng",
            help="Tình trạng dự án",
            options=["Mở", "Đang xử lý", "Đã đóng"],
            required=True,
        ),
        "priority": st.column_config.SelectboxColumn(
            "Mức độ ưu tiên",
            help="Mức độ ưu tiên",
            options=["Cao", "Trung bình", "Thấp"],
            required=True,
        ),
    },
    disabled=["id", "date_submitted"],
)

# Show some metrics and charts about the project

st.header("Thống kê")

# col1, col2, col3 = st.columns(3)
# num_open_projects = len(df[df.status == "Mở"])
# col1.metric(label="Số lượng dự án đang mở", value=num_open_projects, delta=0)
# col2.metric(label="Thời gian phản hồi đầu tiên (giờ)", value=5.2, delta=-1.5)
# col3.metric(label="Thời gian giải quyết trung bình (giờ)", value=16, delta=2)
# Show some metrics and charts about the project
if len(df) > 0:  # Chỉ hiển thị thống kê nếu có dự án
    col1, col2, col3 = st.columns(3)
    num_open_projects = len(df[df.status == "Mở"])
    col1.metric(label="Số lượng dự án đang mở", value=num_open_projects, delta=0)
    col2.metric(label="Thời gian phản hồi đầu tiên (giờ)", value=5.2, delta=-1.5)
    col3.metric(label="Thời gian giải quyết trung bình (giờ)", value=16, delta=2)

    # Display Altair charts
    st.write("##### Tình trạng dự án theo tháng")

    # Đổi định dạng của cột `date_submitted` thành kiểu datetime và tạo cột tháng với định dạng dd-mm-yyyy
    df['date_submitted'] = pd.to_datetime(df['date_submitted'])
    df['month'] = df['date_submitted'].dt.strftime('%d-%m-%Y')

    status_plot = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("month:O", axis=alt.Axis(labelAngle=0)),
            y="count():Q",
            xOffset="status:N",
            color="status:N",
        )
        .configure_legend(
            orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
        )
    )
    st.altair_chart(status_plot, use_container_width=True, theme="streamlit")

    st.write("##### Các mức độ ưu tiên hiện tại")
    priority_plot = (
        alt.Chart(df)
        .mark_arc()
        .encode(theta="count():Q", color="priority:N")
        .properties(height=300)
        .configure_legend(
            orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
        )
    )
    st.altair_chart(priority_plot, use_container_width=True, theme="streamlit")

else:
    st.write("Hiện không có dự án nào để hiển thị.")  # Thông báo không có dự án

# Xóa dự án theo ID người dùng nhập
st.header("Xóa dự án")
project_id_to_delete = st.text_input("Nhập ID dự án muốn xóa (ví dụ: PROJECT-1)")

if st.button("Xóa dự án"):
    if project_id_to_delete in df['id'].values:
        delete_project_from_db(project_id_to_delete)
        st.success(f"Dự án {project_id_to_delete} đã được xóa.")
        # Tải lại danh sách dự án
        df = load_projects_from_db()
    else:
        st.error("ID dự án không tồn tại. Vui lòng kiểm tra lại.")

# Save the edited projects back to the SQLite database if there are changes
if st.button("Lưu thay đổi"):
    with sqlite3.connect('projects.db') as conn:
        for index, row in edited_df.iterrows():
            conn.execute('''
                UPDATE projects
                SET status = ?, priority = ?
                WHERE id = ?
            ''', (row["status"], row["priority"], row["id"]))
        conn.commit()
    st.success("Các thay đổi đã được lưu thành công!")

# End of the Streamlit app
