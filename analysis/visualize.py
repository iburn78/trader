#%%
from html import escape
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent / "templates"

def fmt_value(key, value):
    if value is None:
        return "-"

    if isinstance(value, bool):
        return "✓" if value else "✗"

    if isinstance(value, float):
        if "(pct)" in key.lower() or "(%)" in key.lower():
            return f"{value:.2%}"
        return f"{value:,.6g}"

    if isinstance(value, int):
        return f"{value:,}"

    return str(value)


def get_value(data, *keys, default="-"):
    """Drill down a nested dict using the given key chain."""
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key)

    return default if data is None else data

def dict_signature(data):
    """Return the nested key structure of a dict. Values are ignored."""

    if not isinstance(data, dict):
        return ()

    return tuple(
        (
            key,
            dict_signature(value) if isinstance(value, dict) else None
        )
        for key, value in data.items()
    )

def same_signature(*dicts):
    """Return True if all dictionaries have the same nested structure."""
    if len(dicts) < 2:
        return True

    signature = dict_signature(dicts[0])
    return all(dict_signature(d) == signature for d in dicts[1:])

def section_row(key, level=0, colspan=1):
    return f"""    <tr class="section-row level-{level}">
        <td class="label" colspan="{colspan}">{escape(str(key))}</td>
    </tr>
"""

def table_row(key, values=[], row_class="", level=0):
    cells = "\n".join(
        f'        <td class="value">{escape(fmt_value(key, v))}</td>'
        for v in values
    )

    return f"""    <tr class="{row_class} level-{level}">
        <td class="label">{escape(str(key))}</td>
{cells}
    </tr>
"""

def render_rows(dict_list, level=0):
    """Flatten nested dictionaries into table rows."""
    rows = []

    for key, value in dict_list[0].items():
        values = [d[key] for d in dict_list]

        if isinstance(value, dict):
            # Dictionary = section/header row
            rows.append(
                section_row(
                    key,
                    level=level,
                    colspan=len(dict_list)+1
                )
            )

            rows.extend(
                render_rows(values, level=level + 1)
            )

        else:
            rows.append(
                table_row(
                    key,
                    values,
                    row_class="value-row",
                    level=level,
                )
            )

    return rows

def render_compare(dict_name, column_names, dict_list):
    rows = render_rows(dict_list)

    header = f"""    <tr class="header-row">
        <th class="label">{escape(str(dict_name))}</th>
        {"".join(
            f'<th class="value">{escape(str(name))}</th>'
            for name in column_names
        )}
    </tr>
"""

    return f"""
<table class="dict-table">
    <thead>
{header}    </thead>
    <tbody>
{"".join(rows)}    </tbody>
</table>
"""


def dict_to_html(column_names: list, dict_list: list, output=None):
    if not dict_list:
        raise ValueError("dict_list cannot be empty")

    if len(column_names) != len(dict_list):
        raise ValueError("column_names and dict_list must have the same length")

    if not same_signature(*dict_list):
        raise ValueError("signatures not matching")

    content = render_compare(
        "overall",
        column_names,
        dict_list,
    )

    template = (
        TEMPLATE_DIR / "assessment.html"
    ).read_text(encoding="utf-8")

    html = template.replace(
        "{{ content }}",
        content,
    )

    if output:
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html, encoding="utf-8")

    return html


from trader.analysis.sector_analysis import SectorAnalysis

code = '005930'
sa = SectorAnalysis()
sa.process_code(code)
sa.plot()
sa.print()

code = '000660'
sb = SectorAnalysis()
sb.process_code(code)
sb.plot()
sb.print()

dict_to_html(['sa'], [sa.assess_data], output='a.html')
dict_to_html(['sa', 'b', 'c'], [sa.assess_data, sb.assess_data, sa.assess_data], output='b.html')
