"""
BIS Standards Recommendation Engine — inference.py
Hybrid BM25 + TF-IDF retrieval with query expansion + alias enrichment.
Optional Claude API for plain-English rationale generation.

Usage:
  Single query:  python inference.py --query "We manufacture 33 Grade OPC"
  Batch eval:    python inference.py --batch public_test_set.json --output results.json
  No API key:    python inference.py --query "..." --no-llm

  https://console.groq.com/keys
"""
import re, json, pickle, time, argparse, os
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
import requests

from dotenv import load_dotenv
load_dotenv()

INDEX_DIR = "./index"
API_URL   = "https://api.anthropic.com/v1/messages"
MODEL     = "claude-haiku-4-5-20251001"
GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_K     = 8     # retrieve 8, present top 5
ALPHA     = 0.5   # BM25 : TF-IDF blend weight

# ── Query expansion dictionary
# Maps abbreviations and synonyms → full technical terms that appear in SP 21
QUERY_EXPANSIONS = {
    "opc 53": "53 grade ordinary portland cement IS 12269",
    "opc 43": "43 grade ordinary portland cement IS 8112",
    "opc 33": "33 grade ordinary portland cement IS 269",
    "opc":    "ordinary portland cement grade",
    "ppc":    "portland pozzolana cement fly ash calcined clay",
    "psc":    "portland slag cement blast furnace",
    "srpc":   "sulphate resisting portland cement marine",
    "rhpc":   "rapid hardening portland cement",
    "hac":    "high alumina cement refractory",
    "rcc":    "reinforced cement concrete structural",
    "tmt":    "thermomechanical treated steel bars deformed reinforcement",
    "tmt bar":"deformed high strength steel bars reinforcement",
    "ms pipe":"mild steel pipe water supply",
    "gi pipe":"galvanized iron steel pipe water",
    "ci pipe":"cast iron pipe drainage",
    "pvc pipe":"polyvinyl chloride plastic pipe water supply drainage",
    "hdpe":   "high density polyethylene pipe",
    "aac block":"autoclaved aerated concrete lightweight masonry",
    "hollow block": "concrete masonry unit hollow lightweight",
    "solid block":  "concrete masonry unit solid",
    "fly ash": "portland pozzolana cement fly ash based",
    "calcined clay": "portland pozzolana cement calcined clay based",
    "coastal": "sulphate resisting cement marine aggressive water",
    "marine":  "sulphate resisting cement marine works aggressive",
    "white cement": "white portland cement architectural decorative",
    "rapid hardening": "rapid hardening portland cement fast setting",
    "waterproof cement": "hydrophobic portland cement",
    "drainage pipe": "precast concrete pipe drainage reinforced",
    "water main":    "precast concrete pipe water mains supply",
    "roofing sheet": "asbestos cement corrugated sheet roofing",
    "masonry mortar": "masonry cement mortar bricklaying",
    "aggregate concrete": "coarse fine aggregate natural sources structural concrete",
    "aluminium door": "aluminium doors windows ventilators IS 1948",
    "aluminium window": "aluminium windows ventilators IS 1948 1949",
    "aluminum door": "aluminium doors windows ventilators IS 1948",
    "aluminum window": "aluminium doors windows ventilators IS 1948",
    "clay brick": "burnt clay building bricks common",
    "red brick": "common burnt clay building bricks",
    "ms pipe": "mild steel tube water supply IS 1239",
    "gi pipe": "mild steel tube water supply galvanized IS 1239",
    "roof tile": "burnt clay roof tiles ceramic",
    "clay tile": "burnt clay roof tiles ceramic IS 2690",
    "glass sheet": "flat glass sheets glazing IS 2835",
    "glass pane": "flat glass sheets glazing IS 2835",
    "window glass": "flat glass sheets glazing IS 2835",
}

# ── Load indexes (once at module import)
def _load():
    with open(f"{INDEX_DIR}/standards.json") as f:
        stds = json.load(f)
    with open(f"{INDEX_DIR}/tfidf.pkl", "rb") as f:
        d = pickle.load(f)
    with open(f"{INDEX_DIR}/bm25.pkl", "rb") as f:
        bm25 = pickle.load(f)
    return stds, d["tfidf"], d["matrix"], bm25

STANDARDS, TFIDF, TFIDF_MX, BM25 = _load()

# ── Utility 
def normalize_id(s: str) -> str:
    """Strips spaces/punctuation for fuzzy IS-code matching."""
    return re.sub(r'[\s\(\)\.\-:]+', '', str(s)).lower()

def expand_query(query: str) -> str:
    """Appends domain synonym expansions to the query."""
    q = query.lower()
    extras = [v for k, v in QUERY_EXPANSIONS.items() if k in q]
    return (query + " " + " ".join(extras)).strip() if extras else query

# ── Core retrieval 
def hybrid_retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Hybrid BM25 + TF-IDF retrieval with query expansion.
    Returns top_k candidate standards sorted by fused relevance score.
    """
    q_exp  = expand_query(query)
    tokens = q_exp.lower().split()

    # BM25 (exact / keyword match strength)
    b_scores = np.array(BM25.get_scores(tokens))
    b_norm   = (b_scores - b_scores.min()) / (b_scores.max() - b_scores.min() + 1e-9)

    # TF-IDF cosine (phrase / n-gram semantic overlap)
    q_vec    = TFIDF.transform([q_exp])
    t_scores = cosine_similarity(q_vec, TFIDF_MX).flatten()
    t_norm   = (t_scores - t_scores.min()) / (t_scores.max() - t_scores.min() + 1e-9)

    # Fusion
    fused  = ALPHA * b_norm + (1 - ALPHA) * t_norm
    top_ix = np.argsort(fused)[::-1][:top_k]

    return [
        {**STANDARDS[i], "score": round(float(fused[i]), 4)}
        for i in top_ix
    ]

# ── Rationale generation (Claude API)
def _build_context(candidates: list[dict]) -> str:
    parts = []
    for c in candidates[:6]:
        snippet = re.sub(r'\s+', ' ', c["content"])[:350]
        parts.append(f"[{c['id']}] {c['title']}\n{snippet}")
    return "\n\n".join(parts)

SYSTEM_PROMPT = """You are a BIS (Bureau of Indian Standards) compliance expert helping Indian MSE manufacturers.

