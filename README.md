
# CALYCO — 48–72 hr Demo Task  
### Automated Content & Image Generation Pipeline (Integration-Ready)

This project implements the full end-to-end demo pipeline requested in the CALYCO 48–72 hr assignment.  
It includes data scraping, trend extraction, competitor analysis, AI text generation, automated image prompt creation, (optional) DALL·E 3 image generation, SEO artifacts, and a Streamlit-based viewer.

The system is fully automated and **image-generation integration-ready** — meaning:

- If an OpenAI API key is present → real DALL·E 3 images are generated.  
- If no API key is present → black placeholders are created so the demo always runs cleanly.  

Designed to demonstrate real-world content operations automation.

---

# 📁 Project Structure

```

calyco-demo/
│
├── pipeline/
│   ├── scrapers/                 # Google Trends, Competitor sites, Social, News
│   ├── process_data.py           # Clean + combine scraped data
│   ├── generate_content.py       # LLM content generation + postprocess
│   ├── generate_prompts_via_groq_auto.py  # Builds AI & image prompts
│   ├── image_generator.py        # DALL·E 3 integration + fallback placeholder logic
│   ├── utils/                    # Validation, helpers
│   └── schemas/                  # Blog, SEO, Social, Ads schemas
│
├── prompts/
│   └── image_prompts.yaml        # Hero / product / social templates
│
├── outputs/
│   ├── trends/                   # Google Trends output
│   ├── competitors/              # Competitor snippets
│   ├── social/                   # Social CSV
│   ├── ads/                      # Ad CSV
│   ├── blog/                     # Blog JSON files (with image prompts & paths)
│   ├── mdx/                      # Product MDX pages
│   ├── seo/                      # JSON-LD schema for latest blog
│   └── llm_results/              # Raw LLM generation
│
├── images/
│   ├── *.png                     # Auto-generated images (real or placeholder)
│   └── metadata.json             # Log of all prompt → image generations
│
├── dashboard/
│   └── app_premium.py            # Streamlit viewer
│
├── scripts/
│   ├── print_latest_image_prompts.py
│   ├── regenerate_images_from_latest_blog.py
│   └── test_image_gen.py
│
├── run_pipeline.py               # One-click pipeline runner
├── requirements.txt
└── README.md

````

---

# ⚙️ Setup Instructions

## 1. Create Virtual Environment
Windows:
```powershell
python -m venv venv
venv\Scripts\activate
````

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 2. Install Dependencies

```
pip install -r requirements.txt
```

---

## 3. Environment Variables

Create a `.env` file in repo root:

```
# GROQ key for text generation
GROQ_API_KEY=

# Optional: DALL·E 3 image generation
OPENAI_API_KEY=

# Choose: "manual" or "api"
CONTENT_MODE=api
CONTENT_PROVIDER=groq
```

### 🔥 Behavior:

* **If `OPENAI_API_KEY` is present → real DALL·E images**
* **If missing → black placeholder images**

This matches CALYCO requirement:

> “Use DALL·E 3 and keep integration ready. If key missing, show placeholder.”

---

# 🚀 Running the Pipeline

## A) Manual Mode (Default)

Outputs prompts → you paste → pipeline processes them.

```bash
python pipeline/generate_content.py postprocess
```

This:

* Loads context
* Builds prompts (blog, mdx, ads, social)
* Generates image prompts
* Generates images or placeholders
* Writes blog.json, mdx, ads CSV, social CSV
* Writes SEO json-ld

---

## B) Automatic Mode (Recommended)

In `.env`:

```
CONTENT_MODE=api
```

Then run:

```bash
python run_pipeline.py
```

Pipeline will:

1. Load context
2. Call GROQ to generate all text
3. Call DALL·E 3 (if key exists)
4. Save all outputs
5. Produce placeholders otherwise

---

# 🖼️ Image Generation (Hero + Support Images)

### Image Prompt Generation

Prompts are created from:

* Blog title
* Tags
* Color family
* Trend keywords
* Brand rules
* Templates (`prompts/image_prompts.yaml`)

Auto-generated fields appear in blog JSON:

```
image_prompt_hero
image_prompt_support1
image_prompt_support2
```

### Image Saving Behavior

`pipeline/image_generator.py`:

* If API key exists → calls OpenAI → saves real PNG
* If not → saves solid black placeholder PNG

All operations logged in:

```
images/metadata.json
```

### Example Metadata Entry:

```json
{
  "file": "Hero-image-for-Pastel-Trends-fe90e921.png",
  "prompt": "Hero image for 'Pastel Trends 2026'...",
  "size": "1024x1792",
  "mode": "placeholder",
  "ts": "2025-11-17T07:41:00Z"
}
```

---

# 📊 Displaying Outputs (Frontend)

Run:

```bash
streamlit run dashboard/app_premium.py
```

UI includes:

* Blog viewer
* MDX product page viewer
* Social posts
* Ads
* Images gallery
* Raw prompt inspector

Automatically reads:

```
outputs/blog/
outputs/social/social_posts.csv
images/
```

---

# 🧠 Architecture Summary

### Data Flow Diagram (Simplified)

```
Scrapers
   │
   └──> outputs/raw/ & context.json
               │
               ▼
     generate_content.py (Manual/API)
               │
      ┌────────┴──────────┐
      ▼                   ▼
 Text Generation     Image Prompt Builder
      │                   │
      ▼                   ▼
  blog.json        make_image_prompt()
                      │
                      ▼
             generate_image()
         (Real or Placeholder)
                      │
                      ▼
                images/*.png
                      │
                      ▼
                Streamlit UI
```

---

# 🛠️ Troubleshooting

### Pipeline cannot find `pipeline` package

Run scripts from repo root.

### Images not generating

Check:

* No OpenAI key → placeholders
* Invalid OpenAI key → error_fallback in metadata.json

### Frontend not showing images

Ensure `image_path_hero` in blog JSON matches actual file in `images/`.

---

# 🎥 How to Demo (Suggested Flow)

1. **Run pipeline**

```
python pipeline/generate_content.py postprocess
```

2. **Open latest blog JSON**

* Show generated text
* Show image prompts
* Show image paths

3. **Show images folder**

* Placeholder images
* metadata.json entries

4. **Run Streamlit**

```
streamlit run dashboard/app_premium.py
```

5. **Explain DALL·E toggle**

* No key → placeholders
* Add key → real images

6. **Wrap up**
   Show end-to-end automation.

---

# 📦 Final Notes

* `.env` is purposely excluded for security
* Integration with real APIs is opt-in (no accidental billing)
* Pipeline is stable even with missing API keys
* Clean outputs & standardized schema for every content type
* Ready for deployment or further extension

---

# 🙌 Author

Assignment by: **Ankit Verma**
Tech stack: Python, GROQ API, DALL·E 3, Streamlit, Selenium/PyTrends, YAML, JSON-LD

