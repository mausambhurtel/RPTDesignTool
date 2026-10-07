import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import warnings
from PIL import Image, ImageTk
from project_io import parse_design_info_text, apply_project_values, validate_project_values

class tab1_content(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.gv = app.gv
        self.create_widgets()
        self.pack(expand=True, fill="both")

    def create_widgets(self):
        # Keep the whole page and transparent logo on one uniform background.
        background = "#ffffff"
        self.configure(background=background)

        ttl_logo_path = Path(__file__).resolve().with_name("ttl_logo.png")
        wpl_logo_path = Path(__file__).resolve().with_name("wpl_logo.png")
        # The bundled logos are high resolution; only keep display-sized copies.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            with Image.open(ttl_logo_path) as logo:
                logo.thumbnail((155, 120), Image.Resampling.LANCZOS)
                self.ttl_logo_image = ImageTk.PhotoImage(logo, master=self)
            with Image.open(wpl_logo_path) as logo:
                logo.thumbnail((180, 120), Image.Resampling.LANCZOS)
                self.wpl_logo_image = ImageTk.PhotoImage(logo, master=self)

        ttl_logo_label = tk.Label(
            self,
            image=self.ttl_logo_image,
            background=background,
            borderwidth=0,
            highlightthickness=0
        )
        ttl_logo_label.place(relx=0.45, rely=0.30, anchor="center")

        wpl_logo_label = tk.Label(
            self,
            image=self.wpl_logo_image,
            background=background,
            borderwidth=0,
            highlightthickness=0
        )
        wpl_logo_label.place(relx=0.55, rely=0.30, anchor="center")

        title_label = tk.Label(
            self,
            text="RPTDesignTool",
            font=("TkDefaultFont", 28),
            foreground="#202020",
            background=background,
            borderwidth=0,
            highlightthickness=0
        )
        title_label.place(relx=0.5, rely=0.5, anchor="center")


        # New Project Button
        new_project_button = ttk.Button(self, text="New Project", width=24, padding=(12, 8), style="TButton", command=self.app.next_page)
        new_project_button.place(relx=1 / 3, rely=0.72, anchor="center")

        # Upload Project Button
        upload_project_button = ttk.Button(self, text="Upload Project", width=24, padding=(12, 8), style="TButton", command=self.upload_project)
        upload_project_button.place(relx=2 / 3, rely=0.72, anchor="center")

    def upload_project(self):
        file_path = filedialog.askopenfilename(title="Select Project File", filetypes=[("Text Files", "*.txt")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as handle:
                    content = handle.read()
                values = parse_design_info_text(content)
                is_valid, missing = validate_project_values(values)
                if not is_valid:
                    missing_text = ", ".join(missing)
                    messagebox.showerror(
                        "Project Load Error",
                        f"Missing required values in project file:\n{missing_text}"
                    )
                    return
                apply_project_values(self.app, self.gv, values)
                if hasattr(self.app, "notebook") and hasattr(self.app, "tab2"):
                    try:
                        self.app.notebook.select(self.app.tab2)
                        self.app.update_navigation_visibility()
                    except Exception:
                        pass
                messagebox.showinfo("Project Loaded", f"Project file loaded:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Project Load Error", f"Failed to load project file:\n{str(e)}")