Given a product description and candidate standards from SP 21, select the TOP 3–5 most relevant standards and explain WHY each one applies.

STRICT RULES:
- Only recommend standards from the provided candidate list — never invent IS numbers
- Use exact IS codes as shown (e.g. "IS 269: 1989")
- Keep each rationale to 1–2 clear sentences a factory owner can understand
- Respond ONLY with valid JSON — no markdown fences, no extra text

Format:
{"recommendations": [{"standard": "IS XXX: YYYY", "title": "...", "rationale": "..."}, ...]}"""

def generate_rationale(query: str, candidates: list[dict]) -> list[dict] | None:
    """Calls Groq (Llama 3) to rank candidates and generate plain-English rationales."""
    context = _build_context(candidates)
    user_msg = (
        f"Product / Query: {query}\n\n"
        f"Candidate Standards from SP 21:\n{context}\n\n"
        "Return the top 3-5 most applicable standards as JSON."
    )
    try:
        from groq import Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
        chat = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}
            ],
            max_tokens=900,
            temperature=0.1
        )
        raw = re.sub(r'```json|```', '', chat.choices[0].message.content).strip()
        return json.loads(raw).get("recommendations", [])
    except Exception as e:
        print(f"Groq error: {e}")
        return None

def fallback_rationale(candidates: list[dict]) -> list[dict]:
    """Used when API is unavailable — returns retrieval-based summaries."""
    out = []
    for c in candidates[:5]:
        snippet = re.sub(r'\s+', ' ', c["content"])[:200].strip()
        out.append({
            "standard":  c["id"],
            "title":     c["title"],
            "rationale": f"[Retrieval score: {c['score']:.3f}] {snippet}…",
            "confidence": c["score"]
        })
    return out

# ── Post-validation
def validate_recommendations(recs: list[dict], candidates: list[dict]) -> list[dict]:
    """
    Anti-hallucination guard: drops any IS code not present in retrieved candidates.
    The LLM should never add codes outside the candidate list, but this ensures it.
    """
    valid_ids = {normalize_id(c["id"]) for c in candidates}
    clean = [r for r in recs if normalize_id(r.get("standard", "")) in valid_ids]

    # Attach confidence score from retrieval
    score_map = {normalize_id(c["id"]): c["score"] for c in candidates}
    for r in clean:
        r["confidence"] = score_map.get(normalize_id(r["standard"]), 0.0)

    return clean

# ── Main pipeline
def recommend(query: str, use_llm: bool = True) -> dict:
    """
    Full pipeline:
      1. Query expansion (abbreviation → full term)
      2. Hybrid BM25 + TF-IDF retrieval
      3. Claude API rationale generation (or fallback)
      4. Anti-hallucination post-validation
    """
    t0 = time.time()

    candidates    = hybrid_retrieve(query)
    recommendations = generate_rationale(query, candidates) if use_llm else None

    if recommendations is None:
        recommendations = fallback_rationale(candidates)
    else:
        recommendations = validate_recommendations(recommendations, candidates)
        if not recommendations:           # paranoia: if all were hallucinated
            recommendations = fallback_rationale(candidates)

    return {
        "query":                query,
        "retrieved_standards":  [r["standard"] for r in recommendations],
        "recommendations":      recommendations,
        "latency_seconds":      round(time.time() - t0, 3),
    }

# ── CLI
def _print_result(result: dict):
    print(f"\nQuery   : {result['query']}")
    print(f"Latency : {result['latency_seconds']}s\n")
    for i, r in enumerate(result["recommendations"], 1):
        conf = f"  [confidence: {r.get('confidence', 0):.3f}]" if r.get("confidence") else ""
        print(f"  {i}. {r['standard']} — {r['title']}")
        print(f"     ↳ {r['rationale']}{conf}\n")

def main():
    parser = argparse.ArgumentParser(description="BIS Standards Recommendation Engine")
    parser.add_argument("--query",   type=str, help="Single product description")
    parser.add_argument("--batch",   type=str, help="JSON file with test queries")
    parser.add_argument("--output",  type=str, default="results.json")
    parser.add_argument("--no-llm",  action="store_true", help="Skip Claude API, use retrieval only")
    args = parser.parse_args()

    use_llm = not args.no_llm

    if args.query:
        _print_result(recommend(args.query, use_llm=use_llm))

    elif args.batch:
        with open(args.batch) as f:
            tests = json.load(f)

        results = []
        for t in tests:
            print(f"  {t['id']}…", end=" ", flush=True)
            r = recommend(t["query"], use_llm=use_llm)
            results.append({
                "id":                   t["id"],
                "query":                t["query"],
                "expected_standards":   t.get("expected_standards", []),
                "retrieved_standards":  r["retrieved_standards"],
                "recommendations":      r["recommendations"],
                "latency_seconds":      r["latency_seconds"],
            })
            print(f"{r['latency_seconds']}s")

        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved → {args.output}")
        print("   Run:  python eval_script.py --results", args.output)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
