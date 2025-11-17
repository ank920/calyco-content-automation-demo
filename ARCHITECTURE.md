
# CALYCO Demo – System Architecture  
### 48–72 hr Assignment — Automated Content & Image Generation Pipeline

This document explains the **system design, data flow, components, and architecture** of the CALYCO demo project.  
The pipeline is built for end-to-end automation: scraping → trend processing → LLM content creation → image prompt generation → image generation (real or placeholder) → UI display.

---

# 🌐 High-Level Overview

The demo consists of three major layers:

1. **Data Layer (Scrapers + Context Builder)**  
2. **Intelligence Layer (LLM text + image prompt + image generation)**  
3. **Presentation Layer (Streamlit UI + Output Files)**

The system is built to handle missing API keys gracefully and still produce a complete demo.

---

# 1. **Data Layer (Scrapers & Processing)**

### Components:
- `scrapers/google_trends.py`
- `scrapers/competitors.py`
- `scrapers/social.py`
- `scrapers/industry_news.py`
- `pipeline/process_data.py`

### Responsibilities:
- Collect real-world signals (Google Trends, competitor pages, social samples, headlines)
- Clean & normalize raw scraped data
- Convert everything into **context.json**:
```

outputs/context.json

````
- This context is used by LLM generators and image prompt builder

### Process Summary:
1. Scrapers run individually or via the pipeline  
2. Each scraper outputs structured JSON/CSV  
3. `process_data.py` merges data → produces `context.json`  
4. Passed into `generate_content.py`

### Why this matters:  
The automation layer builds content based on **live signals**, not static inputs.

---

# 2. **Intelligence Layer (LLM + Prompts + Images)**

This is the core of the assignment.

### Key Components:
- `pipeline/generate_content.py`  
- `pipeline/generate_prompts_via_groq_auto.py`  
- `pipeline/image_generator.py`

### Functions:
1. **Text Content Generation**  
 - Blog (SEO long-form)  
 - Product MDX page  
 - Social posts CSV  
 - Ads CSV  
 - Structured metadata  
 - JSON-LD SEO schema  
 - All validated via schema files

2. **Automatic Image Prompt Generation**  
 - Using:
   - blog title  
   - body content  
   - trend keywords  
   - tags / color families  
   - competitor hints  
   - prompt templates

3. **Image Generation (Integration-Ready)**  
 - Uses `pipeline/image_generator.py`
 - Behavior:
   ```
   If OPENAI_API_KEY exists → Generate real DALL·E 3 images
   If missing → Generate black placeholder images
   ```
 - Always returns a valid PNG, never breaks pipeline
 - Saves full metadata in:
   ```
   images/metadata.json
   ```

4. **Caching & Filename Strategy**  
 - Images stored in:
   ```
   images/<slug>-<hash>-<size>.png
   ```
 - Ensures:
   - No repeated billing  
   - Same prompt always produces same filename  
   - Idempotent runs

### Why this matters:  
Manish asked for:
> “Use DALL·E 3 for images and keep the integration ready. If key not present, still produce output.”

This layer fully delivers that requirement.

---

# 3. **Presentation Layer (UI & Outputs)**

### Components:
- `dashboard/app_premium.py`
- `/outputs/` folder structure
- `/images/` folder

### Responsibilities:
- Display:
- Blogs  
- Product MDX  
- Social CSV  
- Ads CSV  
- SEO JSON-LD  
- Generated images (real or placeholder)

### Streamlit UI Features:
- Clean viewer for all content  
- Image gallery showing final generated assets  
- Clicking an item displays:
- Final image  
- Prompt used  
- JSON metadata  
- Designed to be smooth for demo reviewers

---

# 📁 Directory-Level Architecture

````

pipeline/
scrapers/            # Data collection
process_data.py      # Merging + cleaning
generate_content.py  # LLM content generation
generate_prompts_via_groq_auto.py  # AI & image prompts
image_generator.py   # Real or placeholder images
schemas/             # Validation JSON schemas
utils/               # Validation helpers

prompts/
image_prompts.yaml   # Templates for hero/product/social images

outputs/
blog/                # Blog JSON with image_path fields
mdx/                 # Product pages
social/              # Social CSV
ads/                 # Ads CSV
seo/                 # JSON-LD
llm_results/         # Raw results

images/
*.png                # Auto-generated images
metadata.json        # Prompt + status log

dashboard/
app_premium.py       # Streamlit frontend

scripts/
print_latest_image_prompts.py
regenerate_images_from_latest_blog.py
test_image_gen.py

````

---

# 🔄 Pipeline Data Flow (Mermaid Diagram)

## A) End-to-End Flow

```mermaid
flowchart TD

A[Scrapers\n(Google Trends, Competitors, Social, News)] --> B[process_data.py]
B --> C[context.json]

C --> D[generate_content.py<br>(Manual/API Mode)]

D --> E1[Blog Generator]
D --> E2[MDX Product Page]
D --> E3[Social CSV]
D --> E4[Ads CSV]

E1 --> F1[make_image_prompt()]
E2 --> F1
E3 --> F1
F1 --> F2[generate_image()\n(DALL·E / Placeholder)]

F2 --> G[images/*.png]
F2 --> H[images/metadata.json]

E1 --> I[outputs/blog/*.json]
E2 --> J[outputs/mdx/*.mdx]
E3 --> K[outputs/social/social_posts.csv]
E4 --> L[outputs/ads/*.csv]
I --> M[SEO JSON-LD]

I --> N[Streamlit UI]
J --> N
K --> N
L --> N
G --> N
````

---

## B) Image Generation Internal Flow

```mermaid
flowchart LR

A[make_image_prompt()] --> B[generate_image()]
B -->|Has OPENAI_KEY| C[Call DALL·E 3 API\nReturn PNG]
B -->|No key / Error| D[Generate Black Placeholder PNG]

C --> E[Write PNG → /images]
D --> E

E --> F[Append metadata.json]
```

---

# 🧩 Key Architectural Features

### ✔ Modular

Each part (scrapers → processing → LLM → images → UI) is separate.

### ✔ Fault-tolerant

* No API key? → Still produces complete output
* DALL·E error? → Still displays something
* LLM error? → Saved in `/outputs/llm_results/`

### ✔ Idempotent

Running pipeline multiple times will not duplicate or break data.

### ✔ Caching

* Same prompt → same filename
* Prevents duplicate OpenAI billing
* Great for demos + production

### ✔ Extendable

* Add more content types
* Add more scrapers
* Swap image model
* Swap LLM provider
* Deploy pipeline to Airflow, Prefect, or CRON easily

---

# 🛡️ Error Handling Strategy

### In `generate_image()`:

* try → call API
* except → write placeholder
* always → append metadata

### In content generation:

* All API failures logged to:

  ```
  outputs/logs/
  ```

### In UI:

* Missing image → fallback shown automatically
* Corrupted JSON → validation warns

---

# 🔑 Technology Stack

| Layer     | Tool                            |
| --------- | ------------------------------- |
| Scraping  | Selenium, PyTrends, Requests    |
| LLM Text  | GROQ Llama 3.1 / API            |
| Image Gen | DALL·E 3 (OpenAI) / Placeholder |
| Framework | Python                          |
| Frontend  | Streamlit                       |
| Formats   | JSON, CSV, MDX, JSON-LD         |

---

# 📦 Conclusion

This architecture demonstrates a **production-style automation pipeline** within 48–72 hours:

* Robust
* Clean
* Fully automated
* Fault-tolerant
* Integration-ready for DALL·E 3
* Demo-friendly UI
* Easy to extend

It meets all requirements of the assignment and is packaged in a clear, professional format for review.

