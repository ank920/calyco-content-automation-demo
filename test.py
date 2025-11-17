import os
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

print("Python:", os.sys.version)
print("GROQ_API_KEY present?", bool(API_KEY))

if not API_KEY:
    print("❌ GROQ_API_KEY is not set. Check your .env file.")
    exit()

print("Sending request to GROQ...")

url = "https://api.groq.com/openai/v1/chat/completions"

# Recommended safe model (fast + available)
model = "llama-3.1-8b-instant"

payload = {
    "model": model,
    "messages": [
        {"role": "user", "content": "Say 'GROQ test is successful'."}
    ],
    "max_tokens": 50
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print("HTTP status:", response.status_code)

# print entire response
print("Response:", response.text)




# dashboard/app_premium.py
"""
Calyco — Ultra-Premium macOS Dashboard
Upgraded: integrated pipeline runner, live logs, auto-refresh, plotly charts,
better image handling, expanded-blog support and improved UX.
"""
import os
import subprocess
import threading
import queue
import time
import json
import glob
import zipfile
import shutil
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# ---------- Configuration ----------
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
COMPETITORS_DIR = OUT / "competitors"
LLM_DIR = OUT / "llm_results"

# Pipeline commands
PIPELINE_CMD_WIN = "run_pipeline.bat"
PIPELINE_CMD_UNIX = "./run_pipeline.sh"

# ---------- Styling (kept your macOS ultra style) ----------
MACOS_ULTRA_STYLE = """<style>
/* (omitted here for brevity in the displayed doc) - copy the same CSS from your version above */
/* --- Use the same CSS you previously had --- */
</style>
"""
# For brevity in this message: use the CSS block you already provided.
# In practice, paste the CSS you had earlier (MACOS_ULTRA_STYLE) here.

st.set_page_config(
    page_title="Calyco — Premium Dashboard",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject CSS (use the CSS block you want)
# NOTE: replace with the full CSS string from your existing MACOS_ULTRA_STYLE variable
st.markdown(MACOS_ULTRA_STYLE, unsafe_allow_html=True)

# ---------- Utilities ----------
def safe_read_json(p: Path):
    """Robust JSON loader with defensive behavior."""
    try:
        text = p.read_text(encoding="utf-8")
        raw = json.loads(text)
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, list):
            # prefer single-dict lists
            if len(raw) == 0:
                return {}
            if len(raw) == 1 and isinstance(raw[0], dict):
                return raw[0]
            # otherwise return wrapper
            return {"list_value": raw}
        return {"value": raw}
    except Exception as e:
        return {"_error": str(e), "path": str(p)}

def list_files(folder: Path, pattern="*"):
    if not folder or not folder.exists():
        return []
    return sorted([Path(x) for x in glob.glob(str(folder / pattern))])

def human_count(n):
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)

def get_outputs_mtime(out_dir: Path):
    try:
        files = [p for p in out_dir.rglob('*') if p.is_file()]
        if not files:
            return 0
        return max(p.stat().st_mtime for p in files)
    except Exception:
        return 0

# ---------- Subprocess streaming ----------
def stream_subprocess(command, cwd=None, q=None):
    """Run subprocess and push lines into queue. Returns returncode."""
    # Use shell=True to accept simple command strings (run_pipeline.bat)
    p = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        universal_newlines=True,
        bufsize=1
    )
    try:
        # iterate lines as they appear
        for line in iter(p.stdout.readline, ""):
            if line is None:
                break
            if q is not None:
                q.put(line)
        p.wait()
    except Exception as e:
        if q is not None:
            q.put(f"ERROR: {e}\n")
    finally:
        if q is not None:
            q.put("__PIPELINE_DONE__")
        return p.returncode if p else -1

def start_pipeline_thread(run_cmd, cwd=None):
    q = queue.Queue()
    t = threading.Thread(target=stream_subprocess, args=(run_cmd, cwd, q), daemon=True)
    t.start()
    return q, t

