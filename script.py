# Generate pdf from every rows in the csv file
# Usage: python script.py <csv file> <output folder>
# Example: python script.py data.csv output

import csv
import sys
import os
import pdfkit
import string
from jinja2 import Environment, FileSystemLoader

import datetime


def include_html_template(row_dict):
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("template.html")

   # Render the template with the row_dict data
    rendered_template = template.render(room_num=row_dict['Room No.'], previous_month=previous_month, meter_no=row_dict['Meter No.'], present_units=row_dict['present units'], previous_units=row_dict['[previous] Units T.'], units=row_dict['[present] UNITS'], electric_bill=row_dict['[present] BILL'],
                                            gas_bill=row_dict['Gas Bill'], service_charge=row_dict['Service Charge'], rent=row_dict['Rent'], previous_due=row_dict['Previous Due'], advance_paid=row_dict['Paid'], comments="", total_bill=row_dict['TOTAL W. OC'], house_num=str(house_num))
    # print(rendered_template)
    return rendered_template


# Check if the number of arguments is correct
if len(sys.argv) != 3:
    print("Usage: python script.py <csv file> <output folder>")
    sys.exit(1)

# Check if the csv file exists
if not os.path.isfile(sys.argv[1]):
    print("The csv file does not exist")
    sys.exit(1)

# Check if the output folder exists
if not os.path.isdir(sys.argv[2]):
    print("The output folder does not exist")
    sys.exit(1)


today = datetime.date.today()
first_day_of_month = datetime.date(today.year, today.month, 1)
last_day_of_previous_month = first_day_of_month - datetime.timedelta(days=1)
previous_month = last_day_of_previous_month.strftime("%B")

now = datetime.datetime.now()
one_month_ago = now - datetime.timedelta(days=30)
month = one_month_ago.strftime("%B")[:3]
year = str(one_month_ago.year)[2:]

formatted_date = f"{month}'{year}"


csv_file = sys.argv[1]
output_folder = sys.argv[2]
field_names = []

# Open the csv file
with open(csv_file, 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')

    # Read every row
    for row in reader:

        # Save the field names from the first line
        if reader.line_num == 1:
            field_names = row
            continue

        house_num = 220

        # after 17 occurance , the house number will be 221
        if reader.line_num > 17:
            house_num = 226

        # Create a dictionary from the row
        row_dict = dict(zip(field_names, row))

        # Create a html file for each row
        # if row_dict['Room No.'] is null then skip the row or if the row_dict['Room No.'] == '3BC' then skip the row:
        if row_dict['Room No.'] == '' or row_dict['Room No.'] == '3BC':
            continue
        html_file = os.path.join(
            output_folder, row_dict['Room No.'] + '_' + str(house_num) + '_' + formatted_date + '.html')
        print('Generating ' + html_file)
        with open(html_file, 'w') as f:
            updated_template = include_html_template(row_dict)
            f.write(updated_template)
        # show progress
        print('Progress: ' + str(reader.line_num) + ' rows completed')

# list all the html files in the output folder
html_files = [f for f in os.listdir(output_folder) if f.endswith('.html')]

options = {
    'page-size': 'A4',
    'zoom': 2,
}

# print some spaces to make the output more readable
print('\n\n')

all_files_paths = []


# Combine 2 html files into 1 pdf file in landscape A4 size
for i in range(0, len(html_files)):
    all_files_paths.append(os.path.join(output_folder, html_files[i]))


output_file = os.path.join(
    output_folder, 'all_bills_' + formatted_date + '.pdf')
print('Generating pdf for all bills...')

path_wkhtmltopdf = r'C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

pdfkit.from_file(all_files_paths, output_file, options=options, configuration=config)

# remove all the html files
for i in range(0, len(html_files)):
    os.remove(os.path.join(output_folder, html_files[i]))


print("Done")



