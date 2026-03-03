"""
PDF generation using WeasyPrint — a pure-Python HTML→PDF library
with a modern CSS engine (flexbox, grid, @page all supported).

No external binary required. Install system deps once:
  sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf2.0-0
Then:
  pip install weasyprint
"""
import os
import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..")
TEMPLATE_FILE = "template.html"


def _render_room_html(row: dict, previous_month: str, house_num: int) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(TEMPLATE_FILE)
    return template.render(
        room_num=row["room_no"],
        previous_month=previous_month,
        meter_no=row.get("meter_no", ""),
        present_units=row["present_units"],
        previous_units=row["previous_units"],
        units=row["units_used"],
        electric_bill=row["electric_bill"],
        gas_bill=row["gas_bill"],
        service_charge=row["service_charge"],
        rent=row["rent"],
        previous_due=row["previous_due"],
        advance_paid=row["paid"],
        comments=row.get("comments", ""),
        total_bill=row["total_bill"],
        house_num=str(house_num),
    )


def generate_pdf_for_month(rooms_data: list[dict], year: int, month: int) -> bytes:
    """
    Render all room bills into one combined HTML document and convert to PDF.
    Each room gets its own A4 page (via CSS page-break-after).
    Returns raw PDF bytes.
    """
    billing_date = datetime.date(year, month, 1)
    previous_month_name = billing_date.strftime("%B")

    # Render each room and collect the <body> content
    pages_html = []
    for room in rooms_data:
        html = _render_room_html(room, previous_month_name, room["building_num"])
        pages_html.append(f'<div class="bill-page">{html}</div>')

    combined = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .bill-page {{ page-break-after: always; }}
    .bill-page:last-child {{ page-break-after: avoid; }}
  </style>
</head>
<body>
{"".join(pages_html)}
</body>
</html>"""

    # WeasyPrint renders from a string; base_url lets it resolve relative assets
    pdf_bytes = HTML(string=combined, base_url=TEMPLATE_DIR).write_pdf()
    return pdf_bytes
