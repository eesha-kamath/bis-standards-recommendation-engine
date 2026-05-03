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
        "High":   "background:#36064D; color:#F7F6E5;",
        "Medium": "background:#DA4848; color:#F7F6E5;",
        "Low":    "background:#76D2DB; color:#1a1a2e;",
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

    return summary + cards if cards else "<p style='color:#76D2DB; padding:12px 0;'>No standards matched. Try rephrasing your description.</p>"


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
        return "<p style='color:#76D2DB;padding:12px 0;'>Please enter a product description.</p>", "", ""
    result = recommend(query.strip(), use_llm=use_llm)
    return (
        format_results_html(result),
        format_checklist_md(result),
        format_json_output(result),
    )



# Color system (self-chosen):
# --ink:      #1C2B2B  deep teal-black  -> primary text, header bg, index circles
# --ink-mid:  #2E4A4A  medium teal      -> section labels, active tab
# --sage:     #4A9E8E  sage teal        -> accents, info panel, badge-high
# --sage-lt:  #D4EDE9  pale sage        -> info panel bg, hover fills
# --stone:    #F3F2EE  warm off-white   -> page bg
# --card:     #FFFFFF  white            -> input, result cards
# --panel:    #EDECEA  light stone      -> left panel bg, example tiles
# --border:   #DDD9D3  stone border     -> all borders
# --muted:    #7A8F8E  muted teal-grey  -> subtitles, latency, footer
# --coral:    #C95F4A  warm coral       -> medium badge, section label accent

THEME = gr.themes.Base(
    font=[gr.themes.GoogleFont("DM Sans"), "ui-sans-serif", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("DM Mono"), "ui-monospace", "monospace"],
    primary_hue=gr.themes.colors.stone,
    neutral_hue=gr.themes.colors.stone,
).set(
    body_background_fill="#F3F2EE",
    block_background_fill="#F3F2EE",
    block_border_width="0px",
    block_label_text_color="#1C2B2B",
    button_primary_background_fill="#1C2B2B",
    button_primary_background_fill_hover="#2E4A4A",
    button_primary_text_color="#F3F2EE",
    input_background_fill="#ffffff",
    input_border_color="#DDD9D3",
    input_border_width="1.5px",
    panel_background_fill="#F3F2EE",
    shadow_drop="none",
    checkbox_background_color="#ffffff",
    checkbox_background_color_selected="#4A9E8E",
    checkbox_border_color="#DDD9D3",
)

