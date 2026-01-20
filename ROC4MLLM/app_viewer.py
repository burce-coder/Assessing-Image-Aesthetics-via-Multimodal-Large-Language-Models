import streamlit as st
import json
import os
import sys
import argparse
from PIL import Image


# 1. Argument Parser for Command Line
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_dir", type=str, default="./test_images",
                        help="Images root directory")
    parser.add_argument("-j", "--json_path", type=str, default="./results.json",
                        help="Path to results.json")
    # Streamlit passes its own arguments, so we use parse_known_args
    args, _ = parser.parse_known_args()
    return args


args = get_args()

# 2. Page Configuration
st.set_page_config(layout="wide", page_title="ROC4MLLM Result Viewer")

st.title("🖼️ ROC4MLLM Assessment Viewer")

# 3. Path Display (Read-only or Override)
col1, col2 = st.columns(2)
with col1:
    json_path = st.text_input("JSON Path:", value=args.json_path)
with col2:
    img_root = st.text_input("Images Root Directory:", value=args.input_dir)

# 4. Data Validation
if not os.path.exists(json_path):
    st.error(f"❌ JSON file not found: {json_path}")
    st.stop()

# 5. Load Data
try:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    st.error(f"❌ Error reading JSON: {e}")
    st.stop()

# 6. Sidebar Controls
st.sidebar.header("Filter & Sort")
st.sidebar.info(f"Loaded: {os.path.basename(json_path)}")
st.sidebar.write(f"Total entries: **{len(data)}**")

sort_order = st.sidebar.selectbox("Sort by Score:", ["Original", "High to Low", "Low to High"])
cols_per_row = st.sidebar.slider("Images per row:", 1, 6, 4)
search_query = st.sidebar.text_input("Search file path:")

# 7. Sorting & Filtering Logic
if sort_order == "High to Low":
    data = sorted(data, key=lambda x: x['score'] if x['score'] is not None else -1, reverse=True)
elif sort_order == "Low to High":
    data = sorted(data, key=lambda x: x['score'] if x['score'] is not None else 101)

if search_query:
    data = [d for d in data if search_query.lower() in d['file_path'].lower()]

# 8. Pagination
items_per_page = 40
total_pages = max(1, (len(data) + items_per_page - 1) // items_per_page)
page = st.sidebar.number_input(f"Page (Total {total_pages})", min_value=1, max_value=total_pages, value=1)

start_idx = (page - 1) * items_per_page
display_batch = data[start_idx: start_idx + items_per_page]

# 9. Main Display Grid
st.divider()

if not display_batch:
    st.write("No results found.")
else:
    for i in range(0, len(display_batch), cols_per_row):
        cols = st.columns(cols_per_row)
        batch_row = display_batch[i: i + cols_per_row]

        for j, item in enumerate(batch_row):
            with cols[j]:
                rel_path = item['file_path']
                full_img_path = os.path.join(img_root, rel_path)

                score = item.get('score')
                if score is not None:
                    color = "green" if score > 75 else "orange" if score > 45 else "red"
                    st.markdown(f"### Score: :{color}[{score}]")
                else:
                    st.markdown("### Score: :gray[N/A]")

                if os.path.exists(full_img_path):
                    st.image(full_img_path, use_container_width=True)
                else:
                    st.error(f"File Not Found")
                    st.caption(f"Target: {rel_path}")

                with st.expander("View Comment"):
                    st.write(item.get('comment', 'No comment.'))