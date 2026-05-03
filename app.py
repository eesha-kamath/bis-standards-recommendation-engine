"""
BIS Standards Recommendation Engine - app.py
Gradio web UI for demo and presentation.
"""
import gradio as gr
import json
from inference import recommend


EXAMPLE_QUERIES = [
    "We manufacture 33 Grade Ordinary Portland Cement for residential construction.",
    "Our factory produces hollow lightweight concrete masonry blocks for partition walls.",
    "We need to comply with standards for precast concrete drainage pipes.",
    "Setting up production of Portland Pozzolana Cement using fly ash.",
    "Manufacturing corrugated asbestos cement roofing sheets.",
    "We produce Portland Slag Cement using blast furnace slag.",
    "Our plant makes White Portland Cement for architectural finishing.",
    "Looking for standards on supersulphated cement for marine construction.",
    "We make OPC 43 grade cement for structural concrete applications.",
    "Need standard for masonry cement used in brick-laying mortar.",
]


def confidence_label(score: float) -> str:
    if score >= 0.7:
        return "High"
    elif score >= 0.4:
        return "Medium"
    return "Low"


def badge_color(label: str) -> str:
    return {
        "High":   "background:#703B3B; color:#E1D0B3;",
        "Medium": "background:#A18D6D; color:#E1D0B3;",
        "Low":    "background:#C8B99A; color:#3d2b2b;",
    }.get(label, "")


def format_results_html(result: dict) -> str:
    recs = result["recommendations"]
    latency = result["latency_seconds"]

    summary = f"""
    <div class="res-summary">
        <span class="res-count">{len(recs)} standards found</span>
        <span class="res-latency">processed in {latency:.2f}s</span>
    </div>
    """

    cards = ""
    for i, r in enumerate(recs, 1):
        conf = r.get("confidence", 0)
        label = confidence_label(conf)
        bc = badge_color(label)
        rationale = r.get("rationale", "").strip()
        cards += f"""
        <div class="res-card">
            <div class="res-card-top">
                <span class="res-index">{i}</span>
                <div class="res-card-meta">
                    <div class="res-standard">{r['standard']}</div>
                    <div class="res-title">{r['title']}</div>
                </div>
                <span class="res-badge" style="{bc}">{label} &nbsp; {conf:.0%}</span>
            </div>
            {f'<div class="res-rationale">{rationale}</div>' if rationale else ''}
        </div>
        """

    return summary + cards if cards else "<p style='color:#A18D6D; padding:12px 0;'>No standards matched. Try rephrasing your description.</p>"


def format_checklist_md(result: dict) -> str:
    recs = result["recommendations"]
    lines = [
        "## Compliance Checklist",
        "",
        "Steps to begin your BIS certification process:",
        "",
    ]
    for r in recs:
        lines += [
            f"**{r['standard']}**",
            "",
            f"- [ ] Obtain the standard document from the BIS portal (https://bis.gov.in)",
            f"- [ ] Review scope and confirm applicability to your product",
            f"- [ ] Go through testing and certification requirements",
            f"- [ ] Apply for BIS licence under the IS Mark scheme",
            "",
        ]
    lines += [
        "---",
        "BIS standard documents can be purchased at https://www.bis.gov.in or through the BIS One app.",
    ]
    return "\n".join(lines)


def format_json_output(result: dict) -> str:
    out = {
        "query": result["query"],
        "retrieved_standards": result["retrieved_standards"],
        "latency_seconds": result["latency_seconds"],
        "recommendations": result["recommendations"],
    }
    return json.dumps(out, indent=2)


def run_query(query: str, use_llm: bool) -> tuple:
    if not query.strip():
        return "<p style='color:#A18D6D;padding:12px 0;'>Please enter a product description.</p>", "", ""
    result = recommend(query.strip(), use_llm=use_llm)
    return (
        format_results_html(result),
        format_checklist_md(result),
        format_json_output(result),
    )


THEME = gr.themes.Base(
    font=[gr.themes.GoogleFont("DM Sans"), "ui-sans-serif", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("DM Mono"), "ui-monospace", "monospace"],
    primary_hue=gr.themes.colors.stone,
    neutral_hue=gr.themes.colors.stone,
).set(
    body_background_fill="#E1D0B3",
    block_background_fill="#E1D0B3",
    block_border_width="0px",
    block_label_text_color="#5a3d3d",
    button_primary_background_fill="#703B3B",
    button_primary_background_fill_hover="#5a2f2f",
    button_primary_text_color="#E1D0B3",
    input_background_fill="#f5ede0",
    input_border_color="#C8B99A",
    input_border_width="1.5px",
    panel_background_fill="#E1D0B3",
    shadow_drop="none",
    checkbox_background_color="#f5ede0",
    checkbox_background_color_selected="#703B3B",
    checkbox_border_color="#A18D6D",
)

