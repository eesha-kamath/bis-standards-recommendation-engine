"""
BIS Standards Recommendation Engine build_index.py
Parses SP 21 PDF and builds the hybrid BM25 + TF-IDF search index.

Run once:  python build_index.py
Then use:  python inference.py --query "your product description"

Requirements:
    pip install scikit-learn rank-bm25 requests
    sudo apt install poppler-utils   (for pdftotext)
"""
import re, json, pickle, subprocess
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from rank_bm25 import BM25Okapi

PDF_PATH  = "dataset.pdf"
INDEX_DIR = "../index"
Path(INDEX_DIR).mkdir(exist_ok=True)

# 1. Extract text from PDF 
print("Extracting text from SP 21 PDF...")
subprocess.run(["pdftotext", PDF_PATH, f"{INDEX_DIR}/sp21.txt"], check=True)
with open(f"{INDEX_DIR}/sp21.txt") as f:
    text = f.read()
print(f"   {len(text):,} characters extracted")

# 2. Parse IS standard entries
print("Parsing IS standard entries...")

# Matches: "IS 269 : 1989 ORDINARY PORTLAND CEMENT, 33 GRADE"
# Also handles digit-starting titles like "IS 8112 : 1989 43 GRADE ORDINARY..."
header_pattern = re.compile(
    r'(?:^|\n|\x0c)(IS\s+\d+(?:\s*\([A-Za-z0-9\s]+\))?\s*:\s*\d{4})\s+'
    r'([A-Z0-9][A-Z\s,/\(\)\-\.0-9]+)',
    re.MULTILINE
)

all_positions = []
for m in header_pattern.finditer(text):
    is_ref = re.sub(r'\s*:\s*', ': ', re.sub(r'\s+', ' ', m.group(1)).strip())
    all_positions.append((m.start(), is_ref, m.group(2).strip()))
all_positions.sort(key=lambda x: x[0])

# Extract content blocks between headers
all_entries = []
for i, (pos, is_ref, title) in enumerate(all_positions):
    end = all_positions[i+1][0] if i+1 < len(all_positions) else len(text)
    all_entries.append((is_ref, title, text[pos:end].strip()))

# De-duplicate: keep the LONGEST content per IS ID
# (avoids picking Table of Contents stubs over actual summaries)
best = {}
for is_ref, title, content in all_entries:
    if is_ref not in best or len(content) > len(best[is_ref][1]):
        best[is_ref] = (title, content)

print(f"   {len(best)} unique standards found")

# 3. Build enriched documents
# Add domain aliases so abbreviations (OPC, PPC, TMT…) match correctly
ALIASES = {
    "IS 269: 1989":          ["OPC 33", "OPC", "ordinary portland cement 33 grade"],
    "IS 8112: 1989":         ["OPC 43", "43 grade OPC", "ordinary portland cement 43 grade"],
    "IS 12269: 1987":        ["OPC 53", "53 grade OPC", "ordinary portland cement 53 grade", "high strength cement"],
    "IS 1489 (PART 1): 1991":["PPC fly ash", "portland pozzolana fly ash cement"],
    "IS 1489 (PART 2): 1991":["PPC calcined clay", "calcined clay pozzolana cement"],
    "IS 455: 1989":          ["PSC", "portland slag cement", "blast furnace slag cement"],
    "IS 12330: 1988":        ["SRPC", "sulphate resisting cement", "marine cement", "coastal cement"],
    "IS 6909: 1990":         ["supersulphated cement", "aggressive water cement marine"],
    "IS 8041: 1990":         ["RHPC", "rapid hardening cement", "fast setting cement"],
    "IS 8042: 1989":         ["white cement", "decorative cement", "architectural cement"],
    "IS 8043: 1991":         ["hydrophobic cement", "waterproof cement moisture resistant"],
    "IS 383: 1970":          ["coarse aggregate", "fine aggregate", "natural aggregate concrete"],
    "IS 458: 2003":          ["concrete pipe", "precast pipe", "drainage pipe", "RCC pipe", "water main pipe"],
    "IS 2185 (PART 1): 1979":["concrete masonry block", "normal weight hollow block"],
    "IS 2185 (PART 2): 1983":["lightweight concrete block", "hollow lightweight block", "aerated block"],
    "IS 459: 1992":          ["asbestos cement sheet", "AC sheet", "corrugated roofing sheet"],
    "IS 3466: 1988":         ["masonry cement", "mortar cement", "bricklaying cement"],
    "IS 6452: 1989":         ["high alumina cement", "HAC", "refractory cement"],
}

standards_list = []
for is_ref, (title, content) in best.items():
    alias_text = " ".join(ALIASES.get(is_ref, []))
    content_clean = re.sub(r'\s+', ' ', content).strip()
    doc_text = f"Standard {is_ref}: {title}. {content_clean[:1400]} {alias_text}".strip()
    standards_list.append({
        "id":       is_ref,
        "title":    title,
        "content":  content[:1500],
        "doc_text": doc_text
    })

# 4. Build TF-IDF + BM25 indexes
print("Building TF-IDF index (trigrams)...")
corpus   = [s["doc_text"] for s in standards_list]
tfidf    = TfidfVectorizer(ngram_range=(1, 3), min_df=1, sublinear_tf=True)
tfidf_mx = tfidf.fit_transform(corpus)
print(f"   Matrix: {tfidf_mx.shape}")

print("Building BM25 index...")
bm25 = BM25Okapi([doc.lower().split() for doc in corpus])

# 5. Save
with open(f"{INDEX_DIR}/standards.json", "w") as f:
    json.dump(standards_list, f, indent=2)
with open(f"{INDEX_DIR}/tfidf.pkl", "wb") as f:
    pickle.dump({"tfidf": tfidf, "matrix": tfidf_mx}, f)
with open(f"{INDEX_DIR}/bm25.pkl", "wb") as f:
    pickle.dump(bm25, f)

print(f"\nIndex built: {len(standards_list)} standards in {INDEX_DIR}/")
print("   Run: python inference.py --query 'your product description here'")
