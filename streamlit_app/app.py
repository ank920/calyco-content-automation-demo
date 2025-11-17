"""
Calyco Content Pipeline Dashboard - Complete Edition v2.2
All outputs displayed with fixed deprecation warnings and proper data handling
"""

import streamlit as st
import json
import pandas as pd
import os
import glob
import zipfile
from io import BytesIO
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import subprocess
import time
import sys

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="Calyco Pipeline - Complete Outputs",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CUSTOM CSS =====
st.markdown("""
<style>
    .main-header {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #2563eb, #10b981, #f59e0b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: fadeIn 1.5s;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f2937;
        border-left: 4px solid #2563eb;
        padding-left: 1rem;
        margin: 2rem 0 1rem 0;
    }
    .data-card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .insight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    .info-card {
        background: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# ===== UTILITIES =====
def safe_read_json(filepath, default=None):
    """Safely read JSON with type checking"""
    try:
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if default is not None:
                    if isinstance(default, list) and not isinstance(data, list):
                        return default
                    if isinstance(default, dict) and not isinstance(data, dict):
                        return default
                return data
    except Exception as e:
        st.warning(f"⚠️ {os.path.basename(filepath)}: {str(e)}")
    return default if default is not None else {}

def safe_read_csv(filepath):
    """Safely read CSV with multiple encodings"""
    try:
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding, on_bad_lines='skip')
                    df = df.dropna(how='all', axis=1)
                    return df
                except:
                    continue
    except Exception as e:
        st.error(f"❌ {os.path.basename(filepath)}: {str(e)}")
    return pd.DataFrame()

def count_files(folder):
    """Count all files recursively"""
    if not os.path.exists(folder):
        return 0
    return sum(1 for _ in Path(folder).rglob('*') if _.is_file())

def get_all_images(folder):
    """Get all images from folder recursively"""
    images = []
    if os.path.exists(folder):
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.gif']:
            images.extend(glob.glob(f"{folder}/**/{ext}", recursive=True))
    return images

# ===== HEADER =====
st.markdown('<div class="main-header">🎨 Calyco Pipeline - Complete Outputs</div>', unsafe_allow_html=True)
st.caption("Comprehensive visualization of all generated content, images, and data")

# ===== CONTROLS =====
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🚀 Run Pipeline", use_container_width=True, type="primary"):
        with st.spinner("Running pipeline... (2-4 minutes)"):
            try:
                if not os.path.exists("run_pipeline.py"):
                    st.error("❌ run_pipeline.py not found")
                else:
                    result = subprocess.run(
                        [sys.executable, "run_pipeline.py"], 
                        capture_output=True, 
                        text=True, 
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        st.success("✅ Pipeline completed!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Pipeline failed!")
                        with st.expander("🔍 Error Details"):
                            st.code(result.stderr, language="text")
            except Exception as e:
                st.error(f"❌ {str(e)}")

with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

with col3:
    if st.button("📥 Download All", use_container_width=True):
        try:
            buf = BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk("outputs"):
                    for file in files:
                        filepath = os.path.join(root, file)
                        zf.write(filepath, os.path.relpath(filepath, "outputs"))
            
            st.download_button(
                "💾 Download ZIP", 
                buf.getvalue(), 
                f"calyco_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip"
            )
        except Exception as e:
            st.error(f"❌ {str(e)}")

with col4:
    if st.button("🎉 Celebrate", use_container_width=True):
        st.balloons()
        st.toast("🎊 Great work!", icon="🎉")

st.divider()

# ===== 1. CONTEXT.JSON =====
st.markdown('<div class="section-header">📋 Context & Pipeline Info</div>', unsafe_allow_html=True)

context = safe_read_json("outputs/context.json", default={})
if context:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        built_at = context.get('built_at', 'N/A')
        st.metric("Built At", built_at[:10] if built_at != 'N/A' else 'N/A')
    with col2:
        st.metric("Competitors", len(context.get('competitors', [])))
    with col3:
        trends_data = context.get('trends', {})
        if isinstance(trends_data, dict):
            st.metric("Keywords", len(trends_data.get('keywords', [])))
    with col4:
        st.metric("Total Files", count_files("outputs"))
    
    with st.expander("📄 Full Context JSON"):
        st.json(context)
else:
    st.warning("⚠️ No context.json. Run pipeline first.")

st.divider()

# ===== 2. TRENDS.JSON =====
st.markdown('<div class="section-header">📈 Trends Data</div>', unsafe_allow_html=True)

trends = safe_read_json("outputs/trends.json", default={})
if trends and isinstance(trends, dict):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Keywords Tracked")
        keywords = trends.get('keywords', [])
        if keywords:
            for kw in keywords:
                st.info(f"🔑 {kw}")
        
        st.subheader("Fetched At")
        st.caption(trends.get('fetched_at', 'N/A'))
    
    with col2:
        st.subheader("Data Summary")
        st.json({
            "keywords": len(keywords),
            "interest_records": len(trends.get('interest', [])),
            "related_queries": sum([len(v) for v in trends.get('related', {}).values()])
        })
    
    if 'interest' in trends and trends['interest']:
        st.subheader("📊 Interest Over Time")
        df_trends = pd.DataFrame(trends['interest'])
        if not df_trends.empty and keywords:
            fig = px.line(
                df_trends, 
                x='date', 
                y=[k for k in keywords if k in df_trends.columns], 
                markers=True, 
                title="Keyword Interest Trends"
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_trends, use_container_width=True)
    
    if 'related' in trends:
        st.subheader("🔎 Related Queries")
        for keyword in keywords:
            if keyword in trends['related'] and trends['related'][keyword]:
                with st.expander(f"Related: {keyword}"):
                    df_rel = pd.DataFrame(trends['related'][keyword])
                    if not df_rel.empty:
                        fig = px.bar(df_rel.head(10), x='value', y='query', orientation='h')
                        st.plotly_chart(fig, use_container_width=True)
                        st.dataframe(df_rel, use_container_width=True)
else:
    st.info("📊 No trends data.")

st.divider()

# ===== 3. BLOG DATA =====
st.markdown('<div class="section-header">📝 Blog Content</div>', unsafe_allow_html=True)

blog_files = glob.glob("outputs/blog/*.json")
st.metric("Total Blogs", len(blog_files))

if blog_files:
    for blog_file in blog_files:
        blog = safe_read_json(blog_file, default={})
        if blog:
            with st.expander(f"📄 {os.path.basename(blog_file)}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### {blog.get('meta_title', 'Untitled')}")
                    st.caption(f"📅 {blog.get('generated_at', 'N/A')}")
                    st.markdown(f"**Meta:** {blog.get('meta_description', 'N/A')}")
                
                with col2:
                    st.download_button(
                        "💾 Download", 
                        json.dumps(blog, indent=2), 
                        file_name=os.path.basename(blog_file), 
                        key=f"blog_{blog_file}"
                    )
                
                st.markdown("---")
                body = blog.get('body', '*No content*')
                if len(body) > 5000:
                    st.markdown(body[:5000] + "\n\n*[Truncated]*", unsafe_allow_html=True)
                else:
                    st.markdown(body, unsafe_allow_html=True)
else:
    st.info("📝 No blogs found.")

st.divider()

# ===== 4. COMPETITOR IMAGES =====
st.markdown('<div class="section-header">🏆 Competitor Intelligence</div>', unsafe_allow_html=True)

all_comps = [d for d in glob.glob("outputs/competitors/*") if os.path.isdir(d)]

if all_comps:
    for comp_dir in all_comps:
        comp_name = os.path.basename(comp_dir).replace('_', ' ')
        images = get_all_images(f"{comp_dir}/images")
        
        with st.expander(f"🏢 {comp_name} ({len(images)} images)"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                json_files = glob.glob(f"{comp_dir}/*.json")
                if json_files:
                    comp_data = safe_read_json(json_files[0], default={})
                    if comp_data:
                        url = comp_data.get('url', '#')
                        st.markdown(f"**URL:** [{url}]({url})")
                        st.markdown(f"**Title:** {comp_data.get('title', 'N/A')}")
                        
                        snippet = comp_data.get('snippet', 'N/A')
                        if len(snippet) > 200:
                            snippet = snippet[:200] + "..."
                        st.markdown(f"**Info:** {snippet}")
            
            with col2:
                st.metric("Images", len(images))
            
            if images:
                st.markdown("**📸 Gallery:**")
                cols = st.columns(4)
                for idx, img in enumerate(images[:20]):
                    with cols[idx % 4]:
                        try:
                            st.image(img, use_container_width=True, caption=f"#{idx+1}")
                        except:
                            st.caption("⚠️ Load error")
                
                if len(images) > 20:
                    st.info(f"➕ {len(images) - 20} more images")
else:
    st.info("🏢 No competitor data.")

st.divider()

# ===== 5. GENERATED IMAGES =====
st.markdown('<div class="section-header">🖼️ Generated Images</div>', unsafe_allow_html=True)

gen_images = glob.glob("outputs/images/*")
st.metric("Total Images", len(gen_images))

if gen_images:
    cols = st.columns(4)
    for idx, img in enumerate(gen_images):
        with cols[idx % 4]:
            try:
                st.image(img, caption=os.path.basename(img), use_container_width=True)
            except:
                st.caption(f"⚠️ {os.path.basename(img)}")
else:
    st.info("🖼️ No generated images.")

st.divider()

# ===== 6. LLM RESULTS =====
st.markdown('<div class="section-header">🧠 LLM Raw Outputs</div>', unsafe_allow_html=True)

llm_files = glob.glob("outputs/llm_results/*.txt")
st.metric("Total LLM Files", len(llm_files))

if llm_files:
    for llm_file in llm_files:
        try:
            with open(llm_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            size = os.path.getsize(llm_file) / 1024
            
            with st.expander(f"🧠 {os.path.basename(llm_file)} ({size:.1f} KB)"):
                col1, col2 = st.columns([4, 1])
                with col2:
                    st.download_button(
                        "💾", 
                        content, 
                        file_name=os.path.basename(llm_file), 
                        key=f"llm_{llm_file}"
                    )
                
                st.text_area("Content:", content, height=400, key=f"txt_{llm_file}")
        except Exception as e:
            st.error(f"❌ {os.path.basename(llm_file)}: {str(e)}")
else:
    st.info("🧠 No LLM outputs.")

st.divider()

# ===== 7. LOGS & VALIDATION (FIXED - NO WHITE SPACES) =====
st.markdown('<div class="section-header">📋 Pipeline Logs & Quality Control</div>', unsafe_allow_html=True)

# Run Summary (Enhanced)
st.subheader("📊 Pipeline Execution Summary")
run_summary_path = "outputs/logs/run_summary.json"

if os.path.exists(run_summary_path):
    run_summary = safe_read_json(run_summary_path, default=None)
    
    if run_summary:
        # Extract and display key information
        if isinstance(run_summary, dict):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                start_time = run_summary.get('start_time', run_summary.get('timestamp', 'N/A'))
                if start_time != 'N/A' and len(start_time) > 10:
                    start_time = start_time[:10]
                st.metric("🕐 Started", start_time)
            
            with col2:
                duration = run_summary.get('duration', run_summary.get('duration_seconds', 'N/A'))
                if isinstance(duration, (int, float)):
                    duration_str = f"{duration:.1f}s"
                else:
                    duration_str = str(duration)
                st.metric("⏱️ Duration", duration_str)
            
            with col3:
                status = run_summary.get('status', 'completed')
                st.metric("✅ Status", status.title())
            
            with col4:
                files_created = run_summary.get('files_created', run_summary.get('total_files', count_files("outputs")))
                st.metric("📁 Files", files_created)
            
            # Show detailed breakdown
            with st.expander("🔍 View Full Run Summary"):
                st.json(run_summary)
        
        elif isinstance(run_summary, list):
            if len(run_summary) > 0:
                st.info(f"📊 Found {len(run_summary)} pipeline run(s) recorded")
                for idx, run in enumerate(run_summary, 1):
                    with st.expander(f"Run #{idx}"):
                        st.json(run)
            else:
                st.info("📊 Run summary is empty. Pipeline will populate this after execution.")
        else:
            # Handle unexpected format gracefully
            st.info("📊 Run summary exists with custom format")
            with st.expander("🔍 View Data"):
                st.json(run_summary)
    else:
        st.info("📊 Run summary file is empty. It will be populated after pipeline execution.")
else:
    st.info("📊 No run summary yet. The file will be created automatically when you run the pipeline.")

st.divider()

# Validation Report (Enhanced with NO ugly warnings)
st.subheader("✅ Content Quality & Brand Compliance")
validation_path = "outputs/logs/validation_report.json"

if os.path.exists(validation_path):
    validation = safe_read_json(validation_path, default=None)
    
    if validation and isinstance(validation, list) and len(validation) > 0:
        # Calculate metrics
        total = len(validation)
        passed = sum(1 for v in validation if isinstance(v, dict) and not v.get('forbidden', []))
        failed = total - passed
        score = (passed / total * 100) if total > 0 else 0
        
        # Visual quality score
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Quality Score", f"{score:.1f}%")
        with col2:
            st.metric("✅ Passed", passed)
        with col3:
            st.metric("⚠️ Issues", failed)
        with col4:
            st.metric("📁 Total", total)
        
        # Status message
        if score == 100:
            st.success("🎉 Perfect! All content meets brand standards.")
        elif score >= 80:
            st.info(f"💡 Good quality - {failed} file(s) need minor adjustments.")
        else:
            st.warning(f"⚠️ {failed} file(s) require review.")
        
        # Visual breakdown
        fig = go.Figure(data=[
            go.Pie(
                labels=['Passed', 'Issues'],
                values=[passed, failed],
                hole=.4,
                marker_colors=['#10b981', '#f59e0b']
            )
        ])
        fig.update_layout(title="Validation Status", showlegend=True, height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed issues
        issues = [v for v in validation if isinstance(v, dict) and v.get('forbidden', [])]
        
        if issues:
            st.markdown("**🔍 Files with Issues:**")
            for idx, issue in enumerate(issues, 1):
                with st.expander(f"📄 {issue.get('file', 'Unknown')}"):
                    forbidden = issue.get('forbidden', [])
                    if forbidden:
                        st.markdown("**Forbidden terms:**")
                        for term in forbidden:
                            st.code(term)
        
        # Full data
        with st.expander("🔍 View Complete Report"):
            st.json(validation)
    
    elif validation and isinstance(validation, list) and len(validation) == 0:
        st.info("📋 Validation report is empty. No files have been validated yet.")
    
    elif validation and not isinstance(validation, list):
        # FIXED: Handle unexpected format without ugly warning
        st.info(f"📋 Validation data exists (format: {type(validation).__name__})")
        with st.expander("🔍 View Data"):
            st.json(validation)
    else:
        st.info("📋 Validation report is empty.")
else:
    st.info("✅ No validation report yet. It will be created after pipeline execution.")

st.divider()

# ===== 8. PROMPTS =====
st.markdown('<div class="section-header">📝 AI Prompts</div>', unsafe_allow_html=True)

prompt_files = glob.glob("outputs/prompts/*.txt")

if prompt_files:
    st.metric("Total Prompts", len(prompt_files))
    tabs = st.tabs([os.path.basename(f) for f in prompt_files])
    
    for tab, prompt_file in zip(tabs, prompt_files):
        with tab:
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                col1, col2 = st.columns([4, 1])
                with col2:
                    st.download_button(
                        "💾 Download", 
                        content, 
                        file_name=os.path.basename(prompt_file), 
                        key=f"prompt_{prompt_file}"
                    )
                
                st.text_area("Content:", content, height=400, key=f"pmt_{prompt_file}")
            except Exception as e:
                st.error(f"❌ {str(e)}")
else:
    st.info("📝 No AI prompts found. They will be generated during pipeline execution.")

st.divider()

# ===== 9. SOCIAL MEDIA (FIXED - NO WHITE SPACES) =====
st.markdown('<div class="section-header">📱 Social Media Content Strategy</div>', unsafe_allow_html=True)

# Social Posts CSV (Enhanced)
st.subheader("📊 Social Media Calendar")
social_csv = "outputs/social/social_posts.csv"

if os.path.exists(social_csv):
    df_social = safe_read_csv(social_csv)
    
    if not df_social.empty:
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📱 Posts", len(df_social))
        
        with col2:
            if 'platform' in df_social.columns:
                st.metric("🌐 Platforms", df_social['platform'].nunique())
        
        with col3:
            if 'post_type' in df_social.columns:
                st.metric("📋 Types", df_social['post_type'].nunique())
        
        with col4:
            if 'date' in df_social.columns:
                st.metric("📅 Scheduled", "Yes")
        
        # Platform filtering
        if 'platform' in df_social.columns:
            platforms = ['All'] + sorted(df_social['platform'].dropna().unique().tolist())
            selected = st.selectbox("Filter Platform:", platforms)
            
            filtered = df_social if selected == 'All' else df_social[df_social['platform'] == selected]
            
            # Chart
            platform_counts = df_social['platform'].value_counts()
            
            fig = go.Figure(data=[
                go.Bar(
                    x=platform_counts.index,
                    y=platform_counts.values,
                    text=platform_counts.values,
                    textposition='auto',
                    marker_color=['#E4405F', '#1DA1F2', '#0A66C2', '#25D366'][:len(platform_counts)]
                )
            ])
            fig.update_layout(
                title="Posts by Platform",
                xaxis_title="Platform",
                yaxis_title="Posts",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            filtered = df_social
        
        # Data table
        st.dataframe(filtered, use_container_width=True, height=400)
        
        # Download
        st.download_button(
            "📥 Download CSV",
            filtered.to_csv(index=False),
            file_name=f"social_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("📱 Social posts CSV exists but is empty. Run pipeline to generate content.")
else:
    st.info("📱 No social media calendar yet. It will be created after pipeline execution.")

st.divider()

# Social Index JSON (Enhanced - NO WHITE SPACE)
st.subheader("📋 Social Data Index")
social_index_path = "outputs/social/social_index.json"

if os.path.exists(social_index_path):
    social_index = safe_read_json(social_index_path, default=None)
    
    if social_index:
        # Display structure info
        if isinstance(social_index, list):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📊 Entries", len(social_index))
            with col2:
                if len(social_index) > 0 and isinstance(social_index[0], dict):
                    st.metric("🔑 Fields", len(social_index[0].keys()))
            
            # Show sample
            with st.expander("🔍 View Index Data"):
                if len(social_index) > 0:
                    st.json(social_index[0])
                    if len(social_index) > 1:
                        st.caption(f"...and {len(social_index) - 1} more entries")
        
        elif isinstance(social_index, dict):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🔑 Keys", len(social_index.keys()))
            with col2:
                total = sum(len(v) if isinstance(v, list) else 1 for v in social_index.values())
                st.metric("📊 Items", total)
            
            with st.expander("🔍 View Data"):
                st.json(social_index)
        else:
            st.info(f"📋 Social index exists (format: {type(social_index).__name__})")
            with st.expander("🔍 View Data"):
                st.json(social_index)
    else:
        st.info("📋 Social index file is empty. Run pipeline to populate.")
else:
    st.info("📋 No social index yet. It will be created during pipeline execution.")

# ===== FOOTER =====
st.divider()
st.markdown(f"""
<div style='text-align: center; color: #6b7280; padding: 2rem 0;'>
    <p><strong>🎨 Calyco Pipeline Dashboard v2.3</strong></p>
    <p>Last refreshed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")}</p>
</div>
""", unsafe_allow_html=True)


#streamlit run streamlit_app/app.py
