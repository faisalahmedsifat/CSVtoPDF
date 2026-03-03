"""
Cross-platform PDF generation using wkhtmltopdf via direct subprocess.
Uses a single merged HTML file (with CSS page-break-after) so that
wkhtmltopdf only receives ONE input file — this avoids the multi-file bug
present in some wkhtmltopdf 0.12.6 builds on WSL/Linux.
"""
import os
import shutil
import platform
import tempfile
import subprocess
from jinja2 import Environment, FileSystemLoader
import datetime

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..")
TEMPLATE_FILE = "template.html"


def _find_wkhtmltopdf() -> str:
    env_path = os.getenv("WKHTMLTOPDF_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    found = shutil.which("wkhtmltopdf")
    if found:
        return found

    if platform.system() == "Windows":
        for c in [
            r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
            r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
        ]:
            if os.path.isfile(c):
                return c

    if platform.system() == "Darwin":
        for c in ["/usr/local/bin/wkhtmltopdf", "/opt/homebrew/bin/wkhtmltopdf"]:
            if os.path.isfile(c):
                return c

    raise RuntimeError(
        "wkhtmltopdf not found. "
        "Run the install_wkhtmltopdf script for your OS, or set WKHTMLTOPDF_PATH env var."
    )


def _call_wkhtmltopdf(binary: str, single_html: str, out_pdf: str) -> None:
    """Call wkhtmltopdf with a single HTML file. Clears DISPLAY on Linux/WSL."""
    env = os.environ.copy()
    if platform.system() == "Linux":
        env.pop("DISPLAY", None)  # headless—no X server needed

    cmd = [binary, "--quiet", "--page-size", "A4", "--zoom", "2", single_html, out_pdf]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)

    if result.returncode != 0:
        raise OSError(
            f"wkhtmltopdf exited with code {result.returncode}.\n"
            f"stderr: {result.stderr.strip()}"
        )


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


# CSS page-break wrapper — each room gets its own page in the PDF
PAGE_WRAPPER = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  .page-break {{ page-break-after: always; }}
  .page-break:last-child {{ page-break-after: avoid; }}
</style>
</head>
<body>
{pages}
</body>
</html>"""


def generate_pdf_for_month(rooms_data: list[dict], year: int, month: int) -> bytes:
    """
    Render all room bills into one merged HTML, then convert to PDF.
    Returns raw PDF bytes.
    """
    binary = _find_wkhtmltopdf()

    billing_date = datetime.date(year, month, 1)
    previous_month_name = billing_date.strftime("%B")
    short_month = billing_date.strftime("%b")[:3]
    short_year = str(year)[2:]
    formatted_date = f"{short_month}'{short_year}"

    with tempfile.TemporaryDirectory() as tmpdir:
        # Render each room's HTML (body content only) and wrap with page-break divs
        page_sections = []
        for room in rooms_data:
            html = _render_room_html(room, previous_month_name, room["building_num"])
            # Extract just the <body> content from each rendered template
            page_sections.append(f'<div class="page-break">{html}</div>')

        merged_html = PAGE_WRAPPER.format(pages="\n".join(page_sections))

        merged_path = os.path.join(tmpdir, f"merged_{formatted_date}.html")
        with open(merged_path, "w", encoding="utf-8") as f:
            f.write(merged_html)

        out_pdf = os.path.join(tmpdir, f"all_bills_{formatted_date}.pdf")
        _call_wkhtmltopdf(binary, merged_path, out_pdf)

        with open(out_pdf, "rb") as f:
            return f.read()