CUSTOM_CSS = """
html, body, .gradio-container, .main, footer {
    background: #F3F2EE !important;
    color: #1C2B2B !important;
}

.app-header {
    background: #1C2B2B;
    border-radius: 14px;
    padding: 32px 38px;
    margin-bottom: 24px;
}
.app-header h1 {
    font-size: 1.65rem;
    font-weight: 700;
    color: #F3F2EE;
    margin: 0 0 8px 0;
    letter-spacing: -0.02em;
}
.app-header p {
    font-size: 0.96rem;
    color: #7AAEAA;
    margin: 0;
    line-height: 1.6;
}

.main-row {
    gap: 20px !important;
    align-items: stretch !important;
}
.main-row > div {
    align-self: stretch !important;
}

.left-panel {
    background: #EDECEA;
    border: 1px solid #DDD9D3;
    border-radius: 14px;
    padding: 24px 26px;
    display: flex;
    flex-direction: column;
    height: 100%;
    box-sizing: border-box;
}

.main-input textarea {
    font-size: 0.97rem !important;
    line-height: 1.65 !important;
    color: #1C2B2B !important;
    background: #ffffff !important;
    border-color: #DDD9D3 !important;
    border-radius: 8px !important;
}
.main-input label span {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    color: #2E4A4A !important;
    letter-spacing: 0.01em;
}

.submit-btn > button {
    height: 46px !important;
    font-size: 0.93rem !important;
    font-weight: 600 !important;
    border-radius: 9px !important;
    letter-spacing: 0.01em;
    min-width: 200px;
}

.llm-toggle label {
    font-size: 0.86rem !important;
    color: #2E4A4A !important;
}

.section-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #7A8F8E;
    margin: 22px 0 10px 0;
}

.example-links {
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.example-links button {
    font-size: 0.86rem !important;
    font-family: 'DM Sans', sans-serif !important;
    text-align: left !important;
    justify-content: flex-start !important;
    color: #2E4A4A !important;
    background: #E6E4E0 !important;
    border: 1px solid #DDD9D3 !important;
    padding: 9px 14px !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    transition: background 0.15s, border-color 0.15s, color 0.15s;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.example-links button:hover {
    background: #D4EDE9 !important;
    border-color: #4A9E8E !important;
    color: #1C2B2B !important;
}

.info-panel {
    background: #D4EDE9;
    border: 1px solid #B2D9D3;
    border-radius: 14px;
    padding: 26px 28px;
    height: 100%;
    box-sizing: border-box;
}
.info-panel h3 {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #2E4A4A;
    margin: 0 0 12px 0;
}
.info-panel li {
    font-size: 0.92rem;
    color: #1C2B2B;
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
    font-size: 0.8rem;
    font-weight: 600;
    padding: 5px 13px;
    border-radius: 6px;
    display: inline-block;
    width: fit-content;
    letter-spacing: 0.01em;
}
.badge-high   { background: #1C2B2B; color: #D4EDE9; }
.badge-medium { background: #C95F4A; color: #FEF0ED; }
.badge-low    { background: #B2D9D3; color: #1C2B2B; }

.info-note {
    font-size: 0.77rem;
    color: #4A7A76;
    margin-top: 18px;
    line-height: 1.55;
}

.tab-nav {
    border-bottom: 1.5px solid #DDD9D3 !important;
    margin-top: 10px !important;
}
.tab-nav button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    color: #7A8F8E !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 10px 22px !important;
    border-radius: 0 !important;
    margin-bottom: -1.5px;
    transition: color 0.15s;
}
.tab-nav button.selected {
    color: #2E4A4A !important;
    border-bottom: 2px solid #4A9E8E !important;
    background: transparent !important;
}
.tab-nav button:hover:not(.selected) {
    color: #2E4A4A !important;
}

.res-summary {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 16px;
    padding-top: 4px;
}
.res-count {
    font-size: 0.97rem;
    font-weight: 700;
    color: #1C2B2B;
}
.res-latency {
    font-size: 0.79rem;
    color: #7A8F8E;
}

.res-card {
    background: #ffffff;
    border: 1px solid #DDD9D3;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 10px;
    transition: border-color 0.15s;
}
.res-card:hover {
    border-color: #4A9E8E;
}
.res-card-top {
    display: flex;
    align-items: flex-start;
    gap: 14px;
}
.res-index {
    font-size: 0.76rem;
    font-weight: 700;
    color: #D4EDE9;
    background: #1C2B2B;
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
    color: #1C2B2B;
    margin-bottom: 3px;
}
.res-title {
    font-size: 0.84rem;
    color: #7A8F8E;
    line-height: 1.45;
}
.res-badge {
    font-size: 0.74rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 5px;
    white-space: nowrap;
    flex-shrink: 0;
    letter-spacing: 0.01em;
}
.res-rationale {
    font-size: 0.87rem;
    color: #2E4A4A;
    line-height: 1.72;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #EDECEA;
}

.checklist-out .prose {
    font-size: 0.93rem !important;
    line-height: 1.8 !important;
    color: #1C2B2B !important;
}

.json-out code, .json-out pre {
    font-size: 0.83rem !important;
    background: #EDECEA !important;
    color: #1C2B2B !important;
}

.app-footer {
    border-top: 1px solid #DDD9D3;
    margin-top: 20px;
    padding-top: 14px;
    font-size: 0.75rem;
    color: #7A8F8E;
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

            with gr.Row():
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
                "<p style='color:#76D2DB; padding: 8px 0; font-size:0.93rem;'>Results will appear here after you submit a query.</p>"
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