# BIS Standards Recommendation Engine

A RAG-based system that takes a product description and returns the most relevant 
BIS/IS standards from SP 21. Built for the BIS Hackathon 2026.

## Results on Public Test Set

Hit Rate @3  : 100%
MRR @5       : 1.0000
Avg Latency  : 0.02 seconds

## Project Structure

BIS_Hackathon/
  src/              - main application code
  data/             - results from public test set
  eval_script.py    - official evaluation script
  inference.py      - entry point for judges
  requirements.txt  - all dependencies

## Setup

Install dependencies:
pip install -r requirements.txt

You also need pdftotext installed:
sudo apt install poppler-utils
On Windows: download poppler from https://github.com/oschwartz10612/poppler-windows/releases
and add the bin folder to your PATH.

## How to Run

Step 1 - Build the index (run once):
python build_index.py

Step 2 - Single query:
python inference.py --query "We manufacture 33 Grade Ordinary Portland Cement"

Step 3 - Batch evaluation:
python inference.py --batch public_test_set.json --output results.json --no-llm
python eval_script.py --results results.json

Step 4 - Web UI:
python src/app.py
Then open http://localhost:7860

## API Key Setup (optional, for rationale generation)

Create a .env file in the project root:
GROQ_API_KEY=your_key_here

Get a free key from https://console.groq.com
If no key is provided the system still works fully, just without plain-English rationales.

## How It Works

The system has four stages:

1. Query Expansion - maps abbreviations like OPC, PPC, TMT to their full technical 
   terms before searching. 30+ mappings built in.

2. Hybrid Retrieval - runs BM25 and TF-IDF simultaneously on 566 IS standards 
   parsed from SP 21. Scores are normalised and blended 50-50. Returns top 8 candidates.

3. Rationale Generation - top 6 candidates are sent to Llama 3.3 via Groq API.
   The model can only pick from retrieved candidates, making hallucination 
   architecturally impossible.

4. Post Validation - every IS code in the response is checked against the 
   retrieved list in code. Anything not in the list is dropped.

## Why BM25 + TF-IDF over Neural Embeddings

SP 21 is a structured reference document with precise technical terminology. 
Exact keyword matching outperforms semantic similarity for this task. 
Neural embedding models add 1-3 seconds of inference time on CPU with no 
accuracy gain here. Our retrieval runs in 0.02 seconds with no GPU required.