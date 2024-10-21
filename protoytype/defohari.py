import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import sys
import os
import time
import pdb

# print
class PrintLogger:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)

    def write(self, message):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message + '\n')
        self.text_widget.see(tk.END)  
        self.text_widget.config(state=tk.DISABLED)

    def flush(self):
        pass  

# execute subroutine
def run_subroutine(command, update_progress):
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in iter(process.stdout.readline, ''):
            print(line.strip())
            time.sleep(0.1)
        process.stdout.close()
        process.wait()
        if process.returncode != 0:
            print(f"Error: {process.stderr.read()}")
        update_progress()
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")

# GUI Class
class ArtifactExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Defohari Artifact Extracter")
        
        # Progress bar
        self.progress_label = tk.Label(root, text="Progress : ")
        self.progress_label.pack(pady=10)
        
        # Progress Label
        self.current_task_label = tk.Label(root, text="Waiting...", font=("Helvetica", 12))
        self.current_task_label.pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=600, mode="determinate")
        self.progress_bar.pack(pady=10)
        
        # output(print)
        self.output_text = tk.Text(root, height=30, width=80)
        self.output_text.pack(pady=10)
        
        # Start Button
        self.start_button = tk.Button(root, text="Extract Start", command=self.start_extraction)
        self.start_button.pack(pady=10)
        
        self.subroutines = [
            ('Extracting & Processing web artifacts...', ['python', r'subroutine\web\web_complete.py']),
            ('Extracting & Processing  prefetch artifacts...', ['python', r'subroutine\prefetch\prefetch_complete.py']),
            ('Extracting & Processing  event artifacts...', ['python', r'subroutine\event_log\evt_complete.py']),
            ('Extracting & Processing  MFTJ artifacts...', ['python', r'subroutine\MFTJ\mftJ_complete.py']),
            ('Extracting & Processing LNK artifacts...', ['python', r'subroutine\LNK\LNK_complete.py']),
            ('Combinding CSV files...', ['python', 'csv_totaler.py'])
        ]
        self.total_tasks = len(self.subroutines)
        
        self.progress_bar["maximum"] = 100

    # subroutine start
    def start_extraction(self):
        pl = PrintLogger(self.output_text)
        sys.stdout = pl
        
        threading.Thread(target=self.run_subroutines).start()

    # run subroutine
    def run_subroutines(self):
        for task_name, command in self.subroutines:
            self.update_task_label(f"{task_name}")
            print(f"Command Execution : {' '.join(command)}")
            run_subroutine(command, self.update_progress)
        print("All tasks complete.")
        self.update_task_label("Done ! Check your combined_analysis.xlsx")

    # label update
    def update_task_label(self, task_name):
        self.current_task_label.config(text=task_name)
        self.root.update_idletasks()

    # Progress update
    def update_progress(self):
        progress_increment = 100 / self.total_tasks
        self.progress_bar["value"] += progress_increment
        self.root.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = ArtifactExtractorApp(root)
    root.geometry("800x600")
    root.mainloop()
