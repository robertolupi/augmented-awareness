import streamlit as st
import argparse
import os
from datetime import datetime
from aww.file_manager import get_file_paths, read_file_content


def main():
    st.title("Retrospective Comparison")

    parser = argparse.ArgumentParser(description="Compare retrospectives from two different directories.")
    parser.add_argument("dir1", help="The first retrospectives directory.")
    parser.add_argument("dir2", help="The second retrospectives directory.")

    try:
        args = parser.parse_args()
    except SystemExit as e:
        st.stop()

    dir1 = args.dir1
    dir2 = args.dir2

    st.sidebar.header("Options")
    level = st.sidebar.selectbox("Level", ["daily", "weekly", "monthly", "yearly"])
    selected_date = st.sidebar.date_input("Select a date", datetime.now())

    file_path1, file_path2 = get_file_paths(dir1, dir2, level, selected_date)

    col1, col2 = st.columns(2)

    with col1:
        st.header(os.path.basename(dir1))
        if file_path1 and os.path.exists(file_path1):
            content = read_file_content(file_path1)
            st.markdown(content)
        else:
            st.warning(f"File not found: {file_path1}")

    with col2:
        st.header(os.path.basename(dir2))
        if file_path2 and os.path.exists(file_path2):
            content = read_file_content(file_path2)
            st.markdown(content)
        else:
            st.warning(f"File not found: {file_path2}")


if __name__ == "__main__":
    main()