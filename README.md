# ETL Django — OCR Document-to-Data Pipeline (Academic Project)

> A Django web platform whose core is an **OCR-based ETL pipeline**: it **extracts** text from car-insurance document images with a multi-engine OCR stack (OpenCV + Tesseract / EasyOCR / ArabicOCR), **transforms** it (deskew, reading-order reconstruction, neural auto-correction), and **loads** the result as structured JSON + relational records — wrapped in a multilingual NLU chatbot, DRF JSON APIs, and Chart.js / Bokeh analytics dashboards.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Django REST Framework](https://img.shields.io/badge/DRF-A30000?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![Tesseract](https://img.shields.io/badge/Tesseract%20OCR-4285F4?style=for-the-badge&logo=google&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)
![Keras](https://img.shields.io/badge/Keras-D00000?style=for-the-badge&logo=keras&logoColor=white)
![NLTK](https://img.shields.io/badge/NLTK-154F5B?style=for-the-badge&logo=python&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)

---

## Overview

This is an academic Django project that turns **document images into structured data** and serves that data through a full web application. The modelled domain is a small car-insurance platform, but the engineering centre of gravity is the **ETL (Extract → Transform → Load)** layer: registration cards, contracts, and invoices (scanned/photographed) are pushed through an OpenCV + OCR pipeline that recovers the raw text, repairs it, and emits structured **JSON** plus database records.

Around that core sit three more subsystems that make it a complete product rather than a script:

- a **trained NLU chatbot** (NLTK + Keras) that answers insurance questions in **three languages** — English, French, and Tunisian dialect (*tounsi*);
- a **DRF JSON API** exposing the domain entities over **6 REST endpoints**;
- **analytics dashboards** rendered with **Chart.js** (4 aggregation endpoints) and **Bokeh** (a server-side product chart).

> This is a student / coursework project, presented as-is for learning and demonstration. It is **not** a production system — see *Limitations & Senior Judgment* below.

### At a glance

| Dimension | Concrete scale |
|---|---|
| Django apps | **3** — `customer`, `backoffice`, and the `humanressource` project package |
| Domain models | **9** — `Customer` (1) + `Category`, `Vocation` (policy), `Sales`, `LeaveRecord`, `Question`, `Car`, `Card`, `Course` (8) |
| OCR engines | **3** — Tesseract (`pytesseract`), `EasyOCR`, `ArabicOcr` — plus `pyzbar` for barcodes/QR |
| Transform stages | grayscale → median-blur → Otsu threshold → **skew correction** → **reading-order reconstruction** → punctuation cleanup → **neural auto-correction** |
| Neural correctors | **3** bundled Keras models — `model_first_name`, `model_last_name`, `model_job_name` (trained on the matching `*.csv` corpora) |
| Chatbot | **33 intents** across **3 languages**, with a per-language "I don't understand" fallback |
| REST API | **6** DRF `ModelViewSet` endpoints |
| Dashboards | **4** Chart.js JSON endpoints + **1** Bokeh chart + a data-driven year filter |

---

## Architecture & Rationale (Extract → Transform → Load)

The pipeline lives in `customer/views.py` (image + text processing) and `customer/chat.py` (the NLU layer). Each stage exists for a reason; the choices below are the interesting part of the project.

```
        ┌──────────────────────────────────────────────────────────────────┐
        │  document image  (carte grise / contrat / invoice — JPG/PNG)      │
        └───────────────────────────────┬──────────────────────────────────┘
                                         ▼
   E X T R A C T   ───────────────────────────────────────────────────────────
        multi-engine OCR, chosen by script:
          • pytesseract (Tesseract)   → general Latin text
          • EasyOCR (Reader)          → robust Latin / mixed layouts
          • ArabicOcr                 → Arabic script (RTL)
          • pyzbar                    → barcodes / QR on the document
                                         ▼
   T R A N S F O R M ─────────────────────────────────────────────────────────
        OpenCV pre-processing:
          grayscale  →  medianBlur (denoise)  →  Otsu binary threshold
        geometry repair:
          correct_orientation()  — searches angles in ±45° at 0.1° steps,
              picking the rotation that MAXIMISES the horizontal
              projection-profile score (classic deskew heuristic)
        structure repair:
          correct_ocr_order()    — clusters OCR boxes into lines by
              vertical-coordinate proximity, then orders them top-to-bottom
              so the text reads in the right sequence
          correct_ocr_output()   — strips punctuation / fixes common
              mis-reads ($→S, ()→0)
        learned repair:
          auto_correction_word() — a Keras n-gram language model
              (loaded from model_first_name / _last_name / _job_name)
              re-predicts garbled name/job tokens character-by-character
                                         ▼
   L O A D   ─────────────────────────────────────────────────────────────────
          • structured JSON       → processed.json, processed1..3.json
          • relational records    → Django / SQLite (9 models)
                                         ▼
   S E R V E ─────────────────────────────────────────────────────────────────
          • DRF JSON API (6 endpoints)   • Chart.js + Bokeh dashboards
          • multilingual NLU chatbot (separate NLU layer, intents.json)
```

### Why these choices

- **Why multiple OCR engines instead of one.** Insurance paperwork in this domain mixes **Latin** fields (names, plate numbers, French labels) with **Arabic** script (Tunisian *carte grise* headers). A single Latin-trained engine mangles Arabic, and a single Arabic engine is wasteful on Latin. The project therefore keeps **Tesseract** and **EasyOCR** for Latin/mixed text and a dedicated **ArabicOcr** path (with `arabic_reshaper` + `python-bidi` for correct RTL display), so each script is read by an engine that can actually handle it.
- **Why a deskew step.** Phone-photographed documents arrive rotated. `correct_orientation()` brute-forces the rotation angle (±45°, 0.1° resolution) and keeps the one that maximises the projection-profile variance — a well-known, dependency-light deskew that needs no training data.
- **Why reading-order reconstruction.** OCR engines return boxes in detection order, not reading order. `correct_ocr_order()` re-groups boxes into lines by their vertical position and sorts them, so downstream JSON reflects how a human reads the page — essential before any field extraction.
- **Why a neural corrector on top of OCR.** OCR routinely garbles proper nouns and job titles that no spell-checker dictionary contains. Rather than a static lexicon, the project trains small **Keras** character/word models per field type (first name / last name / job) so corrections are learned from real corpora (`first_name.csv`, `last_name.csv`, `job_name.csv`).
- **Why the chatbot is a separate NLU layer.** It is not OCR — it is intent classification. `customer/chat.py` tokenises + lemmatises with **NLTK** (WordNet), builds a bag-of-words, and runs a **Keras** classifier with an `ERROR_THRESHOLD = 0.25` candidate cut and a `0.4` confidence floor before answering; below that it emits the right "I don't understand" message **in the user's language**. Keeping it decoupled from the ETL path means each can evolve independently.
- **Why DRF + dashboards on top.** Once data is structured and loaded, **Django REST Framework** `ModelViewSet`s expose it as JSON (`/rpolicy/`, `/ruser/`, `/rpolicyRecord/`, `/rcategory/`, `/rpayment/`, `/rquestion/`), and `backoffice/views.py` aggregates the same tables (Django `ExtractYear` / `ExtractMonth` / `Sum` / `Avg` / `Count`) into Chart.js-ready JSON for the management dashboards.

---

## Why It's Hard (the honest thesis)

Most student web projects are CRUD. This one chains an entire **document-image → structured-data** pipeline and three additional ML/web subsystems into a single Django codebase:

- **Unstructured input.** The input is a *photograph*, not a form. Everything downstream depends on getting usable text out of noisy, skewed, multi-script images — the genuinely hard, real-world ETL case.
- **Multilingual on two fronts.** OCR must handle Latin **and** Arabic script (different engines, RTL handling); the chatbot must classify intent in **English, French, and Tunisian dialect** (33 intents). Multilingual is hard once; here it shows up twice, in two different ML problems.
- **Learned post-correction.** Going beyond off-the-shelf OCR to *train your own* Keras correctors per field type is more than wiring a library — it requires assembling corpora and a training/inference loop.
- **End-to-end in one system.** Extraction, transformation, learned correction, structured load, REST serving, a trained NLU chatbot, and analytics dashboards all coexist behind one Django project. Integrating that many moving parts coherently is ambitious for a coursework scope, and the breadth is the achievement.

---

## Features

### ETL / document-processing pipeline (`customer/views.py`)
- **Extract** — `pytesseract` (Tesseract), `EasyOCR` (`Reader`), and `ArabicOcr` for Arabic text; `pyzbar` for barcode/QR decoding.
- **Transform** — `grayscale` / `remove_noise` (median blur) / `thresholding` (Otsu); `correct_orientation` (projection-profile deskew); `correct_ocr_order` (reading-order reconstruction); `correct_ocr_output` (punctuation/mis-read cleanup); `auto_correction_word` (Keras n-gram correction using the bundled `model_first_name` / `model_last_name` / `model_job_name`).
- **Load** — structured JSON (`processed.json`, `processed1..3.json`) + Django/SQLite records.

### Multilingual chatbot (`customer/chat.py`, `intents.json`)
- **NLTK** tokenisation + WordNet lemmatisation → bag-of-words → **Keras** intent classifier.
- **33 intents** spanning greetings, goodbyes, insurance types, site/contract/tariff/payment Q&A across **EN / FR / Tounsi**.
- Thresholded decision (`0.25` candidate / `0.4` answer) with a graceful, per-language fallback.

### Insurance back office (Django, `backoffice/`)
- Customer sign-up / login, profile, and notification preferences (email / SMS / call / WhatsApp toggles).
- Admin CRUD for **categories**, **policies** (`Vocation`), **policy holders** (`LeaveRecord` — Approve / Disapprove / Pending), and **customer questions**.
- Template-based document generation with **Pillow** (attendance certificates, payslips, authorisations); PDF via `pdfkit` and **PyMuPDF (`fitz`)**.
- Car reference data from `car_brands.json` backing the `Car` model.

### Analytics dashboards (`backoffice/views.py`, `backoffice/charts.py`)
- **4 Chart.js JSON endpoints**: sales per month, average spend per customer per month, and payment-method breakdown — plus a **year filter** derived from the data's distinct creation years.
- **1 Bokeh** server-rendered product chart.

### REST API (`backoffice/views.py`, `backoffice/json.py`, `humanressource/urls.py`)
- **6** DRF `ModelViewSet` + serializer endpoints: `/rpolicy/`, `/ruser/`, `/rpolicyRecord/`, `/rcategory/`, `/rpayment/`, `/rquestion/`.

### Payments (sandbox / test mode)
- Checkout flows wired for **Stripe**, **PayPal** (`django-paypal`), and **Coinbase Commerce** — configured in test mode only.

---

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Language** | Python |
| **Web framework** | Django 3.0.5 |
| **API** | Django REST Framework |
| **Database** | SQLite (Django default) |
| **OCR / Computer Vision** | OpenCV (`cv2`), `pytesseract`, `EasyOCR`, `ArabicOcr`, `pyzbar`, `arabic_reshaper`, `python-bidi`, SciPy, NumPy, Pillow, Matplotlib |
| **ML / NLP** | TensorFlow / Keras, NLTK, `python-Levenshtein` |
| **Documents** | `pdfkit` (+ `wkhtmltopdf`), PyMuPDF (`fitz`), Pillow |
| **Visualisation** | Chart.js (front end), Bokeh (server-rendered) |
| **Admin / data IO** | `django-import-export`, `django-widget-tweaks` |
| **Payments** | Stripe, PayPal (`django-paypal`), Coinbase Commerce |
| **Front end** | Bootstrap, Soft UI Dashboard theme, jQuery |

> **⚠️ Dependency reproducibility gap (be aware before installing).** The committed `requirements.txt` pins only **5** packages — `Django==3.0.5`, `asgiref`, `django-widget-tweaks`, `pytz`, `sqlparse` — i.e. the Django runtime alone. The application code, however, **imports a much larger stack** that is *not* pinned there: OpenCV, EasyOCR, ArabicOcr, pytesseract, TensorFlow/Keras, NLTK, SciPy, NumPy, Matplotlib, `pyzbar`, `arabic_reshaper`, `python-bidi`, `python-Levenshtein`, `pdfkit`, PyMuPDF, Pillow, Stripe, `coinbase_commerce`, `django-paypal`, `django-import-export`, and the DRF (`rest_framework`). **`pip install -r requirements.txt` alone will NOT run the OCR/ML/payment/charting features** — those libraries (and system Tesseract + `wkhtmltopdf`) must be installed manually. This is a real reproducibility risk and is the project's most important known limitation.

---

## Project Structure

```
ETL-Django-academic-project/
├── manage.py
├── requirements.txt                 # ⚠ pins 5 pkgs; code needs ~20+ (see note above)
├── humanressource/                  # Django project (settings, URLs, WSGI/ASGI)
│   ├── settings.py                  # ⚠ DEBUG=True + hardcoded SECRET_KEY + test payment/SMTP keys
│   └── urls.py                      # admin pages, charts, 6 DRF routers, customer include
├── customer/                        # Customer-facing app
│   ├── models.py                    # Customer
│   ├── views.py                     # OCR/ETL pipeline, payments, document generation
│   ├── chat.py                      # NLTK + Keras intent chatbot
│   ├── forms.py / urls.py
├── backoffice/                      # Admin / insurance back office
│   ├── models.py                    # Category, Vocation, Sales, LeaveRecord, Question, Car, Card, Course
│   ├── views.py                     # CRUD, chart aggregation, 6 DRF viewsets
│   ├── charts.py                    # chart helpers (months, palettes, year dict)
│   ├── json.py                      # DRF serializers
│   └── admin.py                     # import/export-enabled admin
├── utils/charts.py
├── templates/                       # HTML templates (home, backoffice, customer, dashboard)
├── static/                          # CSS/JS/img assets (Soft UI Dashboard theme)
├── intents.json                     # 33 chatbot intents (EN / FR / Tounsi)
├── car_brands.json                  # car brand reference catalogue
├── first_name.csv / last_name.csv / job_name.csv     # neural-corrector training corpora
├── model_first_name / model_last_name / model_job_name  # saved Keras correctors
├── processed*.json                  # example structured ETL outputs
└── *.png / *.jpg                    # sample document images & intermediate stage outputs
```

---

## Getting Started

### Prerequisites
- Python 3.x
- The core packages in `requirements.txt` (Django 3.0.5 + runtime).
- **For the OCR/ML features** (not in `requirements.txt`): a system **Tesseract OCR** install, **`wkhtmltopdf`** (for `pdfkit`), and the Python packages OpenCV, EasyOCR, ArabicOcr, `pytesseract`, TensorFlow/Keras, NLTK, SciPy, NumPy, Matplotlib, `pyzbar`, `arabic_reshaper`, `python-bidi`, `python-Levenshtein`, PyMuPDF, Pillow, `djangorestframework`, `django-import-export`, and the payment SDKs.

### Installation

```bash
# 1. Clone
git clone https://github.com/MuhamedHabib/ETL-Django-academic-project.git
cd ETL-Django-academic-project

# 2. Virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Core dependencies (Django runtime only — see the dependency-gap note)
pip install -r requirements.txt
# Then install the OCR/ML/payment/charting libraries above manually
# (plus system Tesseract and wkhtmltopdf) to enable the full feature set.

# 4. Database migrations
python manage.py migrate

# 5. (Optional) admin user
python manage.py createsuperuser

# 6. Run
python manage.py runserver
```

Then open `http://127.0.0.1:8000/`.

> The chatbot needs NLTK data packages (`punkt`, `wordnet`, `omw-1.4`) — see the commented `nltk.download(...)` lines in `customer/chat.py`.

---

## Limitations & Senior Judgment

Naming weaknesses honestly is part of the engineering. This project has clear, fixable ones:

1. **Reproducibility risk (highest priority).** `requirements.txt` pins 5 packages while the code imports ~20+ heavy OCR/ML libraries (above). Anyone cloning the repo cannot reproduce the OCR/ML features from the lockfile alone. *Next step:* regenerate a complete, pinned `requirements.txt` (`pip freeze`), split into `requirements/base.txt` + `requirements/ml.txt`, and document the system deps (Tesseract, `wkhtmltopdf`); ideally containerise so the environment is reproducible.
2. **Committed secrets.** `humanressource/settings.py` ships with `DEBUG = True`, a hardcoded `SECRET_KEY`, and test-mode payment + SMTP credentials. **Do not reuse these.** *Next step:* move all secrets to environment variables / an untracked `.env`, set `DEBUG = False`, configure `ALLOWED_HOSTS`, and **rotate every key that was ever committed** (git history retains them).
3. **OCR robustness.** The deskew is a brute-force angle search and the engine selection is manual; there is no confidence scoring, no automatic Latin-vs-Arabic routing, and no held-out evaluation of extraction accuracy. *Next step:* add per-field confidence thresholds, automatic script detection to route between engines, and a small labelled test set to measure character/field accuracy.
4. **Neural corrector scope.** The Keras correctors cover only `first_name` / `last_name` / `job_name`; other fields fall back to OCR + punctuation cleanup. *Next step:* broaden corpora/fields and version the models.
5. **Code hygiene.** Several view paths and chart/invoice endpoints are commented out or experimental, reflecting the iterative coursework nature. *Next step:* prune dead code, add tests around the ETL functions, and pin the OCR engine versions (results vary across engine releases).

---

## Notes

- **Academic project** — built as coursework to explore an end-to-end ETL flow (OCR extraction → text transformation/cleanup → structured JSON/database loading) wrapped in a full Django web application.
- The bundled sample images, `processed*.json` outputs, and saved Keras models are included to illustrate the pipeline's inputs and intermediate/output stages.
- The default database is SQLite and the app runs entirely locally, which keeps it easy to clone, migrate, and explore.

---
<p align="center">Built by <b>Mohamed Habib Khattat</b> — <a href="https://github.com/MuhamedHabib">GitHub (@MuhamedHabib)</a> · <a href="https://www.linkedin.com/in/mohamed-habib-khattat-2b206a173">LinkedIn</a></p>
