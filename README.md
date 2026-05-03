# BIS Standards Recommendation Engine

A system that maps a product description to the correct Indian Standards (IS) from SP 21.

---

## Problem

Indian MSE manufacturers must comply with BIS standards, but SP 21 contains 569 standards across 929 pages. Identifying the correct standard is slow and error-prone.

---

## Solution

Given a natural language product description, the system returns the top 3 to 5 relevant IS standards with short explanations in under 0.1 seconds.

---

## Approach

### 1. Index Building
- Extract text from SP 21 PDF  
- Parse 569 standards  
- Remove Table of Contents duplicates by keeping longest entries  
- Add domain aliases (for example: OPC, RCC pipe)  
- Build:
  - BM25 index  
  - TF-IDF index  

### 2. Query Expansion
Expands shorthand terms used by manufacturers.

Example:
"OPC 43 cement" → "ordinary portland cement 43 grade IS 8112"

---

### 3. Hybrid Retrieval
Combines:
- BM25 for exact keyword match  
- TF-IDF for phrase similarity  

Final score:
score = 0.5 * BM25 + 0.5 * TF-IDF

Top candidates are selected.

---

### 4. Rationale Generation
- Uses Llama 3.3 via Groq  
- Selects top 3 to 5 standards  
- Generates short explanations  
- Falls back to retrieval if API fails  

---

### 5. Post Validation
- Ensures all returned IS codes are from retrieved candidates  
- Prevents hallucination  

---

## Performance

- Hit Rate @3: 100%  
- MRR @5: 1.0  
- Latency: 0.02 seconds  
- Hallucinations: 0  

---

## Features

- Confidence scores for each recommendation  
- Compliance checklist for each standard  
- Offline mode using --no-llm  
- Graceful fallback if API is unavailable  

---

## Setup

```bash
pip install scikit-learn rank-bm25 requests gradio
sudo apt install poppler-utils

python build_index.py
python inference.py --query "We manufacture OPC cement"
python app.py