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

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
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


import io
from pypdf import PdfReader, PdfWriter, PageObject, Transformation

def generate_pdf_for_month(rooms_data: list[dict], year: int, month: int, two_up: bool = False) -> bytes:
    """
    Render all room bills into one combined HTML document and convert to PDF.
    If two_up is True, scales and merges every two A4 portrait pages into one A4 landscape page.
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
    @page {{ size: A4 portrait; margin: 0; }}
    .bill-page {{ page-break-after: always; }}
    .bill-page:last-child {{ page-break-after: avoid; }}
  </style>
</head>
<body>
{"".join(pages_html)}
</body>
</html>"""

    # WeasyPrint renders standard A4 portrait pages from template.html
    pdf_bytes = HTML(string=combined, base_url=TEMPLATE_DIR).write_pdf()

    if not two_up:
        return pdf_bytes

    # ── Convert to 2-up layout using pypdf ──
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    for i in range(0, len(reader.pages), 2):
        page1 = reader.pages[i]
        page2 = reader.pages[i+1] if i+1 < len(reader.pages) else None
        
        # Original A4 portrait dimensions
        w = float(page1.mediabox.width)
        h = float(page1.mediabox.height)
        
        # Create a blank Landscape A4 page (width=h, height=w)
        new_page = PageObject.create_blank_page(width=h, height=w)
        
        # The exact scale to fit portrait height(h) into landscape height(w) is w/h.
        scale_factor = w / h
        
        # Place page 1 on the left
        op1 = Transformation().scale(scale_factor, scale_factor)
        new_page.merge_transformed_page(page1, op1, expand=True)
        
        # Place page 2 on the right
        if page2:
            # We translate by precisely half of the landscape width, which is h / 2.0
            op2 = Transformation().scale(scale_factor, scale_factor).translate(h / 2.0, 0)
            new_page.merge_transformed_page(page2, op2, expand=True)
            
        # Re-enforce standard A4 Landscape dimensions on the final output page
        # just to ensure no weird bounding box expansion artifacts
        new_page.mediabox.lower_left = (0, 0)
        new_page.mediabox.upper_right = (h, w)
        new_page.cropbox.lower_left = (0, 0)
        new_page.cropbox.upper_right = (h, w)
            
        writer.add_page(new_page)

    out_buf = io.BytesIO()
    writer.write(out_buf)
    return out_buf.getvalue()
