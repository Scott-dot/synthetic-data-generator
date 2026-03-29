# Synthetic Data Generator

A local LLM-powered utility that generates synthetic datasets from a plain English 
description. Designed to produce CSV files for use in data engineering projects, 
pipeline testing, and portfolio demonstrations.

Built as a supporting tool across a suite of data/AI portfolio projects.

---

## What this demonstrates

- Two-stage LLM pipeline: schema design followed by data generation
- Prompt engineering for structured JSON output from a local model
- Graceful error handling and JSON recovery for malformed LLM responses
- Configurable dirty data injection for testing data quality pipelines
- Clean separation between user interaction, LLM calls, validation, and output

---

## How it works
```
User input (guided or random)
        ↓
LLM designs schema (fields, types, row counts, file structure)
        ↓
Schema sanitised and capped (field count, row count, type validation)
        ↓
LLM generates rows per file matching schema
        ↓
Rows validated against schema
        ↓
Optional dirty data injection (outliers, nulls, duplicates)
        ↓
CSV files + schema.json + generation_report.txt saved to /output
```

---

## Modes

**Guided** — answer a series of questions:
- Industry
- Data type
- Number of files
- Time period
- Rows per file
- Dirty data configuration

**Random** — LLM decides everything. Industry, schema, structure, and row 
counts are chosen autonomously. Good for quickly generating varied test data.

Both modes support dirty data injection.

---

## Dirty data injection

An optional post-generation pass that deliberately introduces noise:

| Type | Description | Default rate |
|---|---|---|
| Outliers | Numeric values multiplied 5–15x | 2% |
| Nulls | Random fields set to None | 1% |
| Duplicates | Random rows duplicated and appended | 1% |

Rates are configurable at runtime.

---

## Stack

| Component | Tool |
|---|---|
| LLM | Llama 3.2 via Ollama (local) |
| Data output | Python csv module |
| Validation | Custom schema validator |

---

## Setup

**Prerequisites:** Python 3.10+, [Ollama](https://ollama.com) installed and running
```bash
pip install requests

ollama pull llama3.2:3b
```

## Usage
```bash
python main.py
```

Follow the prompts. Output is saved to `/output/{filename_prefix}_{timestamp}/` 
containing CSV files, `schema.json`, and `generation_report.txt`.

---

## Project structure
```
synthetic-data-generator/
├── generator/
│   ├── prompt.py       # builds schema design and data generation prompts
│   ├── llm.py          # Ollama calls + JSON parsing and recovery
│   ├── dirty.py        # post-generation dirty data injection
│   └── validate.py     # validates generated rows against schema
├── output/             # generated datasets land here (not committed)
├── interactive.py      # guided question flow and random mode
├── main.py             # entry point and pipeline orchestrator
└── config.py           # model settings, output path, dirty data defaults
```

---

## Known limitations

This project uses `llama3.2:3b` running locally via Ollama. As a small model it 
has known constraints:

- **Data variety** — generated values can be repetitive; a larger model (GPT-4, 
  Claude) would produce richer, more realistic data
- **JSON reliability** — the model occasionally produces malformed JSON; the 
  parser includes recovery logic for the most common failure modes (missing 
  brackets, leading zeros, missing opening bracket)
- **Field type compliance** — the model sometimes returns verbose type strings 
  despite explicit instructions; types are sanitised post-generation as a fallback
- **Row limits** — generation is capped at 50 rows per file and 3 files per run 
  to prevent GPU overload and context truncation on consumer hardware

These are intentional tradeoffs: local inference is free, private, and runs 
offline. Swapping to an API-based model in `generator/llm.py` would resolve most 
quality issues.