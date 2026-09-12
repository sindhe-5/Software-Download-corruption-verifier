import csv
import io
import time
import zlib
from datetime import datetime

import streamlit as st


st.set_page_config(
    page_title="Software Download Corruption Verifier",
    page_icon="✓",
    layout="wide",
)

# Professional styling
st.markdown(
    """
    <style>
    .main { background-color: #f7f9fc; }
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    .hero { background: linear-gradient(135deg, #123b68, #1f6aa5); color: white;
            padding: 1.6rem 2rem; border-radius: 14px; margin-bottom: 1.2rem; }
    .hero h1 { margin: 0; font-size: 2rem; }
    .hero p { margin: .35rem 0 0; opacity: .9; }
    .result-valid { background: #e8f7ee; border: 1px solid #8fd3a8; color: #176b38;
                    padding: 1rem; border-radius: 10px; font-weight: 700; font-size: 1.25rem; }
    .result-invalid { background: #fff0f0; border: 1px solid #e2a0a0; color: #a12525;
                      padding: 1rem; border-radius: 10px; font-weight: 700; font-size: 1.25rem; }
    .small-note { color: #5b6777; font-size: .9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def crc32_hex(data: bytes) -> str:
    """Return the standard unsigned CRC-32 as eight uppercase hex digits."""
    return f"{zlib.crc32(data) & 0xFFFFFFFF:08X}"


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024**2:
        return f"{size / 1024:.2f} KB"
    if size < 1024**3:
        return f"{size / 1024**2:.2f} MB"
    return f"{size / 1024**3:.2f} GB"


def corrupted_copy(data: bytes) -> tuple[bytes, int]:
    """Flip one bit in a temporary copy and return modified data and byte index."""
    if not data:
        return data, -1
    changed = bytearray(data)
    index = len(changed) // 2
    changed[index] ^= 0x01
    return bytes(changed), index


def create_csv(result: dict) -> bytes:
    output = io.StringIO()
    fields = [
        "timestamp", "algorithm", "original_file", "current_file",
        "original_size_bytes", "current_size_bytes", "reference_crc32",
        "current_crc32", "status", "verification_time_seconds", "notes",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerow(result)
    return output.getvalue().encode("utf-8")


if "verification" not in st.session_state:
    st.session_state.verification = None
if "simulated_data" not in st.session_state:
    st.session_state.simulated_data = None
if "simulated_name" not in st.session_state:
    st.session_state.simulated_name = None

st.markdown(
    """
    <div class="hero">
      <h1>Software Download Corruption Verifier</h1>
      <p>CRC-32 based file-integrity verification dashboard</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Group Project")
    st.write("**Product:** Software Download Corruption Verifier")
    st.write("**Group number:** 3")
    st.write("**Product number:** 9")
    st.write("**Batch:** 29")
    st.markdown("**Team members**")
    st.markdown(
        "- S. Amrutha\n"
        "- Deepthi\n"
        "- Varsha\n"
        "- Anand\n"
        "- Uzair Ahmed"
    )
    st.divider()
    st.header("How it works")
    st.caption("1. Upload the original file and downloaded file.\n\n"
               "2. Python calculates CRC-32 for both files.\n\n"
               "3. The dashboard compares the values.\n\n"
               "4. Matching values are VALID; different values are CORRUPTED.")

st.subheader("1. Upload files")
col1, col2 = st.columns(2)
with col1:
    original = st.file_uploader(
        "Original/reference file",
        type=None,
        key="original",
        help="The trusted file before download or transfer.",
    )
with col2:
    current = st.file_uploader(
        "Downloaded/current file",
        type=None,
        key="current",
        help="The file you want to verify.",
    )

if original and current:
    st.success("Both files uploaded. You can calculate their CRC-32 values.")
elif original or current:
    st.info("Upload both files to begin verification.")
else:
    st.info("Start by uploading an original file and a downloaded file.")

st.subheader("2. Verify integrity")
action_col1, action_col2, action_col3 = st.columns([1, 1, 1])
with action_col1:
    calculate = st.button("Calculate CRC-32", type="primary", use_container_width=True)
with action_col2:
    simulate = st.button("Simulate Corruption", use_container_width=True,
                         help="Creates a temporary copy with one bit changed.")
with action_col3:
    clear = st.button("Clear Result", use_container_width=True)

if clear:
    st.session_state.verification = None
    st.session_state.simulated_data = None
    st.session_state.simulated_name = None
    st.rerun()

if simulate:
    if not original:
        st.warning("Upload the original file first so a corrupted copy can be created.")
    else:
        original_data = original.getvalue()
        modified, index = corrupted_copy(original_data)
        if not modified:
            st.warning("The uploaded file is empty, so corruption cannot be simulated.")
        else:
            st.session_state.simulated_data = modified
            st.session_state.simulated_name = f"corrupted_{original.name}"
            st.success(f"Temporary corrupted copy created by changing one bit near byte {index}.")
            st.download_button(
                "Download simulated corrupted file",
                data=modified,
                file_name=st.session_state.simulated_name,
                mime="application/octet-stream",
            )

if calculate:
    if not original or not current:
        st.error("Please upload both the original and downloaded files before calculating.")
    else:
        original_data = original.getvalue()
        current_data = current.getvalue()
        started = time.perf_counter()
        reference_crc = crc32_hex(original_data)
        current_crc = crc32_hex(current_data)
        elapsed = time.perf_counter() - started
        valid = reference_crc == current_crc
        result = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "algorithm": "CRC-32",
            "original_file": original.name,
            "current_file": current.name,
            "original_size_bytes": len(original_data),
            "current_size_bytes": len(current_data),
            "reference_crc32": reference_crc,
            "current_crc32": current_crc,
            "status": "VALID" if valid else "CORRUPTED",
            "verification_time_seconds": f"{elapsed:.6f}",
            "notes": "CRC values match" if valid else "CRC values differ",
        }
        st.session_state.verification = result

