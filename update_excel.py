# A python script to take a text file and input it into an excel file

import pandas as pd
import os
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

# Function to browse for a file
def browse_path():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(filetypes=[("Excel File", "*.xlsx")])
    return path

# Function to browse for a folder
def browse_folder():
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory()
    return folder

# take text file and input it into an excel file
def browse_text():
    root = tk.Tk()
    root.withdraw()
    text = filedialog.askopenfilename(filetypes=[("Text File", "*.txt")])
    return text

# read the xlxs file
def read_xlxs(excel_file):
    global df
    df = pd.read_excel(excel_file)
    
    
# read the text file
def read_text(text_file):
    global text
    text = open(text_file, "r")
    text = text.read()
    for i in range(len(text)):
        print(text[i])

        text[i] = text[i].split(" - ")


text_file = browse_text()
read_text(text_file)
print(text)

first_building = []
second_building = []
is_first = True

for i in range(len(text)):
    if(text[i][0] == "2nd building"):
        is_first = False
        continue
    if is_first:
        first_building.append(text[i])
    else:
        second_building.append(text[i])
        
print("first building...") 
print(first_building)

print('second building...')
print(second_building)
        


    
    