# ---------- Session State ----------
if "pipeline_queue" not in st.session_state:
    st.session_state.pipeline_queue = None
    st.session_state.pipeline_running = False
    st.session_state.outputs_mtime = get_outputs_mtime(OUT)
    st.session_state.logs_text = ""
    st.session_state.pipeline_start_time = None

# Determine platform default
if os.name == "nt":
    DEFAULT_PIPELINE_CMD = PIPELINE_CMD_WIN
else:
    DEFAULT_PIPELINE_CMD = PIPELINE_CMD_UNIX

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:18px 0;'>
        <div style='font-size:56px; margin-bottom:12px;'>🎨</div>
        <div style='font-weight:800; font-size:20px;'>Calyco</div>
        <div style='color:gray; font-size:13px; margin-top:6px;'>Premium Analytics</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ▶️ Run Pipeline")
    st.markdown("Enable and run your content generation pipeline. Logs are streamed live here.")

    confirm_run = st.checkbox("Enable pipeline execution", value=False)
    run_cmd_input = st.text_input("Command", value=DEFAULT_PIPELINE_CMD)
    run_btn = st.button("▶️ Run Now", disabled=not confirm_run, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📦 Export bundle")
    if st.button("Create ZIP Bundle", use_container_width=True):
        zip_path = ROOT / "calyco_outputs_bundle.zip"
        if zip_path.exists():
            zip_path.unlink()
        files = []
        for folder, _, fs in os.walk(OUT):
            for f in fs:
                files.append(os.path.join(folder, f))
        if len(files) == 0:
            st.info("No files to bundle")
        else:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for full in files:
                    arc = os.path.relpath(full, ROOT)
                    zf.write(full, arc)
            with open(zip_path, "rb") as f:
                st.download_button(
                    "⬇️ Download ZIP",
                    data=f,
                    file_name="calyco_outputs_bundle.zip",
                    mime="application/zip",
                    use_container_width=True
                )

    st.markdown("---")
    st.markdown("### 🗑️ Clear outputs")
    st.warning("⚠️ Irreversible action")
    delete_confirm = st.text_input("Type DELETE to confirm", "", key="delete_confirm")
    if st.button("Clear All", use_container_width=True) and delete_confirm.strip().upper() == "DELETE":
        try:
            for child in OUT.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
            st.success("✅ Cleared!")
        except Exception as e:
            st.error(f"❌ {e}")

    st.markdown("---")
    st.markdown("### 📝 Notes")
    st.markdown("""
    <div style='font-size:13px; color:gray;'>
    • Remove <code>.env</code> before sharing<br>
    • Exclude <code>venv/</code> from archives<br>
    • Use manual mode for demos
    </div>
    """, unsafe_allow_html=True)
    st.caption("Built with ❤️ • v2.0 Premium")

# ---------- Launch pipeline ----------
if run_btn and confirm_run:
    if st.session_state.pipeline_running:
        st.warning("Pipeline already running")
    else:
        st.info("Starting pipeline...")
        st.session_state.pipeline_running = True
        st.session_state.logs_text = ""
        st.session_state.pipeline_start_time = time.time()
        q, t = start_pipeline_thread(run_cmd_input, cwd=str(ROOT))
        st.session_state.pipeline_queue = q

# ---------- Header ----------
st.markdown(f"""
<div class="macos-window" style="padding:28px;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div style="font-weight:800; font-size:44px; background:linear-gradient(135deg,#007AFF 0%,#5856D6 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">Calyco Analytics</div>
            <div style="color:gray; margin-top:6px;">Premium content & trends dashboard</div>
        </div>
        <div>
            <span style="display:inline-flex; align-items:center; gap:8px; padding:8px 14px; border-radius:16px; background:linear-gradient(135deg,#34C759,#30D158); color:white;">
                <span style="width:10px; height:10px; border-radius:50%; background:white; display:inline-block;"></span>
                Online
            </span>
        </div>
    </div>
    <div style="margin-top:12px; color:gray; font-size:13px;">
        {datetime.now().strftime('%B %d, %Y %H:%M')}
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- KPIs ----------
competitor_files = len(list_files(COMPETITORS_DIR, "*.json"))
llm_results = len(list_files(LLM_DIR, "*.txt"))
# Prefer expanded blog files if present
blog_files_all = list_files(OUT / "blog", "*.json")
# count expanded separately
expanded_blogs = [p for p in blog_files_all if p.name.endswith("_expanded.json")]
blogs_count = len(expanded_blogs) if expanded_blogs else len(blog_files_all)
mdx_count = len(list_files(OUT / "mdx", "*.mdx"))
images_count = len(list_files(OUT / "images", "*"))

if COMPETITORS_DIR.exists():
    for p in COMPETITORS_DIR.iterdir():
        if p.is_dir():
            images_count += len(list_files(p / "images", "*"))

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"<div class='kpi-card'><div class='kpi-icon icon-blue'>🏢</div><div class='kpi-value'>{human_count(competitor_files)}</div><div class='kpi-label'>Competitors</div></div>", unsafe_allow_html=True)
with k2:
    st.markdown(f"<div class='kpi-card'><div class='kpi-icon icon-purple'>🤖</div><div class='kpi-value'>{human_count(llm_results)}</div><div class='kpi-label'>AI Outputs</div></div>", unsafe_allow_html=True)
with k3:
    st.markdown(f"<div class='kpi-card'><div class='kpi-icon icon-green'>📝</div><div class='kpi-value'>{human_count(blogs_count)}</div><div class='kpi-label'>Articles</div></div>", unsafe_allow_html=True)
with k4:
    st.markdown(f"<div class='kpi-card'><div class='kpi-icon icon-orange'>🖼️</div><div class='kpi-value'>{human_count(images_count)}</div><div class='kpi-label'>Assets</div></div>", unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# ---------- Pipeline Logs ----------
log_col1, log_col2 = st.columns([3, 1])
with log_col1:
    st.markdown("<div class='macos-window'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📋 Pipeline Logs</div>", unsafe_allow_html=True)
    logs_placeholder = st.empty()
    progress_placeholder = st.empty()

    # Stream queued logs
    if st.session_state.pipeline_running and st.session_state.pipeline_queue:
        q = st.session_state.pipeline_queue
        new_lines = []
        # drain some lines (non-blocking)
        for _ in range(500):
            try:
                line = q.get_nowait()
            except queue.Empty:
                break
            else:
                if line == "__PIPELINE_DONE__":
                    st.session_state.pipeline_running = False
                    st.session_state.pipeline_queue = None
                    st.session_state.outputs_mtime = get_outputs_mtime(OUT)
                    st.session_state.logs_text += "\n\n✅ PIPELINE FINISHED\n"
                    progress_placeholder.progress(100)
                    logs_placeholder.code(st.session_state.logs_text[-30000:], language="text")
                    # short pause then rerun so UI reflects new outputs
                    time.sleep(0.6)
                    st.experimental_rerun()
                    break
                else:
                    new_lines.append(line)
        if new_lines:
            st.session_state.logs_text += "".join(new_lines)
        logs_placeholder.code(st.session_state.logs_text[-30000:], language="text")

        # progress heuristic
        elapsed = int(time.time() - st.session_state.get("pipeline_start_time", time.time()))
        p = min(95, elapsed * 3)
        progress_placeholder.progress(p)
        st.markdown("<div class='skeleton'></div>", unsafe_allow_html=True)
        st.markdown("<div class='skeleton' style='width:75%;'></div>", unsafe_allow_html=True)
    else:
        if st.session_state.logs_text:
            logs_placeholder.code(st.session_state.logs_text[-30000:], language="text")
        else:
            logs_placeholder.info("💡 No logs yet. Click 'Run Now' to start the pipeline.")
    st.markdown("</div>", unsafe_allow_html=True)

with log_col2:
    st.markdown("<div class='macos-window'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>⚡ Status</div>", unsafe_allow_html=True)
    if st.session_state.pipeline_running:
        st.markdown("<div style='padding:12px; background:rgba(52,199,89,0.08); border-radius:12px;'>🟢 Running</div>", unsafe_allow_html=True)
        st.write(f"Started: {datetime.fromtimestamp(st.session_state.pipeline_start_time).strftime('%H:%M:%S') if st.session_state.pipeline_start_time else '-'}")
    else:
        st.markdown("<div style='padding:12px; background:rgba(142,142,147,0.08); border-radius:12px;'>⚪ Idle</div>", unsafe_allow_html=True)
    if st.session_state.outputs_mtime:
        st.caption(f"Last update: {datetime.fromtimestamp(st.session_state.outputs_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ---------- Trends (Plotly) ----------
st.markdown("<div class='macos-window'>", unsafe_allow_html=True)
st.markdown("<div class='section-header'>📈 Market Trends</div>", unsafe_allow_html=True)

tfile = OUT / "trends.json"
if tfile.exists():
    t = safe_read_json(tfile)
    related = t.get("related", {}) or {}
    first_key = next(iter(related), None)
    if first_key:
        rel_list = related.get(first_key, [])[:20]
        try:
            df_rel = pd.DataFrame(rel_list)
            if not df_rel.empty and "query" in df_rel.columns and "value" in df_rel.columns:
                fig_rel = px.bar(df_rel.sort_values("value"), x="value", y="query", orientation="h",
                                 title=f"Top Related Queries for: {first_key}")
                fig_rel.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_rel, use_container_width=True)
        except Exception:
            pass
    interest = t.get("interest", [])
    if interest and isinstance(interest, list):
        try:
            df_interest = pd.DataFrame(interest)
            if 'date' in df_interest.columns:
                df_interest['date'] = pd.to_datetime(df_interest['date'], errors='coerce')
                metric_cols = [c for c in df_interest.columns if c not in ('date', 'isPartial')]
                if metric_cols:
                    fig_ts = px.line(df_interest, x='date', y=metric_cols[:1], title=f"Interest Over Time: {metric_cols[0]}")
                    fig_ts.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_ts, use_container_width=True)
        except Exception:
            pass
    with st.expander("📄 Raw Trends Preview"):
        st.json({k: (v if isinstance(v, (int, float, str)) else str(v)) for k, v in list(t.items())[:12]})
else:
    st.info("📊 No trends data. Run the trends scraper.")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ---------- Competitor Analysis ----------
st.markdown("<div class='macos-window'>", unsafe_allow_html=True)
st.markdown("<div class='section-header'>🏆 Competitor Analysis</div>", unsafe_allow_html=True)

comp_json_files = list_files(COMPETITORS_DIR, "*.json")
if comp_json_files:
    show_count = min(3, len(comp_json_files))
    tabs = st.tabs([f"🏢 Competitor {i+1}" for i in range(show_count)])
    for i in range(show_count):
        f = comp_json_files[i]
        with tabs[i]:
            j = safe_read_json(f)
            st.markdown(f"### {f.stem}")
            url = j.get("url") or j.get("website") or None
            if url:
                st.markdown(f"**🔗** [{url}]({url})")
            title = j.get("title")
            if title:
                st.markdown(f"**📌** {title}")
            snippet = j.get("snippet") or j.get("summary") or None
            if snippet:
                st.write(snippet[:800] + ("..." if len(snippet) > 800 else ""))
            # Prefer images inside a folder with the same base name
            candidate_dir = COMPETITORS_DIR / f.stem
            imgs = []
            if candidate_dir.exists() and candidate_dir.is_dir():
                imgs = list_files(candidate_dir / "images", "*")
            # fallback: search any images across competitors
            if not imgs:
                imgs_dirs = sorted([p for p in COMPETITORS_DIR.glob("**/images") if p.is_dir()])
                for d in imgs_dirs:
                    imgs += list_files(d, "*")[:6]
            if imgs:
                st.markdown("**🖼️ Assets**")
                cols = st.columns(min(4, len(imgs)))
                for idx, ip in enumerate(imgs[:8]):
                    try:
                        img = Image.open(ip)
                        with cols[idx % len(cols)]:
                            st.image(img, use_column_width=True, caption=ip.name)
                    except Exception:
                        cols[idx % len(cols)].write(f"📄 {ip.name}")
            else:
                st.info("No images downloaded for this competitor yet")
else:
    st.info("🔍 No competitor data yet")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ---------- AI Outputs ----------
st.markdown("<div class='macos-window'>", unsafe_allow_html=True)
st.markdown("<div class='section-header'>🤖 AI Generated Content</div>", unsafe_allow_html=True)

llm_files = list_files(LLM_DIR, "*.txt")
if llm_files:
    sel = st.selectbox("Select output:", llm_files, format_func=lambda p: p.name)
    if sel:
        txt = sel.read_text(encoding="utf-8")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.code(txt[:20000] + ("..." if len(txt) > 20000 else ""), language="text")
        with col2:
            st.metric("Size", f"{len(txt):,} chars")
            st.metric("Lines", f"{len(txt.splitlines()):,}")
            st.download_button("⬇️ Download", data=txt, file_name=sel.name, use_container_width=True)
else:
    st.info("🤖 No AI outputs yet")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ---------- Content Library (blogs & mdx) ----------
st.markdown("<div class='macos-window'>", unsafe_allow_html=True)
st.markdown("<div class='section-header'>📚 Content Library</div>", unsafe_allow_html=True)

bcol, mcol = st.columns(2)
with bcol:
    st.subheader("📝 Blogs")
    # prefer expanded versions
    blog_files = list_files(OUT / "blog", "*_expanded.json")
    if not blog_files:
        blog_files = list_files(OUT / "blog", "*.json")
    if blog_files:
        sel_blog = st.selectbox("Select:", blog_files, format_func=lambda p: p.name, key="blog_sel")
        j = safe_read_json(sel_blog)
        if "_error" not in j:
            # show word count
            body = j.get("body", "") or j.get("content", "") or ""
            words = len(body.split())
            st.markdown("**✨ Title**")
            st.info(j.get('meta_title', j.get('title', '-')))
            st.markdown("**📋 Description**")
            st.info(j.get('meta_description', '-'))
            st.markdown("**📖 Preview**")
            st.write(body[:4000] + ("..." if len(body) > 4000 else ""))
            st.markdown(f"**🧮 Word count:** {words:,}")
            # quick sanity check
            if words < 1100:
                st.warning("⚠️ Blog is shorter than required long-form 1200+ words (consider running expand_blog).")
            else:
                st.success("✅ Long-form length OK")
            st.download_button("⬇️ Download JSON", data=json.dumps(j, ensure_ascii=False, indent=2), file_name=sel_blog.name, use_container_width=True)
        else:
            st.error("❌ Error reading blog: " + str(j.get("_error")))
    else:
        st.info("No blog files yet")

with mcol:
    st.subheader("📄 MDX")
    mdx_files = list_files(OUT / "mdx", "*.mdx")
    if mdx_files:
        sel_mdx = st.selectbox("Select:", mdx_files, format_func=lambda p: p.name, key="mdx_sel")
        mdx_text = sel_mdx.read_text(encoding="utf-8")
        st.metric("Size", f"{len(mdx_text):,} chars")
        st.code(mdx_text[:3000] + ("..." if len(mdx_text) > 3000 else ""), language="markdown")
        st.download_button("⬇️ Download MDX", data=mdx_text, file_name=sel_mdx.name, use_container_width=True)
    else:
        st.info("No MDX files yet")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ---------- Social & Ads ----------
st.markdown("<div class='macos-window'>", unsafe_allow_html=True)
st.markdown("<div class='section-header'>📱 Social & Ads</div>", unsafe_allow_html=True)

csv_path = OUT / "social" / "social_posts.csv"
if csv_path.exists():
    try:
        df = pd.read_csv(csv_path)
        st.markdown("### 📱 Social Posts")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", len(df))
        col2.metric("Columns", len(df.columns))
        col3.metric("Size", f"{csv_path.stat().st_size / 1024:.1f} KB")
        st.dataframe(df.head(12), use_container_width=True)
        st.download_button("⬇️ Download CSV", data=csv_path.read_bytes(), file_name=csv_path.name, use_container_width=True)
    except Exception as e:
        st.error(f"Error reading social CSV: {e}")
else:
    st.info("No social posts yet")

ad_files = list_files(OUT / "ads", "*.csv")
if ad_files:
    st.markdown("### 📢 Ad Copy")
    for ad in ad_files:
        with st.expander(f"📢 {ad.name}"):
            try:
                dfad = pd.read_csv(ad)
                st.dataframe(dfad, use_container_width=True)
            except Exception:
                st.code(ad.read_text(encoding="utf-8")[:2000])
            st.download_button("⬇️ Download", data=ad.read_bytes(), file_name=ad.name, key=f"ad_{ad.name}")
else:
    st.info("No ads yet")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ---------- SEO & Validation ----------
st.markdown("<div class='macos-window'>", unsafe_allow_html=True)
st.markdown("<div class='section-header'>🔍 SEO & Validation</div>", unsafe_allow_html=True)

seo_files = list_files(OUT / "seo", "*.jsonld")
if seo_files:
    sel_seo = st.selectbox("Select JSON-LD:", seo_files, format_func=lambda p: p.name, key="seo_sel")
    st.code(sel_seo.read_text(encoding="utf-8"), language="json")
    st.download_button("⬇️ Download", data=sel_seo.read_text(encoding="utf-8"), file_name=sel_seo.name)
else:
    st.info("No JSON-LD yet")

val_path = OUT / "logs" / "validation_report.json"
if val_path.exists():
    vr = safe_read_json(val_path)
    st.markdown("### ✅ Validation Report")
    issues = vr.get("issues") or vr.get("errors") or []
    total_checks = vr.get("total_checks", 0)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div style='text-align:center; padding:12px;'><div style='font-size:28px; font-weight:700; color:#007AFF;'>{total_checks}</div><div style='color:gray;'>Total Checks</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='text-align:center; padding:12px;'><div style='font-size:28px; font-weight:700; color:#34C759;'>{total_checks - len(issues)}</div><div style='color:gray;'>Passed</div></div>", unsafe_allow_html=True)
    with col3:
        color = "#34C759" if len(issues) == 0 else "#FF9F0A"
        st.markdown(f"<div style='text-align:center; padding:12px;'><div style='font-size:28px; font-weight:700; color:{color};'>{len(issues)}</div><div style='color:gray;'>Issues</div></div>", unsafe_allow_html=True)
    if not issues:
        st.success("✅ All validation checks passed!")
    else:
        st.warning(f"⚠️ {len(issues)} issue(s) found")
        with st.expander("View Details"):
            for idx, issue in enumerate(issues, 1):
                st.markdown(f"**{idx}.** {issue}")
    with st.expander("📄 Full Report"):
        st.json(vr)
else:
    st.info("No validation report yet")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ---------- Footer ----------
st.markdown("""
<div style='text-align:center; padding:36px 20px; color:gray;'>
    <p style='font-size:15px; font-weight:500; margin-bottom:8px;'>Designed with ❤️ by Calyco Team</p>
    <p style='font-size:13px; color:lightgray;'>Premium Dashboard v2.0 • Remove <code>.env</code> before sharing</p>
</div>
""", unsafe_allow_html=True)

# ---------- Auto-refresh when outputs change ----------
cur_mtime = get_outputs_mtime(OUT)
if cur_mtime > st.session_state.outputs_mtime and not st.session_state.pipeline_running:
    st.session_state.outputs_mtime = cur_mtime
    # short wait to let files settle, then refresh
    time.sleep(0.4)
    st.experimental_rerun()



#streamlit run dashboard/app_premium.py