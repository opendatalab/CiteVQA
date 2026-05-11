# CiteVQA: Benchmarking Evidence Attribution for Trustworthy Document Intelligence

## Overview

CiteVQA is a benchmark for evaluating evidence attribution capabilities of document intelligence models. It assesses whether models can not only answer questions about document content, but also accurately cite the supporting evidence (bounding boxes) from the source pages.

The evaluation covers three dataset types:
- **Single-Doc**: Single-document question answering
- **Multi (1-Gold)**: Multi-document QA with exactly one gold document
- **Multi (N-Gold)**: Multi-document QA with multiple gold documents

### Metrics

| Metric | Description |
|---|---|
| **Recall** | Whether the predicted evidence bbox overlaps with the ground truth |
| **Relevance (Rel)** | Semantic relevance of the cited evidence to the question |
| **QA Accuracy (Ans)** | Answer correctness (judged by a VLM judge) |
| **SAA** | Joint accuracy: correct answer AND valid evidence |
| **Page Recall** | Whether the correct page is identified |
| **Precision** | Precision of evidence bboxes |
| **F1** | F1 score of evidence bboxes |

## Setup

### 1. Install Dependencies

```bash
cd CiteVQA
pip install -r requirements.txt
```

<details>
<summary>Chinese Font Configuration (for PDFs with CJK characters)</summary>

```bash
apt install fonts-noto-cjk poppler-data

cat > /etc/fonts/conf.d/99-pdf-cjk.conf << 'EOF'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <alias><family>STSong-Light</family><prefer><family>Noto Serif CJK SC</family></prefer></alias>
  <alias><family>STSong</family><prefer><family>Noto Serif CJK SC</family></prefer></alias>
  <alias><family>SimSun</family><prefer><family>Noto Serif CJK SC</family></prefer></alias>
  <alias><family>FangSong</family><prefer><family>Noto Serif CJK SC</family></prefer></alias>
  <alias><family>KaiTi</family><prefer><family>Noto Serif CJK SC</family></prefer></alias>
  <alias><family>SimHei</family><prefer><family>Noto Sans CJK SC</family></prefer></alias>
  <alias><family>Microsoft YaHei</family><prefer><family>Noto Sans CJK SC</family></prefer></alias>
</fontconfig>
EOF

fc-cache -f
```

</details>

### 2. Download Dataset & PDFs 

```bash
kaggle datasets download anonymouscitevqa/citevqa -p data --unzip
python data/download/download_pdfs.py --workers 16 --out data/pdf --csv data/download/pdf_source.csv
```

This reads `data/download/pdf_source.csv` and downloads all PDFs to `data/pdf/`. Options:

| Option | Default | Description |
|---|---|---|
| `--csv` | `pdf_source.csv` | CSV source file |
| `--out` | `pdf` | Output directory |
| `--workers` | 16 | Number of concurrent downloads |
| `--timeout` | 120 | Timeout per file (seconds) |
| `--retries` | 3 | Retry count on failure |
| `--no-skip` | — | Re-download existing files |

### 3. Inference & Evaluation

Edit `run.sh` with your API credentials, then run:

```bash
bash run.sh
```

See `run.sh` for the full demo:

```bash
# --- API Config ---
API_TYPE=openai          # openai / genai / anthropic
API_KEY=YOUR_API_KEY
BASE_URL=YOUR_BASE_URL

# --- Inference ---
python infer/run.py \
  --api ${API_TYPE} \
  --model MODEL_NAME \
  --base_url ${BASE_URL} \
  --api_key ${API_KEY} \
  --workers 4 \
  --out outputs/infer/MODEL_NAME.json

# --- Evaluation ---
python eval/run.py \
  --judge_api ${API_TYPE} \
  --judge_model JUDGE_MODEL_NAME \
  --judge_api_key ${API_KEY} \
  --base_url ${BASE_URL} \
  --input outputs/infer/MODEL_NAME.json \
  --out outputs/eval/MODEL_NAME.json \
  --workers 24

# --- Summary ---
python eval/summarize.py \
  --input outputs/eval/MODEL_NAME.json \
  --out_dir outputs/eval/MODEL_NAME
```

#### Inference Options

| Option | Required | Description |
|---|---|---|
| `--api` | Yes | API type: `openai`, `genai`, or `anthropic` |
| `--model` | Yes | Model name |
| `--api_key` | Yes | API key |
| `--base_url` | No | API base URL (for proxies) |
| `--workers` | No | Concurrent workers (default: 4) |
| `--out` | No | Output JSON path |
| `--benchmark` | No | Benchmark JSON path (default: `data/data_items.json`) |
| `--limit` | No | Limit number of items (0 = all) |
| `--max_pdf_mb` | No | Max PDF size in MB before compression (default: 10) |

#### Evaluation Options

| Option | Required | Description |
|---|---|---|
| `--input` | Yes | Inference output JSON |
| `--judge_api` | No | Judge API type (default: `openai`) |
| `--judge_model` | No | Judge model name (default: `gpt-4o`) |
| `--judge_api_key` | Yes | Judge API key |
| `--base_url` | No | API base URL (for proxies) |
| `--metrics` | No | Comma-separated metrics (default: `recall,rel`) |
| `--workers` | No | Concurrent workers (default: 4) |
| `--out` | No | Output JSON path |
| `--limit` | No | Limit number of items (0 = all) |

## Project Structure

```
citevqa/
├── data/
│   ├── data_items.json          # Benchmark QA pairs
│   ├── pdf/                     # Downloaded PDFs
│   └── download/
│       ├── pdf_source.csv       # PDF metadata & URLs
│       └── download_pdfs.py     # PDF download script
├── infer/
│   └── run.py                   # Inference script
├── eval/
│   ├── run.py                   # Evaluation script
│   └── summarize.py             # Summary table generator
├── prompts/                     # System & user prompts
├── outputs/                     # Inference & evaluation outputs
├── requirements.txt
└── run.sh                       # Demo script
```
