#%% 
from trader.analysis.sector_analysis import SectorAnalysis
from scraper.models.valuechain import ValueChainManager

vc_name = "Electronics"
vm = ValueChainManager()
vc = vm.get_item(vc_name)

#1) need to add VC financials (save)
SectorAnalysis().process_valuechain(vm, vc)

for cp in vm.get_components(vc):
    # 2) generate sa for component itself
    SectorAnalysis().process_component(cp)

    # 3) generate sa for companies in the component
    for code in cp.get_codelist():
        SectorAnalysis().process_code(code)

#%% 
code = '005930'
sa = SectorAnalysis()
sa.process_code(code)
sa.plot()
sa.print()
print(sa.assess_data)

#%%
a = {}
a['meta'] = sa.meta
a['assess_data'] = sa.assess_data
a['assess_result'] = sa.assess_result

print(a)
dict_to_html(a, 'a.html')

#%%
from html import escape
from pathlib import Path

style = f'''
<style>
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        max-width: 1100px;
        margin: 40px auto;
        padding: 0 24px;
        background: #f5f6f8;
        color: #222;
    }}

    .header {{
        background: white;
        padding: 24px 28px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 1px 4px #ddd;
    }}

    .header h1 {{
        margin: 0 0 6px;
        font-size: 28px;
    }}

    .header .sub {{
        color: #777;
        font-size: 14px;
    }}

    .metadata {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 12px;
        margin-top: 20px;
    }}

    .meta-item {{
        background: #f7f7f7;
        padding: 12px;
        border-radius: 8px;
    }}

    .meta-label {{
        font-size: 12px;
        color: #888;
        margin-bottom: 4px;
    }}

    .meta-value {{
        font-weight: 600;
    }}

    .section {{
        background: white;
        margin: 18px 0;
        padding: 20px 24px;
        border-radius: 12px;
        box-shadow: 0 1px 4px #ddd;
    }}

    .section h2 {{
        margin: 0 0 16px;
        font-size: 19px;
        border-bottom: 1px solid #eee;
        padding-bottom: 10px;
    }}

    .row {{
        display: flex;
        padding: 9px 0;
        border-bottom: 1px solid #f0f0f0;
    }}

    .row:last-child {{
        border-bottom: none;
    }}

    .label {{
        width: 45%;
        color: #666;
    }}

    .value {{
        flex: 1;
        font-weight: 500;
    }}

    ul {{
        margin: 0;
        padding-left: 20px;
    }}

    .level-1 {{
        margin-left: 10px;
    }}

    .level-2 {{
        margin-left: 20px;
    }}
</style>
'''


def dict_to_html(data: dict, output=None, title=None):
    """Render nested assessment data as a readable HTML report."""

    def fmt_value(key, value):
        if isinstance(value, bool):
            return "✓" if value else "✗"

        if isinstance(value, float):
            # percentage-like fields
            if any(x in key.lower() for x in ("growth", "margin", "pct", "rate")):
                return f"{value:.2%}"
            return f"{value:,.6g}"

        if isinstance(value, int):
            return f"{value:,}"

        return str(value)

    def render_dict(d, level=0):
        rows = []

        for key, value in d.items():
            label = key.replace("_", " ").title() # capitalize first letter

            if isinstance(value, dict):
                # nested dict
                content = render_dict(value, level + 1)
                rows.append(f"""
                <section class="section level-{level}">
                    <h2>{escape(label)}</h2>
                    {content}
                </section>
                """)

            elif isinstance(value, list):
                content = "".join(
                    f"<li>{escape(str(v))}</li>" for v in value
                )
                rows.append(f"""
                <div class="row">
                    <div class="label">{escape(label)}</div>
                    <div class="value"><ul>{content}</ul></div>
                </div>
                """)

            else:
                rows.append(f"""
                <div class="row">
                    <div class="label">{escape(label)}</div>
                    <div class="value">{escape(fmt_value(key, value))}</div>
                </div>
                """)

        return "\n".join(rows)

    meta = data.get("meta", {})
    assess_data = data.get("assess_data", {})
    assess_result = data.get("assess_result", {})

    body_assess_data = render_dict(assess_data)
    body_assess_result = render_dict({'Assess Result':assess_result})

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{style}
</head>
<body>

<div class="header">
    <h2>{escape(str(meta.get("name")))} <small>({escape(str(meta.get("code")))})</small></h2>
    <div class="sub">Updated: {escape(str(meta.get("updated")))}</div>

    <div class="metadata">
"""

    for key, value in meta.items():
        if key in ("name", "code", "updated"):
            continue

        html += f"""
        <div class="meta-item">
            <div class="meta-label">{escape(key.replace("_", " ").title())}</div>
            <div class="meta-value">{escape(fmt_value(key, value))}</div>
        </div>
        """

    html += f"""
    </div>
</div>

{body_assess_data}
{body_assess_result}

</body>
</html>
"""
    if output:
        Path(output).write_text(html, encoding="utf-8")

    return html

# %%
