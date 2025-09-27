#!/usr/bin/env python3
"""
JIM AI Desktop Launcher
User-friendly GUI for forensic data processing
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import webbrowser
from pathlib import Path
import time

class JIMAILauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("JIM AI - Forensic Document Analysis")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')

        # Variables
        self.selected_folder = tk.StringVar()
        self.process_running = False

        self.create_widgets()

    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.root, bg='#2563eb', height=80)
        title_frame.pack(fill='x', padx=10, pady=10)
        title_frame.pack_propagate(False)

        title_label = tk.Label(title_frame, text="🔍 JIM AI - Forensic Analysis",
                              font=('Arial', 20, 'bold'), fg='white', bg='#2563eb')
        title_label.pack(expand=True)

        subtitle_label = tk.Label(title_frame, text="Upload and analyze forensic evidence with AI",
                                 font=('Arial', 12), fg='#e2e8f0', bg='#2563eb')
        subtitle_label.pack()

        # Main content
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Web Interface Section
        web_frame = tk.LabelFrame(main_frame, text="📱 Quick Upload (Small Files)",
                                 font=('Arial', 12, 'bold'), bg='#f0f0f0', pady=10)
        web_frame.pack(fill='x', pady=(0, 20))

        tk.Label(web_frame, text="For documents, photos, and files under 100MB",
                font=('Arial', 10), bg='#f0f0f0').pack(pady=5)

        web_button = tk.Button(web_frame, text="🌐 Open Web Interface",
                              command=self.open_web_interface,
                              font=('Arial', 12, 'bold'), bg='#059669', fg='white',
                              padx=20, pady=10)
        web_button.pack(pady=10)

        # Large Data Section
        large_frame = tk.LabelFrame(main_frame, text="📱 Large Cell Phone Data",
                                   font=('Arial', 12, 'bold'), bg='#f0f0f0', pady=10)
        large_frame.pack(fill='x', pady=(0, 20))

        tk.Label(large_frame, text="For complete cell phone extractions (iPhone, Android)",
                font=('Arial', 10), bg='#f0f0f0').pack(pady=5)

        # Folder selection
        folder_frame = tk.Frame(large_frame, bg='#f0f0f0')
        folder_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(folder_frame, text="Select cell phone data folder:",
                font=('Arial', 10, 'bold'), bg='#f0f0f0').pack(anchor='w')

        folder_select_frame = tk.Frame(folder_frame, bg='#f0f0f0')
        folder_select_frame.pack(fill='x', pady=5)

        self.folder_entry = tk.Entry(folder_select_frame, textvariable=self.selected_folder,
                                    font=('Arial', 10), state='readonly')
        self.folder_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))

        browse_button = tk.Button(folder_select_frame, text="Browse...",
                                 command=self.browse_folder,
                                 font=('Arial', 10), bg='#6b7280', fg='white')
        browse_button.pack(side='right')

        # Process button
        self.process_button = tk.Button(large_frame, text="🚀 Process Large Data",
                                       command=self.process_large_data,
                                       font=('Arial', 12, 'bold'), bg='#dc2626', fg='white',
                                       padx=20, pady=10, state='disabled')
        self.process_button.pack(pady=10)

        # Progress section
        progress_frame = tk.LabelFrame(main_frame, text="📊 Processing Status",
                                      font=('Arial', 12, 'bold'), bg='#f0f0f0')
        progress_frame.pack(fill='both', expand=True)

        self.progress_var = tk.StringVar(value="Ready to process data...")
        self.progress_label = tk.Label(progress_frame, textvariable=self.progress_var,
                                      font=('Arial', 10), bg='#f0f0f0')
        self.progress_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill='x', padx=20, pady=5)

        # Console output
        self.console = scrolledtext.ScrolledText(progress_frame, height=12,
                                                font=('Courier', 9), bg='#1f2937', fg='#e5e7eb')
        self.console.pack(fill='both', expand=True, padx=10, pady=10)

        # Bottom buttons
        button_frame = tk.Frame(self.root, bg='#f0f0f0')
        button_frame.pack(fill='x', padx=20, pady=10)

        help_button = tk.Button(button_frame, text="❓ Help",
                               command=self.show_help,
                               font=('Arial', 10), bg='#6b7280', fg='white')
        help_button.pack(side='left')

        status_button = tk.Button(button_frame, text="📊 Check Status",
                                 command=self.check_status,
                                 font=('Arial', 10), bg='#059669', fg='white')
        status_button.pack(side='right')

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Cell Phone Data Folder")
        if folder:
            self.selected_folder.set(folder)
            self.process_button.config(state='normal')
            self.log_message(f"Selected folder: {folder}")

    def open_web_interface(self):
        try:
            webbrowser.open('http://localhost:8080')
            self.log_message("Opening web interface at http://localhost:8080")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open web browser: {e}")

    def process_large_data(self):
        if not self.selected_folder.get():
            messagebox.showerror("Error", "Please select a folder first")
            return

        if self.process_running:
            messagebox.showwarning("Warning", "Processing is already running")
            return

        # Confirm with user
        folder_path = self.selected_folder.get()
        result = messagebox.askyesno("Confirm Processing",
                                   f"Process all data in:\n{folder_path}\n\n"
                                   f"This may take several hours for large datasets.\n"
                                   f"Continue?")
        if not result:
            return

        # Start processing in background thread
        self.process_running = True
        self.process_button.config(state='disabled')
        self.progress_bar.start()
        self.progress_var.set("Processing large cell phone data...")

        threading.Thread(target=self._run_large_processor, daemon=True).start()

    def _run_large_processor(self):
        try:
            self.log_message("=" * 50)
            self.log_message("🚀 Starting large data processor...")
            self.log_message(f"📂 Processing: {self.selected_folder.get()}")
            self.log_message("=" * 50)

            # Change to project directory
            project_dir = os.path.dirname(os.path.abspath(__file__))

            # Run the large data processor
            cmd = [
                'python3', 'large-data-processor.py',
                self.selected_folder.get()
            ]

            # Set up environment
            env = os.environ.copy()
            env['PYTHONPATH'] = project_dir

            process = subprocess.Popen(
                cmd,
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                env=env
            )

            # Read output line by line
            for line in iter(process.stdout.readline, ''):
                if line:
                    self.log_message(line.strip())

            process.wait()

            if process.returncode == 0:
                self.log_message("=" * 50)
                self.log_message("✅ Processing completed successfully!")
                self.log_message("🌐 Open the web interface to start querying your data")
                self.log_message("=" * 50)
                self.progress_var.set("✅ Processing completed! Open web interface to query data.")

                # Ask if user wants to open web interface
                self.root.after(1000, self._ask_open_web)
            else:
                self.log_message("=" * 50)
                self.log_message("❌ Processing failed. Check the output above for errors.")
                self.log_message("=" * 50)
                self.progress_var.set("❌ Processing failed. Check console output.")

        except Exception as e:
            self.log_message(f"❌ Error: {str(e)}")
            self.progress_var.set(f"❌ Error: {str(e)}")
        finally:
            self.process_running = False
            self.root.after(0, self._reset_ui)

    def _ask_open_web(self):
        result = messagebox.askyesno("Processing Complete",
                                   "Data processing completed successfully!\n\n"
                                   "Would you like to open the web interface to start "
                                   "querying your forensic data?")
        if result:
            self.open_web_interface()

    def _reset_ui(self):
        self.progress_bar.stop()
        self.process_button.config(state='normal' if self.selected_folder.get() else 'disabled')

    def log_message(self, message):
        def _log():
            self.console.insert(tk.END, f"{message}\n")
            self.console.see(tk.END)
            self.root.update_idletasks()

        if threading.current_thread().name == 'MainThread':
            _log()
        else:
            self.root.after(0, _log)

    def check_status(self):
        try:
            # Check if Flask app is running
            import requests
            response = requests.get('http://localhost:8080/api/status', timeout=5)
            if response.status_code == 200:
                status_info = response.json()
                messagebox.showinfo("System Status",
                                  f"✅ JIM AI is running\n\n"
                                  f"Knowledge Base: {status_info['knowledge_base_id']}\n"
                                  f"Model: {status_info['model']}\n"
                                  f"Region: {status_info['region']}")
            else:
                messagebox.showwarning("Status Check", "JIM AI service is not responding properly")
        except:
            messagebox.showwarning("Status Check",
                                 "JIM AI service is not running.\n\n"
                                 "Please start the application first:\n"
                                 "python3 app.py")

    def show_help(self):
        help_text = """
