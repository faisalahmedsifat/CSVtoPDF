import os
import tkinter as tk
from tkinter import filedialog


def browse_path():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    return path


def browse_folder():
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory()
    return folder


def run_script(csv_file, output_folder_path):
    # Run the Python script with the CSV file location as an argument
    os.system(f"python script.py {csv_file} {output_folder_path}")
    tk.messagebox.showinfo(title="Task Completed",
                           message="The conversion is complete!")


# Create a window with file selection buttons and a "Run Script" button
root = tk.Tk()
root.title("CSV to PDF Converter")
root.geometry("300x150")
root.eval('tk::PlaceWindow . center')

csv_file = None
output_folder_path = None


def select_file():
    global csv_file
    csv_file = browse_path()


def select_folder():
    global output_folder_path
    output_folder_path = browse_folder()


csv_button = tk.Button(root, text="Select CSV File", command=select_file)
csv_button.pack(pady=10)

output_button = tk.Button(
    root, text="Select Output Folder", command=select_folder)
output_button.pack(pady=10)

run_button = tk.Button(root, text="Run Script",
                       command=lambda: run_script(csv_file, output_folder_path))
run_button.pack(pady=10)



root.mainloop()
