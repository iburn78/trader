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



def dict_to_html(data: dict, output=None, title=None):


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
