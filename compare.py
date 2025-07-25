import streamlit as st
import argparse
import os
from datetime import datetime

def main():
    st.title("Retrospective Comparison")

    parser = argparse.ArgumentParser(description="Compare retrospectives from two different directories.")
    parser.add_argument("dir1", help="The first retrospectives directory.")
    parser.add_argument("dir2", help="The second retrospectives directory.")
    
    # This is a bit of a hack to get argparse to work with streamlit
    try:
        args = parser.parse_args()
    except SystemExit as e:
        # This prevents Streamlit from exiting when no args are provided
        st.stop()

    dir1 = args.dir1
    dir2 = args.dir2

    st.sidebar.header("Options")
    level = st.sidebar.selectbox("Level", ["daily", "weekly", "monthly", "yearly"])
    
    # Date selection
    selected_date = st.sidebar.date_input("Select a date", datetime.now())

    # Logic to find and display files
    file_path1, file_path2 = get_file_paths(dir1, dir2, level, selected_date)

    col1, col2 = st.columns(2)

    with col1:
        st.header(os.path.basename(dir1))
        if file_path1 and os.path.exists(file_path1):
            with open(file_path1, "r") as f:
                st.markdown(f.read())
        else:
            st.warning("File not found.")

    with col2:
        st.header(os.path.basename(dir2))
        if file_path2 and os.path.exists(file_path2):
            with open(file_path2, "r") as f:
                st.markdown(f.read())
        else:
            st.warning("File not found.")

def get_file_paths(dir1, dir2, level, selected_date):
    year = selected_date.year
    month = selected_date.strftime("%m")
    day = selected_date.strftime("%d")
    week = selected_date.strftime("%W")

    if level == "daily":
        path = os.path.join(str(year), month, f"r{year}-{month}-{day}.md")
    elif level == "weekly":
        path = os.path.join(str(year), "weeks", f"r{year}-W{week}.md")
    elif level == "monthly":
        path = os.path.join(str(year), "months", f"r{year}-{month}.md")
    elif level == "yearly":
        path = os.path.join(str(year), f"r{year}.md")
    else:
        return None, None

    return os.path.join(dir1, path), os.path.join(dir2, path)

if __name__ == "__main__":
    main()