CUSTOM_CSS = """
/* --- base --- */
html, body, .gradio-container, .main, footer {
    background: #E1D0B3 !important;
    color: #3d2b2b !important;
}

/* --- header --- */
.app-header {
    background: #703B3B;
    border-radius: 12px;
    padding: 32px 38px;
    margin-bottom: 24px;
}
.app-header h1 {
    font-size: 1.7rem;
    font-weight: 700;
    color: #E1D0B3;
    margin: 0 0 8px 0;
    letter-spacing: -0.02em;
}
.app-header p {
    font-size: 0.97rem;
    color: #c9aa99;
    margin: 0;
    line-height: 1.6;
}

/* --- two-column row --- */
.main-row {
    gap: 20px !important;
    align-items: stretch !important;
}
.main-row > div {
    align-self: stretch !important;
}

/* --- left panel card --- */
.left-panel {
    background: #EDE3CE;
    border: 1px solid #C8B99A;
    border-radius: 12px;
    padding: 24px 26px;
    display: flex;
    flex-direction: column;
    gap: 0;
    height: 100%;
    box-sizing: border-box;
}

/* --- input box --- */
.main-input textarea {
    font-size: 0.97rem !important;
    line-height: 1.65 !important;
    color: #3d2b2b !important;
    background: #faf6ef !important;
    border-color: #C8B99A !important;
    border-radius: 8px !important;
}
.main-input label span {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    color: #5a3d3d !important;
    letter-spacing: 0.01em;
}

/* --- submit button row --- */
.action-row {
    margin-top: 12px;
    display: flex;
    align-items: center;
    gap: 14px;
}
.submit-btn > button {
    height: 46px !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    min-width: 200px;
}
.llm-toggle label {
    font-size: 0.86rem !important;
    color: #5a3d3d !important;
}

/* --- section label --- */
.section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #703B3B;
    margin: 22px 0 10px 0;
}

/* --- example query blocks --- */
.example-links {
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.example-links button {
    font-size: 0.87rem !important;
    font-family: 'DM Sans', sans-serif !important;
    text-align: left !important;
    justify-content: flex-start !important;
    color: #3d2b2b !important;
    background: #D9C9A8 !important;
    border: 1px solid #C8B99A !important;
    padding: 9px 14px !important;
    border-radius: 7px !important;
    box-shadow: none !important;
    transition: background 0.15s, border-color 0.15s;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.example-links button:hover {
    background: #cfc0a0 !important;
    border-color: #A18D6D !important;
    color: #3d2b2b !important;
}

/* --- info panel (right) --- */
.info-panel {
    background: #9BB4C0;
    border-radius: 12px;
    padding: 26px 28px;
    height: 100%;
    box-sizing: border-box;
}
.info-panel h3 {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #1e2e36;
    margin: 0 0 12px 0;
    opacity: 0.75;
}
.info-panel li {
    font-size: 0.93rem;
    color: #1e2e36;
    line-height: 1.75;
    margin-bottom: 2px;
}
.info-panel ul {
    padding-left: 18px;
    margin: 0 0 6px 0;
}

.badge-row {
    display: flex;
    flex-direction: column;
    gap: 7px;
    margin-top: 12px;
}
.badge {
    font-size: 0.82rem;
    font-weight: 600;
    padding: 6px 13px;
    border-radius: 6px;
    display: inline-block;
    width: fit-content;
}
.badge-high   { background: #703B3B; color: #E1D0B3; }
.badge-medium { background: #A18D6D; color: #E1D0B3; }
.badge-low    { background: #C8B99A; color: #3d2b2b; }

.info-note {
    font-size: 0.78rem;
    color: #1e2e36;
    margin-top: 18px;
    opacity: 0.6;
    line-height: 1.55;
}

/* --- tabs --- */
.tab-nav {
    border-bottom: 2px solid #C8B99A !important;
    margin-top: 8px !important;
}
.tab-nav button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    color: #A18D6D !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 10px 22px !important;
    border-radius: 0 !important;
    margin-bottom: -2px;
}
.tab-nav button.selected {
    color: #703B3B !important;
    border-bottom: 2px solid #703B3B !important;
    background: transparent !important;
}

/* --- result summary line --- */
.res-summary {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 16px;
    padding-top: 4px;
}
.res-count {
    font-size: 1rem;
    font-weight: 700;
    color: #703B3B;
}
.res-latency {
    font-size: 0.8rem;
    color: #A18D6D;
}

/* --- result cards --- */
.res-card {
    background: #faf6ef;
    border: 1px solid #C8B99A;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 12px;
}
.res-card-top {
    display: flex;
    align-items: flex-start;
    gap: 14px;
}
.res-index {
    font-size: 0.78rem;
    font-weight: 700;
    color: #faf6ef;
    background: #703B3B;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 2px;
}
.res-card-meta {
    flex: 1;
}
.res-standard {
    font-size: 0.95rem;
    font-weight: 700;
    color: #3d2b2b;
    margin-bottom: 3px;
}
.res-title {
    font-size: 0.85rem;
    color: #7a6050;
    line-height: 1.45;
}
.res-badge {
    font-size: 0.75rem;
    font-weight: 700;
    padding: 4px 11px;
    border-radius: 5px;
    white-space: nowrap;
    flex-shrink: 0;
}
.res-rationale {
    font-size: 0.88rem;
    color: #4a3535;
    line-height: 1.7;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #DDD0BB;
}

/* --- checklist tab --- */
.checklist-out .prose {
    font-size: 0.93rem !important;
    line-height: 1.8 !important;
    color: #3d2b2b !important;
}

/* --- json output --- */
.json-out code, .json-out pre {
    font-size: 0.83rem !important;
    background: #EDE3CE !important;
    color: #3d2b2b !important;
}

/* --- footer --- */
.app-footer {
    border-top: 1px solid #C8B99A;
    margin-top: 20px;
    padding-top: 14px;
    font-size: 0.76rem;
    color: #8a7060;
    line-height: 2;
}
"""