result = st.session_state.verification
if result:
    st.subheader("3. Verification result")
    valid = result["status"] == "VALID"
    if valid:
        st.markdown("<div class='result-valid'>VALID — No corruption detected</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='result-invalid'>CORRUPTED — Error detected</div>", unsafe_allow_html=True)

    st.write("")
    a, b, c, d = st.columns(4)
    a.metric("Reference CRC-32", result["reference_crc32"])
    b.metric("Current CRC-32", result["current_crc32"])
    c.metric("Original size", format_size(result["original_size_bytes"]))
    d.metric("Current size", format_size(result["current_size_bytes"]))

    details = {
        "Algorithm": result["algorithm"],
        "Original file": result["original_file"],
        "Downloaded/current file": result["current_file"],
        "Verification time": f'{result["verification_time_seconds"]} seconds',
        "Explanation": result["notes"],
    }
    st.table(details)
    st.download_button(
        "Download CSV verification report",
        data=create_csv(result),
        file_name="crc32_verification_report.csv",
        mime="text/csv",
        use_container_width=False,
    )

st.divider()
st.subheader("4. Demonstration flow")
st.code(
    "Upload files → Read file bytes → Calculate CRC-32 → Compare CRC values → Display VALID/CORRUPTED",
    language="text",
)
st.markdown(
    "<p class='small-note'>CRC-32 detects changes by producing a compact checksum for the file contents. "
    "It does not repair a corrupted file; it reports whether the calculated values match.</p>",
    unsafe_allow_html=True,
)

with st.expander("Viva explanation"):
    st.write(
        "The dashboard captures two uploaded files. The Python backend reads both files as bytes and uses "
        "the standard CRC-32 calculation. The original file's value is treated as the reference CRC. "
        "The downloaded file's CRC is compared with it. If both values match, the dashboard displays VALID; "
        "otherwise, it displays CORRUPTED."
    )
    st.write(
        "The Simulate Corruption button flips one bit in a temporary copy. This demonstrates that even a "
        "small change produces a different CRC-32 value."
    )

st.caption("Project MVP | Group 3 | Product 9")

if __name__ == "__main__":
    pass
