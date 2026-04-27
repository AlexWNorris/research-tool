"""
Graphical user interface tool using Tkinter to manage decryption, processing, 
and graphical plot output generation for the research toolset.
"""
import file_handler
import email_finder
from data_handler import PilotDataHandler
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

def main():
    """
    Initialize the Tkinter GUI interface logic and event loop.
    """
    root = tk.Tk()
    root.title("Researcher Hub Tool")
    root.geometry("550x300")

    notebook = ttk.Notebook(root)
    notebook.pack(pady=10, expand=True, fill='both')

    # --- Decryption Tab ---
    tab_decrypt = ttk.Frame(notebook)
    notebook.add(tab_decrypt, text="Decryption")

    decrypt_input_var = tk.StringVar()
    decrypt_output_var = tk.StringVar()

    def select_decrypt_input():
        folder = filedialog.askdirectory(title="Select Encrypted Data Folder")
        if folder:
            decrypt_input_var.set(folder)

    def select_decrypt_output():
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            decrypt_output_var.set(folder)

    def run_decryption():
        input_dir = decrypt_input_var.get()
        output_dir = decrypt_output_var.get()
        
        if not input_dir or not output_dir:
            messagebox.showerror("Error", "Please select both input and output folders.")
            return

        try:
            file_handler.populate_decrypted_folder_from(input_dir, output_dir)
            messagebox.showinfo("Success", "Files successfully decrypted and saved.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{e}")

    tk.Label(tab_decrypt, text="Encrypted Data Folder:").pack(pady=(10, 0))
    frame_d_in = tk.Frame(tab_decrypt)
    frame_d_in.pack(pady=5)
    tk.Entry(frame_d_in, textvariable=decrypt_input_var, width=50).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_d_in, text="Browse", command=select_decrypt_input).pack(side=tk.LEFT)

    tk.Label(tab_decrypt, text="Output Folder:").pack(pady=(10, 0))
    frame_d_out = tk.Frame(tab_decrypt)
    frame_d_out.pack(pady=5)
    tk.Entry(frame_d_out, textvariable=decrypt_output_var, width=50).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_d_out, text="Browse", command=select_decrypt_output).pack(side=tk.LEFT)

    tk.Button(tab_decrypt, text="Run Decryption", command=run_decryption, bg="green", fg="white", font=("Helvetica", 10, "bold")).pack(pady=20)


    # --- Statistics Tab ---
    tab_stats = ttk.Frame(notebook)
    notebook.add(tab_stats, text="Statistics")

    stats_input_var = tk.StringVar()
    stats_output_var = tk.StringVar()

    def select_stats_input():
        folder = filedialog.askdirectory(title="Select Decrypted Data Folder")
        if folder:
            stats_input_var.set(folder)

    def select_stats_output():
        folder = filedialog.askdirectory(title="Select Output Folder for Plots")
        if folder:
            stats_output_var.set(folder)

    def run_statistics():
        input_dir = stats_input_var.get()
        output_dir = stats_output_var.get()
        
        if not input_dir or not output_dir:
            messagebox.showerror("Error", "Please select both data and output folders.")
            return

        try:
            handler = PilotDataHandler(data_dir=input_dir)
            handler.plot_all_demographics(output_dir=output_dir)
            
            # Run the newly integrated boundary shift analysis
            import advanced_eda
            advanced_eda.OUTPUT_DIR = output_dir
            df = advanced_eda.load_data(input_dir)
            advanced_eda.analyze_boundary_entropy(df)
            
            messagebox.showinfo("Success", "Statistics generated and plots saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{e}")

    tk.Label(tab_stats, text="Decrypted Data Folder:").pack(pady=(10, 0))
    frame_s_in = tk.Frame(tab_stats)
    frame_s_in.pack(pady=5)
    tk.Entry(frame_s_in, textvariable=stats_input_var, width=50).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_s_in, text="Browse", command=select_stats_input).pack(side=tk.LEFT)

    tk.Label(tab_stats, text="Plots Output Folder:").pack(pady=(10, 0))
    frame_s_out = tk.Frame(tab_stats)
    frame_s_out.pack(pady=5)
    tk.Entry(frame_s_out, textvariable=stats_output_var, width=50).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_s_out, text="Browse", command=select_stats_output).pack(side=tk.LEFT)

    tk.Button(tab_stats, text="Generate Statistics", command=run_statistics, bg="blue", fg="white", font=("Helvetica", 10, "bold")).pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()