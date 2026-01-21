import streamlit as st
import json
import os
import argparse
from PIL import Image


# 1. Argument Parser for Command Line
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_dir", type=str, default="./test_images",
                        help="Images root directory")
    parser.add_argument("-j", "--json_path", type=str, default="./results.json",
                        help="Path to results.json")
    # Using parse_known_args to avoid conflicts with Streamlit internal args
    args, _ = parser.parse_known_args()
    return args


args = get_args()

# 2. Page Configuration
st.set_page_config(layout="wide", page_title="ROC4MLLM Result Viewer")

st.title("🖼️ ROC4MLLM Assessment Viewer")

# 3. Path Display and Overrides
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

# --- Threshold Filtering UI ---
st.sidebar.subheader("Threshold Filter")
use_threshold = st.sidebar.checkbox("Enable Threshold Filter", value=False)
threshold_val = st.sidebar.slider("Threshold Score:", 0.0, 10.0, 5.5, step=0.1)
filter_mode = st.sidebar.radio("Display Group:", [">= Threshold (Pass)", "< Threshold (Fail)"])
# ------------------------------

sort_order = st.sidebar.selectbox("Sort by Score:", ["Original", "High to Low", "Low to High"])
cols_per_row = st.sidebar.slider("Images per row:", 1, 6, 4)
search_query = st.sidebar.text_input("Search file path:")

# 7. Filtering Logic
# A. Search Query Filter
if search_query:
    data = [d for d in data if search_query.lower() in d['file_path'].lower()]

# B. Threshold Logic Filter
if use_threshold:
    if filter_mode == ">= Threshold (Pass)":
        data = [d for d in data if d['score'] is not None and d['score'] >= threshold_val]
    else:
        data = [d for d in data if d['score'] is not None and d['score'] < threshold_val]

# 8. Sorting Logic
if sort_order == "High to Low":
    data = sorted(data, key=lambda x: x['score'] if x['score'] is not None else -1, reverse=True)
elif sort_order == "Low to High":
    data = sorted(data, key=lambda x: x['score'] if x['score'] is not None else 101)

# 9. Pagination
items_per_page = 40
total_items = len(data)
total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)

st.sidebar.write(f"Filtered results: **{total_items}**")
page = st.sidebar.number_input(f"Page (Total {total_pages})", min_value=1, max_value=total_pages, value=1)

start_idx = (page - 1) * items_per_page
display_batch = data[start_idx: start_idx + items_per_page]

# 10. Main Display Grid
st.divider()

if not display_batch:
    st.info("No results match the current filters.")
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
                    # Logic: Green if >= threshold, Red if < threshold
                    # Use the slider value if enabled, otherwise default to 5.5
                    current_threshold = threshold_val if use_threshold else 5.5

                    if score >= current_threshold:
                        color = "green"
                    else:
                        color = "red"

                    st.markdown(f"### Score: :{color}[{score}]")
                else:
                    st.markdown("### Score: :gray[N/A]")

                # Display Image
                if os.path.exists(full_img_path):
                    st.image(full_img_path, use_container_width=True)
                else:
                    st.error("File Not Found")
                    st.caption(f"Target: {rel_path}")

                # Analysis Comments
                with st.expander("View Comment"):
                    st.write(item.get('comment', 'No comment provided.'))