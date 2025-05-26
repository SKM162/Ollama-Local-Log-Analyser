import streamlit as st
import json
import os
from datetime import datetime, timezone, timedelta
import re

st.set_page_config(layout="wide", page_title="Ollama Log Viewer")

# Widen Streamlit layout with custom CSS
st.markdown("""
    <style>
        /* Override main container to full width */
        .main .block-container {
            max-width: 100% !important;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* Expand expander to 100% width */
        .stExpander {
            width: 100% !important;
        }

        /* Ensure nested content inside expanders also uses full width */
        .stExpander > div {
            width: 100% !important;
        }

        /* Make code blocks scrollable if needed */
        pre, code {
            overflow-x: auto;
            white-space: pre-wrap;
        }

        /* Force content containers to use full available width */
        .element-container {
            width: 100% !important;
        }
    </style>
""", unsafe_allow_html=True)


def extract_number(filename):
    match = re.match(r"(\d+)-", filename)
    return int(match.group(1)) if match else float("inf")


def convert_to_ist(utc_string):
    try:
        utc_time = datetime.fromisoformat(utc_string.replace("Z", "+00:00"))
        ist_offset = timedelta(hours=5, minutes=30)
        ist_time = utc_time.astimezone(timezone(ist_offset))
        return ist_time.strftime("%Y-%m-%d %I:%M:%S %p IST")
    except Exception as e:
        return f"(Invalid timestamp: {utc_string})"


# --- Helper: Reconstruct assistant response from streamed chunks
def reconstruct_response(response_body):
    if isinstance(response_body, list):
        # Streamed response
        return ''.join(chunk['message']['content'] for chunk in response_body if not chunk.get('done'))
    elif isinstance(response_body, dict):
        # Single complete response
        return response_body.get('message', {}).get('content', '')
    return ''


# --- Helper: Extract summary stats
def extract_summary(response_body):
    if isinstance(response_body, list):
        for chunk in response_body:
            if chunk.get("done", False):
                return {
                    "tokens_in": chunk.get("prompt_eval_count", 0),
                    "tokens_out": chunk.get("eval_count", 0),
                    "total_duration_sec": chunk.get("total_duration", 0) / 1e9,
                    "eval_per_token_ms": chunk.get("eval_duration", 0) / max(chunk.get("eval_count", 1), 1) / 1e6,
                    "prompt_per_token_ms": chunk.get("prompt_eval_duration", 0) / max(chunk.get("prompt_eval_count", 1), 1) / 1e6,
                }
    elif isinstance(response_body, dict):
        return {
            "tokens_in": response_body.get("prompt_eval_count", 0),
            "tokens_out": response_body.get("eval_count", 0),
            "total_duration_sec": response_body.get("total_duration", 0) / 1e9,
            "eval_per_token_ms": response_body.get("eval_duration", 0) / max(response_body.get("eval_count", 1), 1) / 1e6,
            "prompt_per_token_ms": response_body.get("prompt_eval_duration", 0) / max(response_body.get("prompt_eval_count", 1), 1) / 1e6,
        }
    return {}

# --- Load logs from folder
def load_logs(folder_path):
    logs = []
    for fname in sorted(os.listdir(folder_path), key=extract_number):
        if fname.endswith(".json"):
            with open(os.path.join(folder_path, fname), "r") as f:
                try:
                    data = json.load(f)
                    if isinstance(data, dict):
                        logs.append({
                            "_filename": fname,
                            "content": data
                        })
                except Exception as e:
                    st.warning(f"⚠️ Failed to load {fname}: {e}")
    return logs

# --- Main UI
# Sidebar for file selection
st.sidebar.title("🧠 Ollama Agent Log Viewer")

with st.sidebar.expander("📁 Select Log folder path"):
    st.markdown("### Choose Log folder path:")
    preset_dirs = ["./logs"]
    log_dir = st.selectbox("Preset log folders", preset_dirs)
    custom_dir = st.text_input("Or enter custom log folder path", "")

# Use custom path if provided, else use dropdown
final_log_dir = custom_dir if custom_dir else log_dir

logs = load_logs(final_log_dir)
log_names = [log["_filename"] for log in logs]

if not logs:
    st.info("No logs loaded. Add .json files to the folder.")
    st.stop()


# --- Navigation Buttons (Reusable)
def go_prev():
    if st.session_state.selected_index > 0:
        st.session_state.selected_index -= 1

def go_next():
    if st.session_state.selected_index < len(log_names) - 1:
        st.session_state.selected_index += 1

