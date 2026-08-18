from html import escape
from pathlib import Path


TEMPLATE_DIR = Path(__file__).parent / "templates"


def fmt_value(key, value):
    """Format a value for HTML display."""

    if value is None:
        return "-"

    if isinstance(value, bool):
        return "✓" if value else "✗"

    if isinstance(value, float):
        key = key.lower()

        if any(x in key for x in ("growth", "margin", "pct", "rate")):
            return f"{value:.2%}"

        return f"{value:,.6g}"

    if isinstance(value, int):
        return f"{value:,}"

    return str(value)


def get_value(data, *keys, default="-"):
    """Safely retrieve a nested value."""
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key)

    return default if data is None else data


def render_table(companies, sections):
    """
    Render comparison table.

    companies:
        list of company assessment dictionaries

    sections:
        [
            ("Section name", [
                ("Row label", callable),
                ...
            ])
        ]
    """

    headers = "".join(
        f"<th>{escape(str(c['meta'].get('name', '-')))}"
        f"<br><small>{escape(str(c['meta'].get('code', '-')))}</small></th>"
        for c in companies
    )

    rows = []

    for section_name, metrics in sections:

        rows.append(f"""
        <tr class="section-row">
            <th colspan="{len(companies) + 1}">
                {escape(section_name)}
            </th>
        </tr>
        """)

        for label, getter in metrics:
            cells = []

            for company in companies:
                value = getter(company)

                formatted = fmt_value(label, value)

                # Simple highlighting
                if isinstance(value, bool):
                    css_class = "positive" if value else "negative"
                elif isinstance(value, str) and value.lower() in (
                    "outperform",
                    "positive",
                ):
                    css_class = "positive"
                elif isinstance(value, str) and value.lower() in (
                    "underperform",
                    "negative",
                ):
                    css_class = "negative"
                else:
                    css_class = ""

                cells.append(
                    f'<td class="{css_class}">'
                    f'{escape(formatted)}'
                    f'</td>'
                )

            rows.append(
                f"""
                <tr>
                    <td class="metric">{escape(label)}</td>
                    {''.join(cells)}
                </tr>
                """
            )

    return f"""
    <table class="company-table">
        <thead>
            <tr>
                <th>Metric</th>
                {headers}
            </tr>
        </thead>

        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """


def render_assessments(data, output=None):
    """
    Render multiple company assessments as a comparison HTML report.

    Parameters
    ----------
    data : list[dict]
        List of company assessment dictionaries.

    output : str | Path | None
        Output HTML file.

    Returns
    -------
    str
        Generated HTML.
    """

    if isinstance(data, dict):
        data = [data]

    if not data:
        raise ValueError("No assessment data provided")

    # ---------------------------------------------------------
    # Define what should appear in the report
    # ---------------------------------------------------------

    sections = [

        (
            "Assessment",
            [
                (
                    "Alpha Level",
                    lambda d: get_value(
                        d, "assess_result", "alpha_level"
                    ),
                ),
                (
                    "Market Sentiment",
                    lambda d: get_value(
                        d, "assess_result", "market_sentiment"
                    ),
                ),
                (
                    "Category",
                    lambda d: get_value(
                        d, "assess_result", "category"
                    ),
                ),
            ],
        ),

        (
            "Operating Income",
            [
                (
                    "Positive Last 4Q",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "opincome_health",
                        "positive_last_4qtrs",
                    ),
                ),
                (
                    "Higher Than Comp",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "opincome_health",
                        "higher_than_comp",
                    ),
                ),
                (
                    "Slope",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "opincome_health",
                        "slope",
                    ),
                ),
                (
                    "Growth / Quarter",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "opincome_health",
                        "growth_per_qtr",
                    ),
                ),
            ],
        ),

        (
            "Operating Margin",
            [
                (
                    "25_3Q",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "opmargin_last_4qtrs",
                        "25_3Q",
                    ),
                ),
                (
                    "25_4Q",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "opmargin_last_4qtrs",
                        "25_4Q",
                    ),
                ),
                (
                    "26_1Q",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "opmargin_last_4qtrs",
                        "26_1Q",
                    ),
                ),
                (
                    "26_2Q",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "opmargin_last_4qtrs",
                        "26_2Q",
                    ),
                ),
            ],
        ),

        (
            "Valuation",
            [
                (
                    "PER LTM",
                    lambda d: get_value(
                        d, "assess_data", "PER", "PER_ltm"
                    ),
                ),
                (
                    "PER Q×4",
                    lambda d: get_value(
                        d, "assess_data", "PER", "PER_qx4"
                    ),
                ),
                (
                    "PER FWD",
                    lambda d: get_value(
                        d, "assess_data", "PER", "PER_fwd"
                    ),
                ),
            ],
        ),

        (
            "Volatility",
            [
                (
                    "Measure / Base",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "volatility_pct",
                        "measure_to_base",
                    ),
                ),
                (
                    "Slope",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "volatility_pct",
                        "slope",
                    ),
                ),
            ],
        ),

        (
            "Trading Amount",
            [
                (
                    "Measure / Base",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "amount_daily",
                        "measure_to_base",
                    ),
                ),
                (
                    "Slope",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "amount_daily",
                        "slope",
                    ),
                ),
            ],
        ),

        (
            "Alpha / Beta",
            [
                (
                    "Alpha — From Start",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "alpha_beta",
                        "from_start_date",
                        "alpha",
                    ),
                ),
                (
                    "Beta — From Start",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "alpha_beta",
                        "from_start_date",
                        "beta",
                    ),
                ),
                (
                    "Alpha — Base Duration",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "alpha_beta",
                        "base_duration",
                        "alpha",
                    ),
                ),
                (
                    "Beta — Base Duration",
                    lambda d: get_value(
                        d,
                        "assess_data",
                        "alpha_beta",
                        "base_duration",
                        "beta",
                    ),
                ),
            ],
        ),
    ]

    # ---------------------------------------------------------
    # Render content
    # ---------------------------------------------------------

    content = render_table(data, sections)

    # ---------------------------------------------------------
    # Header information
    # ---------------------------------------------------------

    updated = get_value(
        data[0],
        "meta",
        "updated",
        default="",
    )

    title = "Stock Assessment"

    # ---------------------------------------------------------
    # Load external template
    # ---------------------------------------------------------

    template_file = TEMPLATE_DIR / "assessment.html"

    template = template_file.read_text(encoding="utf-8")

    html = (
        template
        .replace("{{ title }}", escape(title))
        .replace("{{ updated }}", escape(str(updated)))
        .replace("{{ content }}", content)
    )

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    if output is not None:
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html, encoding="utf-8")

    return html

#%%