🔍 JIM AI - Forensic Document Analysis

QUICK START:
1. For small files (documents, photos): Click "Open Web Interface"
2. For large cell phone data: Select folder and click "Process Large Data"

SUPPORTED DATA:
• Cell phone extractions (iPhone, Android)
• SQLite databases (messages, contacts, calls)
• Documents (PDF, DOCX, TXT)
• Images and archives (ZIP, TAR)

FILE SIZE LIMITS:
• Web Interface: Up to 100MB per file
• Large Data Processor: No limit (handles 150GB+ extractions)

PROCESSING TIME:
• Small files: 5-15 minutes
• Large extractions: 3-6 hours

SYSTEM REQUIREMENTS:
• Internet connection for AWS upload
• 8GB+ RAM recommended for large datasets
• Sufficient disk space (3x source data size)

For technical support, see LARGE_DATA_GUIDE.md
        """

        help_window = tk.Toplevel(self.root)
        help_window.title("JIM AI Help")
        help_window.geometry("600x500")
        help_window.configure(bg='#f0f0f0')

        help_text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD,
                                                    font=('Arial', 10), bg='white')
        help_text_widget.pack(fill='both', expand=True, padx=20, pady=20)
        help_text_widget.insert('1.0', help_text)
        help_text_widget.config(state='disabled')

def main():
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        messagebox.showerror("Error",
                           "Please run this launcher from the JIM AI project directory\n"
                           "The directory should contain app.py and other project files.")
        return

    root = tk.Tk()
    app = JIMAILauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()