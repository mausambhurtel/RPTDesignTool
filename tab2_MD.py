import tkinter as tk
from tkinter import ttk, Frame
from tkinter import messagebox
import math as m
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from PIL import Image, ImageTk
from matplotlib.patches import FancyArrowPatch
from copy import copy
from dataclasses import dataclass


# Only these values belong to Main Dimensions. Later tabs add other keys to
# shared dictionaries (for example D_hub and guide-vane counts).
_MD_KEYS = {
    "heads": ("Hmax", "Hmin", "Hgross", "Hloss", "Hnp", "Hnt"),
    "flows": ("Qmax", "Qp", "Qt"),
    "speeds": ("nc", "nq_pc", "nq_t"),
    "z": ("rv", "pp"),
    "gd": ("D2", "B_hub", "D1", "B0"),
    "pump_in": ("u2_red", "u2", "cm2_red", "cm2", "beta2", "beta2_deg", "w2", "alpha2_deg"),
    "pump_out": (
        "u1_red", "u1", "cm1", "cm1_red", "cu1", "cu1_red", "wu1_red", "wu1",
        "c1", "w1", "beta1_actual", "beta1_actual_deg", "alpha1", "alpha1_deg",
        "slip_deg", "beta1_minus_slip_deg", "beta1_minus_slip", "cm1_slip",
        "u1_slip", "wu1_slip", "cu1_slip", "cm1_slip_red", "cu1_slip_red",
        "wu1_slip_red", "c1_slip", "w1_slip",
    ),
    "turbine_in": (
        "u1", "u1_red", "beta1", "beta1_deg", "cm1", "cm1_red", "cu1", "cu1_red",
        "wu1_red", "wu1", "alpha1", "alpha1_deg", "c1", "w1",
    ),
    "turbine_out": (
        "u2", "u2_red", "beta2", "beta2_deg", "cm2", "cm2_red", "cu2", "cu2_red",
        "w2", "w2_red", "alpha2", "alpha2_deg", "c2",
    ),
    "pm_other": ("speed_no", "RR", "power", "torque", "hs"),
    "tm_other": ("speed_no", "RR", "power", "torque", "hs"),
}
_MD_SCALARS = ("omega_pm", "omega_tm")
_INPUT_ENTRIES = ("pm_Hnp_entry", "pm_Qnp_entry", "tm_Hnt_entry", "Zrv_entry", "Zp_entry")


def _capture_md_values(gv):
    """Immutable full-precision values, independent of formatted table cells."""
    dictionaries = tuple(
        (name, tuple((key, getattr(gv, name)[key]) for key in keys))
        for name, keys in _MD_KEYS.items()
    )
    scalars = tuple((name, getattr(gv, name)) for name in _MD_SCALARS)
    return dictionaries, scalars


def _restore_md_values(gv, values):
    dictionaries, scalars = values
    for name, items in dictionaries:
        getattr(gv, name).update(items)
    for name, value in scalars:
        setattr(gv, name, value)


@dataclass(frozen=True)
class _ConditionSnapshot:
    values: tuple
    entries: tuple
    blade_length: float
    blade_length_text: str