with gr.Blocks(
    theme=THEME,
    css=CUSTOM_CSS,
    title="BIS Standards Recommendation Engine",
) as demo:

    gr.HTML("""
    <div class="app-header">
        <h1>BIS Standards Recommendation Engine</h1>
        <p>
            Find applicable Indian Standards (IS) for your product using the SP 21 compendium.
            Built for MSE manufacturers. Describe your product and get relevant standards instantly.
        </p>
    </div>
    """)

    with gr.Row(elem_classes=["main-row"]):

        with gr.Column(scale=3, elem_classes=["left-panel"]):
            query_box = gr.Textbox(
                label="Product or process description",
                placeholder="e.g. We manufacture 33 Grade Ordinary Portland Cement for residential construction.",
                lines=5,
                elem_classes=["main-input"],
            )

            with gr.Row(elem_classes=["action-row"]):
                use_llm_toggle = gr.Checkbox(
                    label="Generate plain-English rationales (requires Grok API key)",
                    value=False,
                    scale=3,
                    elem_classes=["llm-toggle"],
                )
                submit_btn = gr.Button(
                    "Find Applicable Standards",
                    variant="primary",
                    scale=2,
                    elem_classes=["submit-btn"],
                )

            gr.HTML('<div class="section-label">Example queries</div>')
            with gr.Column(elem_classes=["example-links"]):
                example_btns = []
                for eq in EXAMPLE_QUERIES[:6]:
                    display = eq[:80] + "..." if len(eq) > 80 else eq
                    btn = gr.Button(display, size="sm")
                    example_btns.append((btn, eq))

        with gr.Column(scale=2):
            gr.HTML("""
            <div class="info-panel">
                <h3>How it works</h3>
                <ul>
                    <li>Describe your product or manufacturing process</li>
                    <li>The system searches across 566 IS standards from SP 21</li>
                    <li>Returns the top 3 to 5 standards with relevance scores</li>
                    <li>All IS codes are verified against the SP 21 index</li>
                </ul>

                <h3 style="margin-top: 24px;">Relevance levels</h3>
                <div class="badge-row">
                    <span class="badge badge-high">High &nbsp; 70% and above</span>
                    <span class="badge badge-medium">Medium &nbsp; 40 to 70%</span>
                    <span class="badge badge-low">Low &nbsp; below 40%</span>
                </div>

                <p class="info-note">
                    No invented standards are returned. Results are constrained to verified SP 21 entries only.
                </p>
            </div>
            """)

    with gr.Tabs():
        with gr.Tab("Recommendations"):
            results_html = gr.HTML(
                "<p style='color:#A18D6D; padding: 8px 0; font-size:0.93rem;'>Results will appear here after you submit a query.</p>"
            )
        with gr.Tab("Compliance Checklist"):
            checklist_md = gr.Markdown(
                "Submit a query to generate a checklist.",
                elem_classes=["checklist-out"],
            )
        with gr.Tab("JSON Output"):
            json_out = gr.Code(
                language="json",
                label="Raw output",
                elem_classes=["json-out"],
            )

    gr.HTML("""
    <div class="app-footer">
        Data source: SP 21 : 2005, BIS Compendium of Indian Standards on Building Materials.
        &nbsp;&nbsp; Retrieval: Hybrid BM25 + TF-IDF with query expansion and alias enrichment.
        &nbsp;&nbsp; Generation: Claude Haiku constrained to retrieved candidates only.
    </div>
    """)

    submit_btn.click(
        run_query,
        inputs=[query_box, use_llm_toggle],
        outputs=[results_html, checklist_md, json_out],
    )

    for btn, eq in example_btns:
        btn.click(lambda q=eq: q, outputs=query_box)


if __name__ == "__main__":
    demo.launch(share=False, server_port=7860)