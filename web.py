from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import os
import pandas as pd
import pdfkit
from jinja2 import Environment, FileSystemLoader
import tempfile
import datetime
from fastapi.middleware.cors import CORSMiddleware  # Import CORS middleware

app = FastAPI()


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Define the template rendering function
def render_template(row_dict, previous_month, house_num):
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("template.html")
    
    rendered_template = template.render(
        room_num=row_dict.get('Room No.', ''),
        previous_month=previous_month,
        meter_no=row_dict.get('Meter No.', ''),
        present_units=row_dict.get('present units', ''),
        previous_units=row_dict.get('[previous] Units T.', ''),
        units=row_dict.get('[present] UNITS', ''),
        electric_bill=row_dict.get('[present] BILL', ''),
        gas_bill=row_dict.get('Gas Bill', ''),
        service_charge=row_dict.get('Service Charge', ''),
        rent=row_dict.get('Rent', ''),
        previous_due=row_dict.get('Previous Due', ''),
        advance_paid=row_dict.get('Paid', ''),
        comments="",
        total_bill=row_dict.get('TOTAL W. OC', ''),
        house_num=str(house_num)
    )
    return rendered_template

# Main route to generate PDF
@app.post("/generate_pdf/")
async def generate_pdf(csv_file: UploadFile = File(...)):

    # Read the uploaded CSV file
    df = pd.read_csv(csv_file.file)

    # Date and formatting logic
    today = datetime.date.today()
    first_day_of_month = datetime.date(today.year, today.month, 1)
    last_day_of_previous_month = first_day_of_month - datetime.timedelta(days=1)
    previous_month = last_day_of_previous_month.strftime("%B")

    now = datetime.datetime.now()
    one_month_ago = now - datetime.timedelta(days=30)
    month = one_month_ago.strftime("%B")[:3]
    year = str(one_month_ago.year)[2:]
    formatted_date = f"{month}'{year}"

    # Create a directory for storing HTML and PDF files
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)  # Create the output directory if it doesn't exist
    html_files = []
    house_num = 220

    # Iterate over each row of the dataframe
    for index, row in df.iterrows():

        # Skip rows where 'Room No.' is missing or contains '3BC'
        room_no = row.get('Room No.', '')
        if pd.isna(room_no) or room_no == '3BC':
            continue

        if index >= 17:
            house_num = 226

        # Generate the HTML file for the row
        html_content = render_template(row, previous_month, house_num)
        html_file_path = os.path.join(output_dir, f"{room_no}_{house_num}_{formatted_date}.html")
        with open(html_file_path, 'w') as f:
            f.write(html_content)
        html_files.append(html_file_path)

    # Generate the PDF from the HTML files
    output_pdf = os.path.join(output_dir, f"all_bills_{formatted_date}.pdf")
    path_wkhtmltopdf = r'C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

    options = {
        'page-size': 'A4',
        'zoom': 2,
    }

    try:
        # Attempt to generate the PDF
        pdfkit.from_file(html_files, output_pdf, options=options, configuration=config)
    except OSError as e:
        return {"error": f"PDF generation failed: {str(e)}"}

    # Ensure the file exists before returning it
    if os.path.exists(output_pdf):
        return FileResponse(output_pdf, media_type='application/pdf', filename=f'all_bills_{formatted_date}.pdf')
    else:
        return {"error": "PDF file was not created successfully"}