class tab2_content(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.gv = app.gv
        self._conditions = {}
        self.active_condition_id = None
        self._syncing_selection = False
        self._syncing_scroll = False
        self.app.main_dimensions_tab = self
        self.frame()
        self.pack(expand=True, fill="both")
        self.app.bind("<Configure>", self.update_column_widths, add="+")

    def frame(self):
        # Define a style for buttons
        style = ttk.Style()
        style.theme_use("clam")
        #style.configure("TButton", font=("Arial", 10, "bold"))

        # Create frames for different sections with fixed sizes
        input_frame = ttk.Frame(self, relief="ridge", padding=5)
        pm_vt_frame = ttk.Frame(self, relief="ridge", padding=5)
        tm_vt_frame = ttk.Frame(self, relief="ridge", padding=5)
        image_frame = ttk.Frame(self, relief="flat")
        calculated_data_frame = ttk.Frame(self, relief="ridge", padding=5)

        # Arrange the frames using grid
        pm_vt_frame.grid(row=0, column=1, rowspan=2, sticky="nsew")
        tm_vt_frame.grid(row=0, column=2, rowspan=2, sticky="nsew")
        input_frame.grid(row=0, column=0, sticky="nsew")
        image_frame.grid(row=1, column=0, sticky="nsew")
        calculated_data_frame.grid(row=2, column=0, columnspan=3, sticky="nsew")

        # Configure grid weights to ensure fixed positioning
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        

        # Defining Labels and Entries for Input Data
        ttk.Label(input_frame, text="Input Values", font=("Arial", 12)).grid(row=0, column=0, columnspan=2, padx=5, pady=10, sticky="n")

        ttk.Label(input_frame, text="PM Net Head (m):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.app.pm_Hnp_entry = ttk.Entry(input_frame, width=10)
        self.app.pm_Hnp_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="we")

        ttk.Label(input_frame, text="PM Max Discharge (m³/s):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.app.pm_Qnp_entry = ttk.Entry(input_frame, width=10)
        self.app.pm_Qnp_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="we")

        ttk.Label(input_frame, text="TM Net Head (m):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.app.tm_Hnt_entry = ttk.Entry(input_frame, width=10)
        self.app.tm_Hnt_entry.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky="we")

        ttk.Label(input_frame, text="No. of Blades:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.app.Zrv_entry = ttk.Entry(input_frame, width=10)
        self.app.Zrv_entry.grid(row=5, column=1, columnspan=2, padx=5, pady=5, sticky="we")

        ttk.Label(input_frame, text="No. of Poles:").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        self.app.Zp_entry = ttk.Entry(input_frame, width=10)
        self.app.Zp_entry.grid(row=7, column=1, columnspan=2, padx=5, pady=5, sticky="we")

        # SLIDER
        ttk.Label(input_frame, text="Max. Blade Length:").grid(row=9, column=0, padx=5, pady=5, sticky="w")
        self.app.max_blade_length = tk.DoubleVar(value=1)
        self.app.max_blade_length_str = tk.StringVar(value=f"{self.app.max_blade_length.get():.2f}")
        slider = ttk.Scale(input_frame, from_=0, to=1, orient="horizontal", variable=self.app.max_blade_length, command=lambda e: self.app.max_blade_length_str.set(f"{self.app.max_blade_length.get():.2f}"))
        slider.grid(row=9, column=1, padx=5, pady=5, sticky="we")
        value_label = ttk.Label(input_frame, textvariable=self.app.max_blade_length_str)
        value_label.grid(row=9, column=2, padx=5, pady=5, sticky="w")

        # Buttons inside button_frame
        ttk.Button(input_frame, text="Calculate", command=lambda: calculate_vt(self.app, self.gv)).grid(row=11, column=0, columnspan=3, padx=5, pady=50, sticky="nsew")

        # Load meridional image file
        image_path = 'meridional.png'
        image = Image.open(image_path)
        image = image.resize((300, 150), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(image)
        image_frame.configure(width=300, height=150)
        image_frame.grid_propagate(False)
        
        image_label = ttk.Label(image_frame, image=self.photo)
        image_label.place(relx=0.5, rely=0.5, anchor='center')

        # Inlet Velocity Triangle frame
        ttk.Label(pm_vt_frame, text="Pump Mode Velocity Triangle", font=("Arial", 12)).pack(pady=5)

        # Outlet Velocity Triangle frame
        ttk.Label(tm_vt_frame, text="Turbine Mode Velocity Triangle", font=("Arial", 12)).pack(pady=5)

        # Creating VT plotting canvas in their respective frame >> matplotlibbing velocity triangles directly in the respective frames doesn't work here, so
        self.app.pm_canvas = ttk.Frame(pm_vt_frame)
        self.app.pm_canvas.pack(fill="both", expand=True)
        self.app.pm_canvas.propagate(False)

        self.app.tm_canvas = ttk.Frame(tm_vt_frame)
        self.app.tm_canvas.pack(fill="both", expand=True)
        self.app.tm_canvas.propagate(False)

        # Create sub-frames for data sections
        self.pump_data_frame = ttk.LabelFrame(calculated_data_frame, text="Pump Mode")
        self.turbine_data_frame = ttk.LabelFrame(calculated_data_frame, text="Turbine Mode")
        self.dimensions_data_frame = ttk.LabelFrame(calculated_data_frame, text="Main Dimensions")

        # Grid sub-frames side by side
        self.pump_data_frame.grid(row=0, column=0, sticky="nsew")
        self.turbine_data_frame.grid(row=0, column=1, sticky="nsew")
        self.dimensions_data_frame.grid(row=0, column=2, sticky="nsew")

        # Configure row and column weights for resizing
        calculated_data_frame.grid_columnconfigure(0, weight=1)
        calculated_data_frame.grid_columnconfigure(1, weight=1)
        calculated_data_frame.grid_columnconfigure(2, weight=1)
        calculated_data_frame.grid_rowconfigure(0, weight=1)

        # Define table columns
        self.pump_columns = ["Hₙ,ₚ", "Qₚ", "nq,ₚ", "β₁,ₛₗᵢₚ", "α₂,ₚ", "α₁,ₚ", "Ω*ₚ", "hₛ,ₚ", "RRₚ", "𝜏ₚ", "P𝒸"]
        self.turbine_columns = ["Hₙ,ₜ", "Qₜ", "nq,ₜ", "α₁,ₜ", "α₂,ₜ", "Ω*ₜ", "hₛ,ₜ", "RRₜ", "𝜏ₜ", "Pₚ"]
        self.dimension_columns = ["n", "β₂", "β₁,ₓₛₗᵢₚ", "D₂", "D₁", "B₀", "Bₕ"]

        # Create tables
        self.app.pm_tree = self.create_table(self.pump_data_frame, self.pump_columns)
        self.app.tm_tree = self.create_table(self.turbine_data_frame, self.turbine_columns)
        self.app.dimensions_tree = self.create_table(self.dimensions_data_frame, self.dimension_columns)
        self.tables = (self.app.pm_tree, self.app.tm_tree, self.app.dimensions_tree)
        self.history_scrollbar = ttk.Scrollbar(
            calculated_data_frame, orient="vertical", command=self._scroll_tables
        )
        self.history_scrollbar.grid(row=0, column=3, sticky="ns")
        for tree in self.tables:
            tree.configure(yscrollcommand=lambda first, last, source=tree: self._sync_scroll(source, first, last))
            tree.bind("<<TreeviewSelect>>", self._on_condition_selected)
            tree.bind("<ButtonRelease-1>", self._on_condition_clicked)
            tree.bind("<MouseWheel>", self._on_mousewheel)
            tree.bind("<Button-4>", self._on_mousewheel)
            tree.bind("<Button-5>", self._on_mousewheel)

        # Configure grid weights for resizing within each section
        self.pump_data_frame.grid_columnconfigure(0, weight=1)
        self.turbine_data_frame.grid_columnconfigure(0, weight=1)
        self.dimensions_data_frame.grid_columnconfigure(0, weight=1)

        # Now call update_column_widths() after tables are created
        self.update_column_widths()

    def create_table(self, parent, columns):
        ### Creates a table inside the parent frame
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=8, selectmode="browse")
        tree.grid(row=0, column=0, sticky="nsew")

        # Make sure 5 rows are visible and prevent vertical expansion
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        # Configure column headings
        for col in columns:
            tree.heading(col, text=col, anchor="center")

        return tree

    def _scroll_tables(self, *args):
        self._syncing_scroll = True
        try:
            for tree in self.tables:
                tree.yview(*args)
            self.history_scrollbar.set(*self.tables[0].yview())
        finally:
            self._syncing_scroll = False

    def _sync_scroll(self, source, first, last):
        # This also catches keyboard scrolling, see(), and direct yview calls.
        if self._syncing_scroll:
            return
        self._syncing_scroll = True
        try:
            first, last = source.yview()
            self.history_scrollbar.set(first, last)
            for tree in self.tables:
                if tree is not source and abs(tree.yview()[0] - first) > 1e-9:
                    tree.yview_moveto(first)
        finally:
            self._syncing_scroll = False

    def _on_mousewheel(self, event):
        if event.num in (4, 5):
            units = -3 if event.num == 4 else 3
        else:
            units = -int(event.delta / 120) * 3
            if not units and event.delta:
                units = -1 if event.delta > 0 else 1
        self._scroll_tables("scroll", units, "units")
        return "break"

    def _input_state(self):
        return (
            tuple(getattr(self.app, name).get() for name in _INPUT_ENTRIES),
            self.app.max_blade_length.get(),
            self.app.max_blade_length_str.get(),
        )

    def _restore_inputs(self, snapshot):
        for name, value in zip(_INPUT_ENTRIES, snapshot.entries):
            entry = getattr(self.app, name)
            entry.delete(0, tk.END)
            # ttk.Entry.insert is globally rounded by the application. Restore
            # the original input text directly so selecting a row loses no digits.
            entry.tk.call(entry._w, "insert", 0, value)
        self.app.max_blade_length.set(snapshot.blade_length)
        self.app.max_blade_length_str.set(snapshot.blade_length_text)

    def _highlight_condition(self, iid):
        self._syncing_selection = True
        try:
            for tree in self.tables:
                if tree.selection() != (iid,):
                    tree.selection_set(iid)
                tree.focus(iid)
        finally:
            self._syncing_selection = False

    def _on_condition_selected(self, event):
        if self._syncing_selection:
            return
        selected = event.widget.selection()
        if selected:
            self.select_condition(selected[0])

    def _on_condition_clicked(self, event):
        # A second click on the active row must also discard uncalculated edits.
        iid = event.widget.identify_row(event.y)
        if iid:
            self.select_condition(iid)

    def select_condition(self, iid):
        snapshot = self._conditions.get(iid)
        if snapshot is None:
            return False
        previous = self._conditions.get(self.active_condition_id)
        changed = previous is None or previous.values != snapshot.values
        inputs_changed = self._input_state() != (
            snapshot.entries, snapshot.blade_length, snapshot.blade_length_text
        )
        self.active_condition_id = iid
        self._highlight_condition(iid)
        _restore_md_values(self.gv, snapshot.values)
        if changed or inputs_changed:
            self._restore_inputs(snapshot)
            self._plot_velocity_triangles()
        if changed:
            self._notify_condition_changed()
        return True

    def _notify_condition_changed(self):
        callback = getattr(self.app, "on_main_dimensions_changed", None)
        if callback is not None:
            callback()

    def _plot_velocity_triangles(self):
        plot_pm_vt(self.app.pm_canvas, self.gv.pump_in, self.gv.pump_out)
        plot_tm_vt(self.app.tm_canvas, self.gv.turbine_in, self.gv.turbine_out)

    def record_calculation(self):
        entries, blade_length, blade_length_text = self._input_state()
        snapshot = _ConditionSnapshot(
            _capture_md_values(self.gv), entries, blade_length, blade_length_text
        )
        previous = self._conditions.get(self.active_condition_id)
        iid = f"condition_{len(self._conditions) + 1}"
        self._conditions[iid] = snapshot
        for tree, values in zip(self.tables, _result_rows(self.gv)):
            tree.insert("", 0, iid=iid, values=values)
        self.active_condition_id = iid
        self._highlight_condition(iid)
        for tree in self.tables:
            tree.see(iid)
        self._plot_velocity_triangles()
        if previous is None or previous.values != snapshot.values:
            self._notify_condition_changed()

    def prepare_for_next(self):
        """Keep the selected condition; calculate only new/edited inputs."""
        snapshot = self._conditions.get(self.active_condition_id)
        if snapshot is not None and self._input_state() == (
            snapshot.entries, snapshot.blade_length, snapshot.blade_length_text
        ):
            _restore_md_values(self.gv, snapshot.values)
            return True
        return calculate_vt(self.app, self.gv)

    def update_column_widths(self, event=None):
        ### Update column widths dynamically based on window size
        if event is not None and event.widget is not self.app:
            return
        if not all(getattr(self.app, name, None) is not None
                   and getattr(self.app, name).winfo_exists()
                   for name in ("pm_tree", "tm_tree", "dimensions_tree")):
            return
        total_columns = len(self.pump_columns) + len(self.turbine_columns) + len(self.dimension_columns)
        new_col_width = max(20, int((self.app.winfo_width() - 55) / total_columns))

        # Check if treeviews exist before updating
        if hasattr(self.app, "pm_tree") and hasattr(self.app, "tm_tree") and hasattr(self.app, "dimensions_tree"):
            for col in self.pump_columns:
                self.app.pm_tree.column(col, width=new_col_width)

            for col in self.turbine_columns:
                self.app.tm_tree.column(col, width=new_col_width)

            for col in self.dimension_columns:
                self.app.dimensions_tree.column(col, width=new_col_width)


def calculate_vt(app, gv):
    """Calculate atomically, then append one complete selectable condition."""
    try:
        for name, label in (
            ("pm_Hnp_entry", "Pump net head"),
            ("pm_Qnp_entry", "Maximum discharge"),
            ("tm_Hnt_entry", "Turbine net head"),
        ):
            text = getattr(app, name).get().strip()
            if text and (not np.isfinite(float(text)) or float(text) <= 0):
                raise ValueError(f"{label} must be a positive number.")
        blade_length = float(app.max_blade_length_str.get())
        if not np.isfinite(blade_length) or not 0 < blade_length <= 1:
            raise ValueError("Maximum blade length must be greater than 0 and at most 1.")

        # A rejected calculation must not partly overwrite the selected design.
        calculated = copy(gv)
        for name in _MD_KEYS:
            setattr(calculated, name, getattr(gv, name).copy())
        with np.errstate(divide="raise", invalid="raise", over="raise"):
            if not _calculate_vt_values(app, calculated):
                return False
        values = _capture_md_values(calculated)
        if any(not np.isfinite(value) for _, items in values[0] for _, value in items):
            raise ValueError("These inputs do not produce finite main dimensions.")
    except (ValueError, ArithmeticError) as error:
        messagebox.showerror("Input Error", f"Unable to calculate this condition:\n{error}")
        return False

    _restore_md_values(gv, values)
    tab = getattr(app, "main_dimensions_tab", None)
    if tab is not None:
        tab.record_calculation()
    else:
        # Preserve compatibility with callers that provide their own widgets.
        for tree, row in zip((app.pm_tree, app.tm_tree, app.dimensions_tree), _result_rows(gv)):
            tree.insert("", 0, values=row)
        plot_pm_vt(app.pm_canvas, gv.pump_in, gv.pump_out)
        plot_tm_vt(app.tm_canvas, gv.turbine_in, gv.turbine_out)
    print_design_results(gv)
    return True


def _calculate_vt_values(app, gv):
    ## Head and head loss
    gv.heads["Hmax"] = 465 - 72.34
    gv.heads["Hmin"] = 462 - 69.8
    gv.heads["Hgross"] = (gv.heads["Hmax"] + gv.heads["Hmin"]) / 2
    gv.heads["Hloss"] = 393.5 - 377
    gv.heads["Hnp"] = float(app.pm_Hnp_entry.get()) if app.pm_Hnp_entry.get() else (gv.heads["Hgross"] + gv.heads["Hloss"])
    gv.heads["Hnt"] = float(app.tm_Hnt_entry.get()) if app.tm_Hnt_entry.get() else (gv.heads["Hgross"] - gv.heads["Hloss"])
    # Insert default values in entryboxes
    if not app.pm_Hnp_entry.get():
        app.pm_Hnp_entry.insert(0, str(gv.heads["Hnp"]))

    if not app.tm_Hnt_entry.get():
        app.tm_Hnt_entry.insert(0, str(gv.heads["Hnt"]))

    ## Number of runner blades
    try:
        rv_text = app.Zrv_entry.get().strip()
        if rv_text:
            rv_value = int(rv_text)
            # Validation checks
            if rv_value <= 0:
                raise ValueError("Invalid Blade Number Input!")
            if rv_value > 12:
                messagebox.showwarning("Warning!", "RPT shouldn't have runner vanes greater than 12. Please consider readjusting it for better design!")
            gv.z["rv"] = rv_value
        else:
            # Default value if empty
            gv.z["rv"] = 6
            app.Zrv_entry.insert(0, str(gv.z["rv"]))
    except ValueError as e:
        messagebox.showerror("Input Error! ", str(e))
        return  # stop execution if invalid
    
    #"""
    # Synchronous speed - To allow user input of poles and calculate n_k accordingly (to allow flexibility in design)
    try:
        p_text = app.Zp_entry.get().strip()
        if p_text:
            p_value = int(p_text)
            # Validation checks
            if p_value <= 0:
                raise ValueError("Invalid Number of Poles Input!")
            if p_value > 50:
                messagebox.showwarning("Warning", "Usually RPTs do operate in higher RPM, thus have less number of poles. Please consider readjusting it for better design!")
            gv.z["pp"] = p_value
        else:
            # Default value if empty
            gv.z["pp"] = 6
            app.Zp_entry.insert(0, str(gv.z["pp"]))
    except ValueError as e:
        messagebox.showerror("Input Error!", str(e))
        return  # stop execution if invalid

    # Maximum Flow in FL
    gv.flows["Qmax"] = float(app.pm_Qnp_entry.get()) if app.pm_Qnp_entry.get() else (128 / 4)
    # Insert default values
    if not app.pm_Qnp_entry.get():
        app.pm_Qnp_entry.insert(0, str(gv.flows["Qmax"]))

    # Flow in PM = 73% of max available flow
    gv.flows["Qp"] = gv.flows["Qmax"] * 0.73

    # RPM and Specific Speed
    gv.speeds["nc"] = 3000 / gv.z["pp"]
    gv.speeds["nq_pc"] = gv.speeds["nc"] * (np.sqrt(gv.flows["Qp"])) / (gv.heads["Hnp"] ** 0.75)

    """
    # Specific speed
    fits = pd.read_excel("CharacteristicFits1.xlsx")
    a = fits.at[2, "a"]
    b = fits.at[2, "b"]
    gv.speeds["nqp"] = (1 / b) * np.log(gv.heads["Hnp"] / a)

    # Rotational speed
    gv.flows["Qmax"] = float(app.pm_Qnp_entry.get()) if app.pm_Qnp_entry.get() else (128 / 4)
    # Insert default values
    if not app.pm_Qnp_entry.get():
        app.pm_Qnp_entry.insert(0, str(gv.flows["Qmax"]))

    gv.flows["Qp"] = gv.flows["Qmax"] * 0.73
    gv.speeds["n"] = gv.speeds["nqp"] * (gv.heads["Hnp"] ** 0.75) / (np.sqrt(gv.flows["Qp"]))

    # Synchronous speed
    gv.z["pp"] = round(3000 / gv.speeds["n"])
    gv.speeds["nc"] = 3000 / gv.z["pp"]
    gv.speeds["nq_pc"] = gv.speeds["nc"] * (np.sqrt(gv.flows["Qp"])) / (gv.heads["Hnp"] ** 0.75)
    #"""


    # Velocity triangle - PUMP INLET
    gv.pump_in["u2_red"] = 0.0104 * gv.speeds["nq_pc"] + 0.1977
    gv.pump_in["u2"] = gv.pump_in["u2_red"] * np.sqrt(2 * gv.g * gv.heads["Hnp"])
    gv.pump_in["cm2_red"] = 0.1018 * np.log(gv.speeds["nq_pc"]) - 0.2009
    gv.pump_in["cm2"] = gv.pump_in["cm2_red"] * np.sqrt(2 * gv.g * gv.heads["Hnp"])
    gv.pump_in["beta2"] = np.atan(gv.pump_in["cm2_red"] / gv.pump_in["u2_red"])
    gv.pump_in["beta2_deg"] = gv.pump_in["beta2"] * 180 / np.pi
    gv.pump_in["w2"] = (gv.pump_in["cm2"]**2 + gv.pump_in["u2"]**2) ** 0.5
    gv.pump_in["alpha2_deg"] = 90
    gv.gd["D2"] = np.sqrt(4 * gv.flows["Qp"] / (gv.pump_in["cm2"] * np.pi)) # Pump inlet diameter
    gv.gd["B_hub"] = 0.5 * gv.gd["D2"] # Hub height ---------------For Francis runner, hub height is generally between 40-60% of D2

    # Velocity triangle - PUMP OUTLET
    gv.pump_out["u1_red"] = float(app.max_blade_length_str.get())  # 1 for longer bladesssss
    # Insert default values
    if not app.max_blade_length_str.get():
        app.max_blade_length_str.insert(0, str(gv.pump_out["u1_red"]))
        
    gv.pump_out["u1"] = gv.pump_out["u1_red"] * np.sqrt(2 * gv.g * gv.heads["Hnp"])
    gv.gd["D1"] = gv.pump_out["u1"] * 60 / (np.pi * gv.speeds["nc"]) # Pump outlet diameter (rotor blade)
    gv.pump_out["cm1"] = gv.pump_in["cm2"]
    gv.pump_out["cm1_red"] = gv.pump_in["cm2_red"]
    gv.gd["B0"] = gv.flows["Qp"] / (gv.pump_out["cm1"] * np.pi * gv.gd["D1"]) # Pump outlet height (rotor blade)
    #gv.gd["B0"] = (1.0 * gv.flows["Qmax"]) / (gv.pump_out["cm1"] * np.pi * gv.gd["D1"]) # 0.9 * gv.flows["Qmax"] = Qt [TURBINE MODE FLOW RATE CONSIDERED FOR B0 CALCULATION]
    gv.pump_out["cu1"] = gv.g * gv.heads["Hnp"] / (gv.eta_p * gv.pump_out["u1"])
    gv.pump_out["cu1_red"] = gv.pump_out["cu1"] / np.sqrt(2 * gv.g * gv.heads["Hnp"])
    gv.pump_out["wu1_red"] = (gv.pump_out["u1_red"] - gv.pump_out["cu1_red"])
    gv.pump_out["wu1"] = gv.pump_out["wu1_red"] * np.sqrt(2 * gv.g * gv.heads["Hnp"])
    gv.pump_out["c1"] = ((gv.pump_out["cm1"]) **2 + gv.pump_out["cu1"] **2) ** 0.5
    gv.pump_out["w1"] = ((gv.pump_out["cm1"] ** 2 + gv.pump_out["wu1"] ** 2) ** 0.5)
    gv.pump_out["beta1_actual"] = np.atan(gv.pump_out["cm1_red"] / (gv.pump_out["wu1_red"])) 
    gv.pump_out["beta1_actual_deg"] = gv.pump_out["beta1_actual"] * 180 / np.pi #Exact beta1 without slip >> ACTUAL BLADE ANGLE
    gv.pump_out["alpha1"] = np.atan((gv.pump_out["cm1_red"])/(gv.pump_out["cu1_red"]))
    gv.pump_out["alpha1_deg"] = gv.pump_out["alpha1"] * (180 / np.pi)

    # Slip corrections
    gv.pump_out["slip_deg"] = 3 #Considering 3 degrees slip at pump inlet>>>>>>>>>>>>>>SHOULD BE ESTIMATED BY ANY SORT OF RELATIONS
    gv.pump_out["beta1_minus_slip_deg"] = gv.pump_out["beta1_actual_deg"] - gv.pump_out["slip_deg"] #beta1 with slip >> ACTUAL FLOW ANGLE
    gv.pump_out["beta1_minus_slip"] = gv.pump_out["beta1_minus_slip_deg"] * np.pi / 180


    #For pump outlet slip triangle
    gv.pump_out["cm1_slip"] = gv.pump_out["cm1"]
    gv.pump_out["u1_slip"] = gv.pump_out["u1"]
    gv.pump_out["wu1_slip"] = gv.pump_out["cm1_slip"] / np.tan(gv.pump_out["beta1_minus_slip"])
    gv.pump_out["cu1_slip"] = gv.pump_out["u1_slip"] - gv.pump_out["wu1_slip"]
    gv.pump_out["cm1_slip_red"] = gv.pump_out["cm1_slip"] / np.sqrt(2 * gv.g * gv.heads["Hnp"])
    gv.pump_out["cu1_slip_red"] = gv.pump_out["cu1_slip"] / np.sqrt(2 * gv.g * gv.heads["Hnp"])
    gv.pump_out["wu1_slip_red"] = gv.pump_out["wu1_slip"] / np.sqrt(2 * gv.g * gv.heads["Hnp"])
    gv.pump_out["c1_slip"] = ((gv.pump_out["cm1_slip"]) ** 2 + gv.pump_out["cu1_slip"] ** 2) ** 0.5
    gv.pump_out["w1_slip"] = ((gv.pump_out["cm1_slip"] ** 2 + gv.pump_out["wu1_slip"] ** 2) ** 0.5)

    ## Velocity triangle - TURBINE INLET KNOWN VALUES
    gv.turbine_in["u1"] = np.pi * gv.speeds["nc"] * gv.gd["D1"] / 60
    gv.turbine_in["u1_red"] = gv.turbine_in["u1"] / np.sqrt(2 * gv.g * gv.heads["Hnt"])
    gv.turbine_in["beta1"] = gv.pump_out["beta1_actual"] # Using actual beta1 from pump outlet without slip
    gv.turbine_in["beta1_deg"] = gv.pump_out["beta1_actual_deg"]

    ## Velocity triangle - TURBINE OUTLET KNOWN VALUES
    gv.turbine_out["u2"] = gv.pump_in["u2"]  # n same and D2 same means u2 same
    gv.turbine_out["u2_red"] = gv.turbine_out["u2"] / np.sqrt(2 * gv.g * gv.heads["Hnt"])
    gv.turbine_out["beta2"] = gv.pump_in["beta2"]
    gv.turbine_out["beta2_deg"] = gv.pump_in["beta2_deg"]

    """# Function definitions --find the turbine flow rate Q that matches a given target head H by iteratively adjusting Qmax
    def find_turbine_flow(Q_low, Q_high, H_target, tol, t_in, t_out, D, eta_t, g):
        while True:
            Q_mid = 0.5 * (Q_low + Q_high)

            # Head calculation
            cm1 = 4 * Q_mid / (np.pi * D**2)
            cu1 = t_in["u1"] - cm1 / np.tan(t_in["beta1"])
            cm2 = cm1
            cu2 = (cm2 / np.tan(t_out["beta2"])) - t_out["u2"]
            H_mid = ((abs(t_in["u1"] * cu1) - abs(t_out["u2"] * cu2)) / (g)) * eta_t

            #print(f"Q_mid = {Q_mid:.6f}, H_mid = {H_mid:.6f}") # Debug print

            # Stopping condition
            if abs(H_mid - H_target) < tol:
                return Q_mid, H_mid
            # Update loop bounds
            elif H_mid > H_target:
                Q_low = Q_mid
            else:
                Q_high = Q_mid


    # Iteration to find the flow rate in the turbine
    gv.flows["Qt"], gv.heads["Hnt_it"] = find_turbine_flow(0, gv.flows["Qmax"], gv.heads["Hnt"], 1e-4, gv.turbine_in, gv.turbine_out, gv.gd["D2"], gv.eta_t, gv.g)
    # Here, Hnt = Hnt_it """

    # Direct calculation of turbine flow rate
    #gv.flows["Qt"] = 0.9 * gv.flows["Qmax"]
    gv.flows["Qt"] = gv.flows["Qp"] * (gv.heads["Hnp"] / gv.heads["Hnt"]) * (1/(gv.eta_t * gv.eta_p))

    # Remaining turbine inlet values 
    gv.turbine_in["cm1"] = 4 * gv.flows["Qt"] / (np.pi * gv.gd["D2"] ** 2) #dependent on TM flow rate calculated above
    gv.turbine_in["cm1_red"] = gv.turbine_in["cm1"] / np.sqrt(2 * gv.g * gv.heads["Hnt"])
    gv.turbine_in["cu1"] = gv.turbine_in["u1"] - gv.turbine_in["cm1"] / np.tan(gv.turbine_in["beta1"])
    #gv.turbine_in["cu1"] = gv.turbine_in["u1"] - ((1 / np.tan(gv.turbine_in["beta1"])) * (gv.flows["Qt"] / (np.pi * gv.gd["B0"] * gv.gd["D1"])))
    gv.turbine_in["cu1_red"] = gv.turbine_in["cu1"] / np.sqrt(2 * gv.g * gv.heads["Hnt"])
    gv.turbine_in["wu1_red"] = (gv.turbine_in["u1_red"] - gv.turbine_in["cu1_red"])
    gv.turbine_in["wu1"] = gv.turbine_in["wu1_red"] * np.sqrt(2 * gv.g * gv.heads["Hnt"])
    gv.turbine_in["alpha1"] = np.atan((gv.turbine_in["cm1_red"])/(gv.turbine_in["cu1_red"]))
    gv.turbine_in["alpha1_deg"] = gv.turbine_in["alpha1"] * (180 / np.pi)
    gv.turbine_in["c1"] = (gv.turbine_in["cm1"] ** 2 + gv.turbine_in["cu1"] ** 2) ** 0.5
    gv.turbine_in["w1"] = (((gv.turbine_in["cm1_red"]) ** 2 + gv.turbine_in["wu1_red"] ** 2) ** 0.5) * np.sqrt(2 * gv.g * gv.heads["Hnt"])


    # Remaining turbine inlet values
    gv.turbine_out["cm2"] = gv.turbine_in["cm1"]
    gv.turbine_out["cm2_red"] = gv.turbine_in["cm1_red"]
    gv.turbine_out["cu2"] = (gv.turbine_out["cm2"] / np.tan(gv.turbine_out["beta2"])) - gv.turbine_out["u2"]
    gv.turbine_out["cu2_red"] = gv.turbine_out["cu2"] / np.sqrt(2 * gv.g * gv.heads["Hnt"])
    gv.turbine_out["w2"] = np.sqrt(gv.turbine_out["cm2"] ** 2 + (gv.turbine_out["u2"] + gv.turbine_out["cu2"]) ** 2)
    gv.turbine_out["w2_red"] = gv.turbine_out["w2"] / np.sqrt(2 * gv.g * gv.heads["Hnt"])
    gv.turbine_out["alpha2"] = np.pi - np.atan((gv.turbine_out["cm2_red"])/(gv.turbine_out["cu2_red"]))
    gv.turbine_out["alpha2_deg"] = gv.turbine_out["alpha2"] * (180 / np.pi)
    gv.turbine_out["c2"] = (gv.turbine_out["cm2"] ** 2 + gv.turbine_out["cu2"] ** 2) ** 0.5

    #Power and torque calculations --- PM
    red_pm = np.sqrt(2 * gv.g * gv.heads["Hnp"])
    gv.omega_pm = (2 * np.pi * gv.speeds["nc"]) / 60
    gv.pm_other["speed_no"] = (gv.omega_pm / red_pm) * np.sqrt(gv.flows["Qp"] / red_pm)
    gv.pm_other["RR"] =  1 - ((gv.pump_out["c1"]**2 - gv.pump_in["cm2"]**2) / (2*gv.pump_out["u1"]*gv.pump_out["cu1"])) ## ???????? at pump inlet, c2=cm2
    gv.pm_other["power"] = (gv.eta_p * gv.rho * gv.g * gv.flows["Qp"] * gv.heads["Hnp"]) / 1000000
    gv.pm_other["torque"] = gv.pm_other["power"] / gv.omega_pm

    #Power and torque calculations --- TM
    red_tm = np.sqrt(2 * gv.g * gv.heads["Hnt"])
    gv.omega_tm = gv.omega_pm
    gv.tm_other["speed_no"] = (gv.omega_tm / red_tm) * np.sqrt(gv.flows["Qt"] / red_tm)
    gv.tm_other["RR"] = 2 * gv.turbine_in["u1_red"] * gv.turbine_in["cu1_red"] - gv.turbine_in["cu1_red"] ** 2
    gv.tm_other["power"] = (gv.eta_t * gv.rho * gv.g * gv.flows["Qt"] * gv.heads["Hnt"]) / 1000000
    gv.speeds["nq_t"] = gv.speeds["nc"] * np.sqrt(gv.tm_other["power"] * 1000) / (gv.heads["Hnt"] ** 1.25) #CALCULATING SPECIFIC SPEED IN TM AFTER CALCULATING POWER (in kW)
    gv.tm_other["torque"] = gv.tm_other["power"] / gv.omega_tm

    # Submergence Calculations --- PM
    a_p, b_p = 1.8, 0.23
    h_atm = 10.3
    h_vapour = 0.125
    NPSHr_pm = (a_p * (gv.pump_in["cm2"] ** 2 / (2 * gv.g))) + (b_p * (gv.pump_in["u2"] ** 2 / (2 * gv.g)))
    gv.pm_other["hs"] = h_atm - h_vapour - NPSHr_pm

    # Submergence Calculations --- TM
    # NPSHa>NPSHr for no cavitation _____ NPSHa is site specific...perfect place for powerhouse should be carefully selected where NPSHa>NPSHr
    a_t, b_t = 1.15, 0.055
    NPSHr_tm = (a_t * (gv.turbine_out["cm2"] ** 2 / (2 * gv.g))) + (b_t * (gv.turbine_out["u2"] ** 2 / (2 * gv.g)))
    gv.tm_other["hs"] = h_atm - h_vapour - NPSHr_tm


    return True


def _result_rows(gv):
    # Add the calculated data of PM to the table
    new_pm_data = [gv.heads["Hnp"], gv.flows["Qp"], gv.speeds["nq_pc"], gv.pump_out["slip_deg"], gv.pump_in["alpha2_deg"], gv.pump_out["alpha1_deg"], gv.pm_other["speed_no"], gv.pm_other["hs"], gv.pm_other["RR"], gv.pm_other["torque"], gv.pm_other["power"]]

    # Add the calculated data of TM to the table
    new_tm_data = [gv.heads["Hnt"], gv.flows["Qt"], gv.speeds["nq_t"], gv.turbine_in["alpha1_deg"], gv.turbine_out["alpha2_deg"], gv.tm_other["speed_no"], gv.tm_other["hs"], gv.tm_other["RR"], gv.tm_other["torque"], gv.tm_other["power"]]

    # Add main dimensions of the RPT runner to the table
    new_md_data = [gv.speeds["nc"], gv.pump_in["beta2_deg"], gv.pump_out["beta1_minus_slip_deg"], gv.gd["D2"], gv.gd["D1"], gv.gd["B0"], gv.gd["B_hub"]]

    return new_pm_data, new_tm_data, new_md_data


def plot_pm_vt(vt_frame_pm, pi, po):
        # Create a new Matplotlib figure
        fig = Figure(figsize=(6,6), dpi=100)
        ax = fig.add_subplot(111)
        

        # Set up the coordinate system
        scale = 5

        # Define Pump Inlet Coordinates
        startP = np.array([0, 0])
        w2s = startP[0] - pi["u2_red"] * scale, startP[1] 
        w2e = startP[0], startP[1] + pi["cm2_red"] * scale 
        cm2e = w2s[0], w2e[1] 


        # Draw Pump Inlet Velocity Lines
        ax.plot([w2s[0], cm2e[0]], [w2s[1], cm2e[1]], color='black') #L1
        ax.plot([w2s[0], w2e[0]], [w2s[1], w2e[1]], color='black') #L3
        ax.plot([w2e[0], cm2e[0]], [w2e[1], cm2e[1]], color='black')  # L2

        # With Arrows & Text
        ax.annotate("", xy=(cm2e[0], cm2e[1]), xytext=(w2s[0], w2s[1]), arrowprops=dict(arrowstyle="->", color="black"))
        ax.text((w2s[0] + cm2e[0] + 3) / 2, (w2s[1] + cm2e[1]) / 2, f"w₂ = {round(pi["w2"], 2)}", fontsize=8, color="black")
        ax.annotate("", xy=(w2e[0], w2e[1]), xytext=(w2s[0], w2s[1]),arrowprops=dict(arrowstyle="->", color="black"))
        ax.text((w2s[0] + w2e[0] - 0.6) / 2, (w2s[1] + w2e[1] + 0.8 ) / 2, f"u₂ = {round(pi["u2"], 2)}", fontsize=8, color="black")
        ax.annotate("", xy=(cm2e[0], cm2e[1]), xytext=(w2e[0], w2e[1]), arrowprops=dict(arrowstyle="->", color="black"))
        ax.text((w2s[0] + cm2e[0] - 2) / 2, (w2s[1] + cm2e[1]) / 2, f"cₘ₂ = {round(pi["cm2"], 2)}", fontsize=8, color="black")

        # Pump Outlet Coordinates
        cm1s = cm2e[0] , cm2e[1] + 0.5 #P3
        c1e = cm1s[0] - po["cu1_red"] * scale, cm1s[1] + po["cm1_red"] * scale #P4
        cm1e = cm2e[0] , c1e[1] #P5
        w1e = cm1s[0] + po["wu1_red"] * scale, c1e[1] #P6

        #for slip triangle
        cm1s_slip = cm2e[0] - ((po["cu1_red"] * scale) - (po["cu1_slip_red"] * scale)), cm2e[1] + 0.5  # P3
        c1e_slip = c1e[0] , c1e[1]
        cm1e_slip = cm1s_slip[0], cm1s_slip[1] + (po["cm1_red"] * scale)
        w1e_slip = w1e[0] , w1e[1]

        # Draw Pump Outlet Velocity Lines
        ax.plot([cm1s[0], c1e[0]], [cm1s[1], c1e[1]], color='black')
        ax.plot([cm1s[0], cm1e[0]], [cm1s[1], cm1e[1]], color='black')
        ax.plot([cm1s[0], w1e[0]], [cm1s[1], w1e[1]], color='black')
        ax.plot([c1e[0], w1e[0]], [c1e[1], w1e[1]], color='black')
        ax.plot([cm1e[0], c1e[0]], [cm1e[1] + 0.15, c1e[1] + 0.15], color='black')
        ax.plot([cm1e[0], w1e[0]], [cm1e[1] + 0.2, w1e[1] + 0.2], color='black')

        
        #for slip triangle
        ax.plot([cm1s_slip[0], c1e_slip[0]], [cm1s_slip[1], c1e_slip[1]], color='blue')
        ax.plot([cm1s_slip[0], cm1e_slip[0]], [cm1s_slip[1], cm1e_slip[1]], color='blue')
        ax.plot([cm1s_slip[0], w1e_slip[0]], [cm1s_slip[1], w1e_slip[1]], color='blue')
        ax.plot([c1e_slip[0], w1e_slip[0]], [c1e_slip[1], w1e_slip[1]], color='blue')
        ax.plot([cm1e_slip[0], c1e_slip[0]], [cm1e_slip[1] + 0.35, c1e_slip[1] + 0.35], color='blue')
        ax.plot([cm1e_slip[0], w1e_slip[0]], [cm1e_slip[1] + 0.4, w1e_slip[1] + 0.4], color='blue')

        # With Arrows & Text
        ax.annotate("", xy=(c1e[0], c1e[1]), xytext=(cm1s[0], cm1s[1]), arrowprops=dict(arrowstyle="->", color="black"))
        ax.text((cm1s[0] + c1e[0] - 2.5) / 2, (cm1s[1] + c1e[1]) / 2, f"c₁ = {round(po["c1"], 2)}", fontsize=8, color="black")
        ax.annotate("", xy=(cm1e[0], cm1e[1]), xytext=(cm1s[0], cm1s[1]), arrowprops=dict(arrowstyle="->", color="black"))
        ax.text((cm1s[0] + cm1e[0] - 2) / 2, (cm1s[1] + cm1e[1]) / 2, f"cₘ₁ = cₘ₁ₛ = {round(po["cm1"], 2)}", fontsize=8, color="black")
        ax.annotate("", xy=(w1e[0], w1e[1]), xytext=(cm1s[0], cm1s[1]), arrowprops=dict(arrowstyle="->", color="black"))
        ax.text((cm1s[0] + w1e[0] + 1) / 2, (cm1s[1] + w1e[1]) / 2, f"w₁ = {round(po["w1"], 2)}", fontsize=8, color="black")
        ax.annotate("", xy=(c1e[0], c1e[1]), xytext=(w1e[0], w1e[1]), arrowprops=dict(arrowstyle="->", color="black"))
        ax.text((c1e[0] + w1e[0] - 1) / 2 , (c1e[1] + w1e[1] + 0.08) / 2, f"u₁ = u₁ₛ = {round(po["u1"], 2)}", fontsize=8, color="black")
        ax.annotate("", xy=(c1e[0], c1e[1] + 0.15), xytext=(cm1e[0], cm1e[1] + 0.15), arrowprops=dict(arrowstyle="->", color="black"))
        ax.text((c1e[0] + cm1e[0] - 1.5) / 2, (c1e[1] + cm1e[1] + 0.34) / 2, f"cᵤ₁ = {round(po["cu1"], 2)}", fontsize=8, color="black")
        ax.annotate("", xy=(w1e[0], w1e[1] + 0.2), xytext=(cm1e[0], cm1e[1] + 0.2), arrowprops=dict(arrowstyle="->", color="black"))
        ax.text((w1e[0] + cm1e[0]) / 2, (w1e[1] + cm1e[1] + 0.44) / 2, f"wᵤ₁ = {round(po["wu1"], 2)}", fontsize=8, color="black")

        # With Arrows & Text -- slip triangle
        ax.annotate("", xy=(c1e_slip[0], c1e_slip[1]), xytext=(cm1s_slip[0], cm1s_slip[1]), arrowprops=dict(arrowstyle="->", color="blue"))
        ax.text((cm1s_slip[0] + c1e_slip[0] - 3.5) / 2, (cm1s_slip[1] + c1e_slip[1] + 0.3) / 2, f"c₁ₛ = {round(po["c1_slip"], 2)}", fontsize=8, color="blue")
        ax.annotate("", xy=(cm1e_slip[0], cm1e_slip[1]), xytext=(cm1s_slip[0], cm1s_slip[1]),arrowprops=dict(arrowstyle="->", color="blue"))
        #ax.text((cm1s_slip[0] + cm1e_slip[0]) / 2, (cm1s_slip[1] + cm1e_slip[1]) / 2 + 0.15, f"cₘ₁ₛ = {round(po["cm1_slip"], 2)}", fontsize=8,color="blue")
        ax.annotate("", xy=(w1e_slip[0], w1e_slip[1]), xytext=(cm1s_slip[0], cm1s_slip[1]), arrowprops=dict(arrowstyle="->", color="blue"))
        ax.text((cm1s_slip[0] + w1e_slip[0] + 2) / 2, (cm1s_slip[1] + w1e_slip[1] + 0.3) / 2, f"w₁ₛ = {round(po["w1_slip"], 2)}", fontsize=8,color="blue")
        #ax.annotate("", xy=(c1e_slip[0], c1e_slip[1]), xytext=(w1e_slip[0], w1e_slip[1]), arrowprops=dict(arrowstyle="->", color="blue"))
        #ax.text((c1e_slip[0] + w1e_slip[0]) / 2 + 0.4, (c1e_slip[1] + w1e_slip[1] + 0.08) / 2, f"u₁ₛ = {round(po["u1_slip"], 2)}", fontsize=8,color="blue")
        ax.annotate("", xy=(c1e_slip[0], c1e_slip[1] + 0.35), xytext=(cm1e_slip[0], cm1e_slip[1] + 0.35),arrowprops=dict(arrowstyle="->", color="blue"))
        ax.text((c1e_slip[0] + cm1e_slip[0] - 1.5) / 2, (c1e_slip[1] + cm1e_slip[1] + 0.74) / 2, f"cᵤ₁ₛ = {round(po["cu1_slip"], 2)}", fontsize=8,color="blue")
        ax.annotate("", xy=(w1e_slip[0], w1e_slip[1] + 0.4), xytext=(cm1e_slip[0], cm1e_slip[1] + 0.4),arrowprops=dict(arrowstyle="->", color="blue"))
        ax.text((w1e_slip[0] + cm1e_slip[0]) / 2, (w1e_slip[1] + cm1e_slip[1] + 0.84) / 2, f"wᵤ₁ₛ = {round(po["wu1_slip"], 2)}", fontsize=8,color="blue")

        # Labels and Grid
        #ax.set_title("Pump Mode Velocity Triangle")
        #ax.grid(True, linestyle="--", alpha=0.5)
        ax.set_axis_off()

        # Clear the frame before adding a new plot
        for widget in vt_frame_pm.winfo_children():
            widget.destroy()

        # Embed Matplotlib figure into Tkinter
        canvas = FigureCanvasTkAgg(fig, master=vt_frame_pm)
        canvas.draw()

        # Add Navigation Toolbar
        toolbar = NavigationToolbar2Tk(canvas, vt_frame_pm)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")
        canvas.get_tk_widget().pack(fill="both", expand=True)


def plot_tm_vt(vt_frame_tm, ti, to ):
    # Create a new Matplotlib figure
    fig = Figure(figsize=(6,6), dpi=100)
    ax = fig.add_subplot(111)

    # Set up the coordinate system
    scale = 5

    # Define Turbine Inlet Coordinates
    u1s = np.array([0, 0])  # P0
    cm1s = u1s[0] + ti["cu1_red"] * scale, u1s[1]  # P1
    u1e = cm1s[0] + ti["wu1_red"] * scale, u1s[1]  # P2
    cm1e = cm1s[0], cm1s[1] - ti["cm1_red"] * scale  # P3


    # Draw Turbine Inlet Velocity Lines
    ax.plot([u1s[0], u1e[0]], [u1s[1], u1e[1]], color='black')  # L1
    ax.plot([u1s[0], cm1e[0]], [u1s[1], cm1e[1]], color='black')  # L2
    ax.plot([cm1s[0], cm1e[0]], [cm1s[1], cm1e[1]], color='black')  # L3
    ax.plot([u1e[0], cm1e[0]], [u1e[1], cm1e[1]], color='black')  # L4
    ax.plot([u1s[0], cm1s[0]], [u1s[1] + 0.2, cm1s[1] + 0.2], color='black')
    ax.plot([u1e[0], cm1s[0]], [u1e[1] + 0.25, cm1s[1] + 0.25], color='black')

    #Arrow & Naming
    ax.annotate("", xy=(u1e[0], u1e[1]), xytext=(u1s[0], u1s[1]), arrowprops=dict(arrowstyle="->", color="black"))
    ax.text((u1s[0] + u1e[0]) / 2, (u1s[1] + u1e[1] + 0.08) / 2, f"u₁ = {round(ti["u1"], 2)}", fontsize=8, color="black")
    ax.annotate("", xy=(cm1e[0], cm1e[1]), xytext=(u1s[0], u1s[1]), arrowprops=dict(arrowstyle="->", color="black"))
    ax.text((u1s[0] + cm1e[0]) / 2, (u1s[1] + cm1e[1]) / 2, f"c₁ = {round(ti["c1"], 2)}", fontsize=8, color="black")
    ax.annotate("", xy=(cm1e[0], cm1e[1]), xytext=(cm1s[0], cm1s[1]), arrowprops=dict(arrowstyle="->", color="black"))
    ax.text((cm1s[0] + cm1e[0]) / 2, (cm1s[1] + cm1e[1]) / 2, f"cₘ₁ = {round(ti["cm1"], 2)}", fontsize=8, color="black")
    ax.annotate("", xy=(cm1e[0], cm1e[1]), xytext=(u1e[0], u1e[1]), arrowprops=dict(arrowstyle="->", color="black"))
    ax.text((u1e[0] + cm1e[0] + 0.3) / 2, (u1e[1] + cm1e[1]) / 2, f"w₁ = {round(ti["w1"], 2)}", fontsize=8, color="black")
    ax.annotate("", xy=(cm1s[0], cm1s[1] + 0.2), xytext=(u1s[0], u1s[1] + 0.2), arrowprops=dict(arrowstyle="->", color="black"))
    ax.text((u1s[0] + cm1s[0]-1.5) / 2, (u1s[1] + cm1s[1] + 0.47) / 2, f"cᵤ₁ = {round(ti["cu1"], 2)}", fontsize=8, color="black")
    ax.annotate("", xy=(cm1s[0], cm1s[1] + 0.25), xytext=(u1e[0], u1e[1] + 0.25), arrowprops=dict(arrowstyle="->", color="black"))
    ax.text((u1e[0] + cm1s[0]) / 2, (u1e[1] + cm1s[1] + 0.54) / 2, f"wᵤ₁ = {round(ti["wu1"], 2)}", fontsize=8, color="black")

    # Define Turbine Outlet Coordinates
    cm2s = cm1e[0], cm1e[1] - 0.5 
    w2e = cm2s[0], cm2s[1] - to["cm2_red"] * scale   
    u2s = cm2s[0] + to["cu2_red"] * scale, cm2s[1]  
    w2s = u2s[0] + to["u2_red"] * scale, u2s[1]
    c2e = w2e[0], w2e[1]  
    
    # Draw Turbine Outlet Velocity Lines
    ax.plot([w2s[0], u2s[0]], [w2s[1], u2s[1]], color='black')  # u
    ax.plot([u2s[0], cm2s[0]], [u2s[1], cm2s[1]], color='black')  # cu
    ax.plot([cm2s[0], w2e[0]], [cm2s[1], w2e[1]], color='black')  # cm
    ax.plot([w2s[0], w2e[0]], [w2s[1], w2e[1]], color='black')  # w
    ax.plot([u2s[0], w2e[0]], [u2s[1], w2e[1]], color='black')  # c

    # Arrows & Naming
    ax.annotate("", xy=(w2s[0], w2s[1]), xytext=(u2s[0], u2s[1]), arrowprops=dict(arrowstyle="->", color="black"))
    ax.text((w2s[0] + u2s[0]) / 2, w2s[1] + 0.05, f"u₂ = {round(to['u2'], 2)}", fontsize=8, color="black", ha='center')

    ax.annotate("", xy=(cm2s[0], cm2s[1]), xytext=(u2s[0], u2s[1]), arrowprops=dict(arrowstyle="->", color="black", linestyle='--'))
    ax.text((u2s[0] + c2e[0]) / 2, u2s[1] + 0.05, f"cᵤ₂ = {round(to['cu2'], 2)}", fontsize=8, color="black", ha='center')

    ax.annotate("", xy=(w2e[0], w2e[1]), xytext=(cm2s[0], cm2s[1]), arrowprops=dict(arrowstyle="->", color="black"))
    ax.text(cm2s[0] - 0.1, (cm2s[1] + w2e[1]) / 2, f"cₘ₂ = {round(to['cm2'], 2)}", fontsize=8, color="black", ha='right', va='center')

    ax.annotate("", xy=(w2e[0], w2e[1]), xytext=(w2s[0], w2s[1]), arrowprops=dict(arrowstyle="->", color="black"))
    ax.text((w2s[0] + w2e[0] + 1.5) / 2, (w2s[1] + w2e[1]) / 2, f"w₂ = {round(to['w2'], 2)}", fontsize=8, color="black", ha='center')

    ax.annotate("", xy=(w2e[0], w2e[1]), xytext=(u2s[0], u2s[1]), arrowprops=dict(arrowstyle="->", color="black"))
    ax.text((c2e[0] + w2e[0] + 1) / 2, (cm2s[1] + w2e[1]) / 2, f"c₂ = {round(to['c2'], 2)}", fontsize=8, color="black", ha='left')

    # Labels and Grid
    # ax.set_title("Turbine Mode Velocity Triangle")
    # ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_axis_off()

    # Clear the frame before adding a new plot
    for widget in vt_frame_tm.winfo_children():
        widget.destroy()

    # Embed Matplotlib figure into Tkinter
    canvas = FigureCanvasTkAgg(fig, master=vt_frame_tm)
    canvas.draw()
    

    # Add Navigation Toolbar
    toolbar = NavigationToolbar2Tk(canvas, vt_frame_tm)
    toolbar.update()
    toolbar.pack(side="bottom", fill="x")
    canvas.get_tk_widget().pack(fill="both", expand=True)
    

def build_design_results_text(gv):
    lines = []
    lines.append("\n" + "=" * 80)
    lines.append("RPT RUNNER DESIGN PARAMETERS")
    lines.append("=" * 80)
    
    # INPUT VARIABLES
    lines.append("\n" + "-" * 80)
    lines.append("INPUT VARIABLES")
    lines.append("-" * 80)
    lines.append(f"{'Parameter':<30} {'Value |':>15} {'Unit':<10}")
    lines.append("-" * 80)
    
    # Based on Availability
    lines.append("Based on Availability:")
    lines.append(f"  Net Head - Pump                {gv.heads['Hnp']:>15.2f} {'m':<10}")
    lines.append(f"  Maximum Available Discharge    {gv.flows['Qmax']:>15.2f} {'m³/s':<10}")
    lines.append(f"  Net Head - Turbine             {gv.heads['Hnt']:>15.2f} {'m':<10}")

    lines.append(f"  Number of Blades               {gv.z['rv']:>15} {'--':<10}")
    lines.append(f"  Pair of Poles                  {gv.z['pp']:>15} {'--':<10}")
    lines.append(f"  Max Blade Length (u_1,p,red)   {gv.pump_out['u1_red']:>15.2f} {'--':<10}")
    
    # Based on Assumption
    lines.append("\nBased on Assumption:")
    lines.append(f"  Max. Hydraulic Efficiency at TM{gv.eta_t:>15.2f} {'--':<10}")
    lines.append(f"  Max. Hydraulic Efficiency at PM{gv.eta_p:>15.2f} {'--':<10}")
    lines.append(f"  Pump Inlet Angle (α_2,p)       {gv.pump_in['alpha2_deg']:>15.2f} {'deg':<10}")

    
    # CALCULATED OUTPUT VARIABLES
    lines.append("\n" + "-" * 80)
    lines.append("CALCULATED OUTPUT VARIABLES")
    lines.append("-" * 80)
    
    # Main Dimensions
    lines.append("\nMAIN DIMENSIONS:")
    lines.append(f"{'Parameter':<30} {'Value':>15} {'Unit':<10}")
    lines.append("-" * 80)
    lines.append(f"  Rotational Speed [Synchronous] {gv.speeds['nc']:>15.2f} {'rpm':<10}")
    lines.append(f"  Outlet Diameter (D1)           {gv.gd['D1']:>15.4f} {'m':<10}")
    lines.append(f"  Inlet Diameter (D2)            {gv.gd['D2']:>15.4f} {'m':<10}")
    lines.append(f"  Outlet Height                  {gv.gd['B0']:>15.4f} {'m':<10}")
    lines.append(f"  Hub Diameter                   {gv.gd['B_hub'] * 2:>15.4f} {'m':<10}")
    lines.append(f"  Hub Height                     {gv.gd['B_hub']:>15.4f} {'m':<10}")
    
    # PUMP MODE OPERATION
    lines.append("\n" + "-" * 80)
    lines.append("PUMP MODE OPERATION")
    lines.append("-" * 80)
    
    # PM Inlet
    lines.append("\nPump Inlet:")
    lines.append("  Velocity Components:")
    lines.append(f"    u_2,p                      {gv.pump_in['u2']:>15.4f} {'m/s':<10}")
    lines.append(f"    c_m2,p                     {gv.pump_in['cm2']:>15.4f} {'m/s':<10}")
    lines.append(f"    w_2,p                      {gv.pump_in['w2']:>15.4f} {'m/s':<10}")
    lines.append("  Flow Angles:")
    lines.append(f"    α_2,p                      {gv.pump_in['alpha2_deg']:>15.4f} {'deg':<10}")
    lines.append(f"    β_2,p                      {gv.pump_in['beta2_deg']:>15.4f} {'deg':<10}")
    
    # PM Outlet
    lines.append("\nPump Outlet:")
    lines.append("  Velocity Components:")
    lines.append(f"    u_1,p                      {gv.pump_out['u1']:>15.4f} {'m/s':<10}")
    lines.append(f"    c_1,p                      {gv.pump_out['c1']:>15.4f} {'m/s':<10}")
    lines.append(f"    c_u1,p                     {gv.pump_out['cu1']:>15.4f} {'m/s':<10}")
    lines.append(f"    c_m1,p                     {gv.pump_out['cm1']:>15.4f} {'m/s':<10}")
    lines.append(f"    w_1,p                      {gv.pump_out['w1']:>15.4f} {'m/s':<10}")
    lines.append(f"    w_u1,p                     {gv.pump_out['wu1']:>15.4f} {'m/s':<10}")
    lines.append("  Flow Angles:")
    lines.append(f"    α_1,p                      {gv.pump_out['alpha1_deg']:>15.4f} {'deg':<10}")
    lines.append(f"    β_1,p (actual)             {gv.pump_out['beta1_actual_deg']:>15.4f} {'deg':<10}")
    lines.append(f"    β_1,p (with slip)          {gv.pump_out['beta1_minus_slip_deg']:>15.4f} {'deg':<10}")

    # PM Other Calculated Parameters
    lines.append("\nOther Calculated Parameters at PM:")
    lines.append(f"  Specific Speed             {gv.speeds['nq_pc']:>15.4f} {'--':<10}")
    lines.append(f"  SPEED NO                   {gv.pm_other['speed_no']:>15.4f} {'--':<10}")
    lines.append(f"  Submergence                {gv.pm_other['hs']:>15.4f} {'m':<10}")
    lines.append(f"  Reaction Ratio             {gv.pm_other['RR']:>15.4f} {'--':<10}")
    lines.append(f"  Torque                     {gv.pm_other['torque']:>15.4f} {'MN-m':<10}")
    lines.append(f"  Power Consumption          {gv.pm_other['power']:>15.4f} {'MW':<10}")

    
    # TURBINE MODE OPERATION
    lines.append("\n" + "-" * 80)
    lines.append("TURBINE MODE OPERATION")
    lines.append("-" * 80)
    
    # TM Inlet
    lines.append("\nTurbine Inlet:")
    lines.append("  Velocity Components:")
    lines.append(f"    u_1,t                      {gv.turbine_in['u1']:>15.4f} {'m/s':<10}")
    lines.append(f"    c_1,t                      {gv.turbine_in['c1']:>15.4f} {'m/s':<10}")
    lines.append(f"    c_u1,t                     {gv.turbine_in['cu1']:>15.4f} {'m/s':<10}")
    lines.append(f"    c_m1,t                     {gv.turbine_in['cm1']:>15.4f} {'m/s':<10}")
    lines.append(f"    w_1,t                      {gv.turbine_in['w1']:>15.4f} {'m/s':<10}")
    lines.append(f"    w_u1,t                     {gv.turbine_in['wu1']:>15.4f} {'m/s':<10}")
    lines.append("  Flow Angles:")
    lines.append(f"    α_1,t                      {gv.turbine_in['alpha1_deg']:>15.4f} {'deg':<10}")
    lines.append(f"    β_1,t                      {gv.turbine_in['beta1_deg']:>15.4f} {'deg':<10}")
    
    # TM Outlet
    lines.append("\nTurbine Outlet:")
    lines.append("  Velocity Components:")
    lines.append(f"    u_2,t                      {gv.turbine_out['u2']:>15.4f} {'m/s':<10}")
    lines.append(f"    c_2,t                      {gv.turbine_out['c2']:>15.4f} {'m/s':<10}")
    lines.append(f"    c_u2,t                     {gv.turbine_out['cu2']:>15.4f} {'m/s':<10}")
    lines.append(f"    c_m2,t                     {gv.turbine_out['cm2']:>15.4f} {'m/s':<10}")
    lines.append(f"    w_2,t                      {gv.turbine_out['w2']:>15.4f} {'m/s':<10}")
    lines.append("  Flow Angles:")
    lines.append(f"    α_2,t                      {gv.turbine_out['alpha2_deg']:>15.4f} {'deg':<10}")
    lines.append(f"    β_2,t                      {gv.turbine_out['beta2_deg']:>15.4f} {'deg':<10}")

    # TM Other Calculated Parameters at TM
    lines.append("\nOther Calculated Parameters at TM:")
    lines.append(f"  Specific Speed        {gv.speeds['nq_t']:>15.4f} {'--':<10}")
    lines.append(f"  SPEED NO              {gv.tm_other['speed_no']:>15.4f} {'--':<10}")
    lines.append(f"  Submergence           {gv.tm_other['hs']:>15.4f} {'m':<10}")
    lines.append(f"  Reaction Ratio        {gv.tm_other['RR']:>15.4f} {'--':<10}")
    lines.append(f"  Torque                {gv.tm_other['torque']:>15.4f} {'MN-m':<10}")
    lines.append(f"  Power Produced        {gv.tm_other['power']:>15.4f} {'MW':<10}")
    
    lines.append("\n" + "=" * 80 + "\n")
    return "\n".join(lines)


def print_design_results(gv):
    print(build_design_results_text(gv))