col1, col2 = st.sidebar.columns(2)
col1.button("⬅️ Previous", key=f"prev", use_container_width=True, on_click=go_prev)
col2.button("➡️ Next", key=f"next", use_container_width=True, on_click=go_next)


# Search feature
def log_matches_search(log_data, query):
    log = log_data["content"]
    filename = log_data["_filename"]
    model = log.get("request", {}).get("body", {}).get("model", "")
    messages = log.get("request", {}).get("body", {}).get("messages", [])

    combined_text = filename + " " + model + " " + " ".join(
        m.get("content", "") for m in messages
    )

    return query.lower() in combined_text.lower()

# --- Step 1: Setup
if "search_box" not in st.session_state:
    st.session_state.search_box = ""

if "clear_search" not in st.session_state:
    st.session_state.clear_search = False

# --- Step 2: UI
search_col, clear_col = st.sidebar.columns([5, 1], vertical_alignment="bottom")

with search_col:
    search_query = st.text_input("## 🔍 Search logs", value=st.session_state.search_box, key="search_box")

def clear_search():
    st.session_state.search_box = ""

with clear_col:
    st.button("❌", help="Clear search", on_click=clear_search)

# --- Step 3: After UI
# Apply clear action after rerun
if st.session_state.clear_search:
    st.session_state.search_box = ""
    st.session_state.clear_search = False
    st.rerun()


query = st.session_state.get("search_box", "")
if query:
    filtered_logs = [log for log in logs if log_matches_search(log, query)]
else:
    filtered_logs = logs


filtered_log_names = [log["_filename"] for log in filtered_logs]


# Set initial state once
if "selected_index" not in st.session_state:
    st.session_state.selected_index = 0

# Use radio bound directly to session state
if not filtered_logs:
    st.sidebar.warning("No logs match your search.")
    st.stop()

st.sidebar.radio(
    "🗂️ Select a log",
    options=range(len(filtered_logs)),
    format_func=lambda i: filtered_log_names[i],
    key="selected_index"
)

selected_log = filtered_logs[st.session_state.selected_index]
selected_index = st.session_state.selected_index
log = selected_log["content"]
fname = selected_log["_filename"]


# --- Build a table view
try:
    timestamp = log["timestamp"]
    model = log["request"]["body"]["model"]
    messages = log["request"]["body"]["messages"]
    user_prompt = [m["content"] for m in messages if m["role"] == "user"][-1]
    response_chunks = log["response"].get("body")
    if response_chunks is None:
        raise ValueError("Response missing body — likely a failed API call.")

    full_response = reconstruct_response(response_chunks)
    summary = extract_summary(response_chunks)

    st.markdown("### 📝 Log Details:")
    st.markdown(f"**📄 Log File Name:** `{fname}`")
    st.markdown(f"**🕓 Timestamp (IST):** `{convert_to_ist(timestamp)}`")
    st.markdown(f"**🤖 Model:** `{model}`")

    st.markdown("### 🧠 Prompt Conversation")

    role_labels = {
        "system": "🛠️ System",
        "user": "🧑 User",
        "assistant": "🤖 Assistant"
    }

    role_colors = {
        "system": "#eee",
        "user": "#d1e7dd",
        "assistant": "#e7d1dd"
    }

    for m in messages:
        role = m.get("role", "unknown")
        label = role_labels.get(role, f"🔹 {role}")
        bg_color = role_colors.get(role, "#f8f9fa")
        
        with st.expander(f"**{label}**", True):
            st.code(m.get("content", ""), language="text")

    with st.expander("### 🤖 Assistant Response", True):
        st.code(full_response)

    st.markdown("### 📊 Response Stats")
    st.markdown(f"""
    - 🧾 **Prompt tokens:** {summary.get("tokens_in", "?")}
    - ✍️ **Generated tokens:** {summary.get("tokens_out", "?")}
    - ⏱️ **Total time:** {summary.get("total_duration_sec", 0):.2f} seconds
    - ⚙️ **Generation time per token:** {summary.get("eval_per_token_ms", 0):.2f} ms
    - 🧠 **Prompt processing time per token:** {summary.get("prompt_per_token_ms", 0):.2f} ms
    """)

    st.markdown("""
        ### ℹ️ What do these stats mean?
        - **Prompt tokens**: Number of tokens in the user/system messages.
        - **Generated tokens**: Tokens the model produced.
        - **Total time**: Time from request start to final token.
        - **Generation time per token**: Avg time to compute each output token.
        - **Prompt processing time per token**: How long the model spent understanding the input.
        """)

except Exception as e:
    st.error(f"❌ Error parsing {fname}: {e}")
