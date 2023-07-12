# Generate pdf from every rows in the csv file
# Usage: python script.py <csv file> <output folder>
# Example: python script.py data.csv output

import csv
import sys
import os
import pdfkit


import datetime


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
        
        #Save the field names from the first line
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
            f.write('<!DOCTYPE html> <html> <head> <title>Bill Template</title> <style> body { font-family: Arial, sans-serif; font-size: 14px; line-height: 1.5; margin: 0; padding: 0; } .container { max-width: 800px; margin: 0 auto; padding: 20px; } table { border-collapse: collapse; width: 100%; } table td, table th { border: 0px solid #ddd; padding: 8px; text-align: left; } /* Media queries */ @media screen and (max-width: 600px) { .container { max-width: 400px; padding: 10px; } table td, table th { font-size: 12px; padding: 5px; } } </style> </head> <body> <div class="container" style="text-align: center"> <h1>Bill</h1> <p> Hirajheel R/A, Road No-08, House No- <b>' + str(house_num) + '</b ><br />Siddhirganj, Narayanganj. </p> <table style="margin-top: 30px"> <tr> <td style="font-weight: bold"> Flat No : ' + row_dict['Room No.'] + ' </td> <td>Month : ' + previous_month + '</td> <td>Meter No : ' + row_dict['Meter No.'] + '</td> </tr> <tr> <td>Current Unit : ' + row_dict['present units'] + '</td> <td>Previous Unit : ' + row_dict['[previous] Units T.'] + '</td> <td>Total Unit: ' + row_dict['[present] UNITS'] + '</td> </tr> <tr> <td>Electric Bill: ' + row_dict[
                    '[present] BILL'] + '</td> <td>Gas Bill: ' + row_dict['Gas Bill'] + '</td> <td>Trash Bill : ' + row_dict['Trash Bill'] + '</td> </tr> <tr> <td>Rent : ' + row_dict['Rent'] + '</td> <td>Cleaning Bill : ' + row_dict['Jharu'] + '</td> <td></td> </tr> <tr> <td>Previous Due : ' + row_dict['Previous Due'] + '</td> </tr> <tr> <td>Advance Paid : ' + row_dict['Paid'] + '</td> </tr> <tr> <td>Total : ' + row_dict['TOTAL W. OC'] + '</td> <td></td> <td></td> </tr> <tr> <td>Comments :</td> </tr> <tr> <td></td> <td></td> <td style="text-align: right">Signature</td> </tr> </table> <hr /> <div style=" display: flex; flex-direction: row; justify-content: space-between; margin-top: 40px; padding: 8px; " > <div> <div style="font-weight: bold; text-align: left"> Flat No : ' + row_dict['Room No.'] + ' </div> <div style="margin-top: 10px; text-align: left"> Total Bill : ' + row_dict['TOTAL W. OC'] + ' </div> <div style="margin-top: 10px; text-align: left"> Month : ' + previous_month + ' </div> <!-- <div style="margin-top: 20px; text-align: right">Signature</div> --> </div> <div> <div style="margin-top: 60px; text-align: right">Signature</div> </div> </div> </div> </body> </html> ')
        
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
    

output_file = os.path.join(output_folder, 'all_bills_' + formatted_date + '.pdf')
print('Generating pdf for all bills...')
pdfkit.from_file(all_files_paths, output_file, options=options)

# remove all the html files
for i in range(0, len(html_files)):
    os.remove(os.path.join(output_folder, html_files[i]))


        
print("Done")