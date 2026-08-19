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
    """
    Return the nested key structure of a dict.
    Values are ignored.

    Example:
        {"a": {"b": 1}, "c": 2}

    becomes:
        (("a", ("b",)), ("c",))
    """
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
    if not dicts:
        return True

    signature = dict_signature(dicts[0])
    return all(dict_signature(d) == signature for d in dicts[1:])

def render_dict(d, level=0):
    """Render a single nested dict."""

    rows = []

    for key, value in d.items():
        label = key

        if isinstance(value, dict):
            content = render_dict(value, level + 1)

            rows.append(f"""
            <tr class="section-row level-{level}">
                <th colspan="2">{escape(label)}</th>
            </tr>
            {content}
            """)

        elif isinstance(value, list):
            content = "".join(
                f"<li>{escape(str(v))}</li>"
                for v in value
            )

            rows.append(f"""
            <tr>
                <td class="label">{escape(label)}</td>
                <td class="value"><ul>{content}</ul></td>
            </tr>
            """)

        else:
            rows.append(f"""
            <tr>
                <td class="label">{escape(label)}</td>
                <td class="value">
                    {escape(fmt_value(key, value))}
                </td>
            </tr>
            """)

    return "\n".join(rows)

def render_compare(d1, d2, names=("Value 1", "Value 2"), level=0):
    """Render two dictionaries side-by-side."""

    rows = []

    for key, value1 in d1.items():
        value2 = d2[key]

        if isinstance(value1, dict):
            content = render_compare(
                value1,
                value2,
                names=names,
                level=level + 1,
            )

            rows.append(f"""
            <tr class="section-row level-{level}">
                <th colspan="3">{escape("000---")}</th>
            </tr>
            {content}
            """)

        elif isinstance(value1, list):
            left = ", ".join(str(v) for v in value1)
            right = ", ".join(str(v) for v in value2)

            rows.append(f"""
            <tr>
                <td class="label">{"---"}</td>
                <td>{escape(left)}</td>
                <td>{escape(right)}</td>
            </tr>
            """)

        else:
            rows.append(f"""
            <tr>
                <td class="label">{escape(key)}</td>
                <td>{escape(fmt_value(key, value1))}</td>
                <td>{escape(fmt_value(key, value2))}</td>
            </tr>
            """)

    return f"""
    <table class="dict-table">
        <thead>
            <tr>
                <th>{escape(key)}</th>
                <th>{escape(names[0])}</th>
                <th>{escape(names[1])}</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """

def dict_to_html(*dicts, names=None, output=None):
    """
    Render one or two dictionaries as HTML.

    One dict:
        dict_to_html(data)

    Two matching dicts:
        dict_to_html(data1, data2)

    Two matching dicts with column names:
        dict_to_html(
            data1,
            data2,
            names=("Samsung", "SK Hynix")
        )
    """

    if not dicts:
        raise ValueError("At least one dictionary is required")

    if len(dicts) > 2:
        raise ValueError("Maximum of two dictionaries supported")

    if not all(isinstance(d, dict) for d in dicts):
        raise TypeError("All arguments must be dictionaries")

    if names is None:
        names = ("Value 1", "Value 2")

    if len(dicts) == 1:
        content = f"""
        <table class="dict-table">
            <tbody>
                {render_dict(dicts[0])}
            </tbody>
        </table>
        """

    else:
        if same_signature(*dicts):
            content = render_compare(
                dicts[0],
                dicts[1],
                names=names,
            )
        else:
            # Different structures: render separately
            content = f"""
            <div class="dict-container">
                <h2>{escape(names[0])}</h2>
                <table class="dict-table">
                    <tbody>
                        {render_dict(dicts[0])}
                    </tbody>
                </table>
            </div>

            <div class="dict-container">
                <h2>{escape(names[1])}</h2>
                <table class="dict-table">
                    <tbody>
                        {render_dict(dicts[1])}
                    </tbody>
                </table>
            </div>
            """

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

dict_to_html(sa.assess_data, output='a.html')
dict_to_html(sa.assess_data, sb.assess_data, names=['sa', 'sb'], output='b.html')