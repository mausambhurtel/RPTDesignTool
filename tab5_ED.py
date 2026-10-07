import tkinter as tk
from tkinter import ttk
import numpy as np
import math as m
import matplotlib.pyplot as plt
from scipy.special import comb
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

class tab5_content(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.gv = app.gv
        self.current_plot = None  # To keep track of current plot for clearing
        self.current_toolbar = None  # To keep track of current toolbar

        self.frame()

    def frame(self):
        # Configure grid weights for responsiveness
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=8)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # Configure control frame for centering
        control_frame.columnconfigure(0, weight=1)
        control_frame.rowconfigure(0, weight=1)
        control_frame.rowconfigure(1, weight=1)
        control_frame.rowconfigure(2, weight=1)

        # Create a centered container within control frame
        frame4centeringwidgets = ttk.Frame(control_frame)
        frame4centeringwidgets.grid(row=1, column=0, sticky="ns")

        # Selection options
        selection_label = ttk.Label(frame4centeringwidgets, text="Select Blade Position:")
        selection_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        # Combobox for selection
        self.position_combobox = ttk.Combobox(frame4centeringwidgets, values=["Hub", "Center", "Shroud"], state="readonly", width=15)
        self.position_combobox.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.position_combobox.set("Center")  # Set default to Center

        # Button
        view_ed_button = ttk.Button(frame4centeringwidgets, text="View Energy Distribution", command=self.plot_ed_curves)
        view_ed_button.grid(row=3, column=0, columnspan=2, padx=10, pady=30, sticky="nsew")

        # Energy distribution plot frame
        self.ed_tm_plot_frame = ttk.LabelFrame(self, text="Energy Distribution in Turbine Mode")
        self.ed_tm_plot_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

        # Prevent the plot frame from resizing based on its contents
        self.ed_tm_plot_frame.pack_propagate(False)
        self.ed_tm_plot_frame.grid_propagate(False)

    # Clear the previous plot and toolbar from the frame
    def clear_previous_plot(self):
        for widget in self.ed_tm_plot_frame.winfo_children():
            widget.destroy()
        self.current_plot = None
        self.current_toolbar = None

    # Plot energy distribution curves directly to the frame
    def plot_ed_curves(self):
        
        self.clear_previous_plot()
        
        # Get the selected position
        position = self.position_combobox.get()
        
        # Create the figure
        fig, ax = plt.subplots(figsize=(8, 6))

        betadist_option = self.app.option.get()

        if betadist_option == "Linear Distribution":
            # Calculate Umat, Cumat, Wmat, and UCumat
            self.gv.Umat = self.gv.omega_tm * self.gv.Rmat
            self.gv.Cumat = self.gv.Umat - self.gv.C_mMat / np.tan(self.gv.beta)
            self.gv.Wmat = np.sqrt((self.gv.Umat - self.gv.Cumat) ** 2 + self.gv.C_mMat ** 2)
            self.gv.UCumat = self.gv.Umat * self.gv.Cumat

            # Determine which column to plot based on selection
            if position == "Hub":
                col_index = -1
            elif position == "Center":
                col_index = round((int(self.app.no_streamlines_spinbox.get()) if self.app.no_streamlines_spinbox.get() else 10) / 2)
            else:  # Shroud
                col_index = 0

            # Plot data
            ax.plot(self.gv.blade_span, self.gv.C_mMat[:, col_index] / self.gv.C_mMat[0, col_index], color='#20B2AA', marker='o', markersize=4, markevery=10, label='cm')
            ax.plot(self.gv.blade_span, self.gv.Wmat[:, col_index] / self.gv.Wmat[0, col_index], color='#2E8B57', marker='s', markersize=4, markevery=10, label='w')
            ax.plot(self.gv.blade_span, self.gv.Umat[:, col_index] / self.gv.Umat[0, col_index], color='#4169E1', marker='^', markersize=4, markevery=10, label='u')
            ax.plot(self.gv.blade_span, self.gv.Cumat[:, col_index] / self.gv.Cumat[0, col_index], color='#8B008B', marker='d', markersize=4, markevery=10, label='cu')
            ax.plot(self.gv.blade_span, self.gv.UCumat[:, col_index] / self.gv.UCumat[0, col_index], color='#FF6B35', marker='*', markersize=6, markevery=10, label='UCu')

        elif betadist_option == "UCu Distribution":
            # Determine which column to plot based on selection
            if position == "Hub":
                col_index = -1
            elif position == "Center":
                col_index = round((int(self.app.no_streamlines_spinbox.get()) if self.app.no_streamlines_spinbox.get() else 10) / 2)
            else:  # Shroud
                col_index = 0

            # Plot data
            ax.plot(self.gv.blade_span, self.gv.C_mMat[:, col_index] / self.gv.C_mMat[0, col_index], color='#20B2AA', marker='o', markersize=4, markevery=10, label='cm')
            ax.plot(self.gv.blade_span, self.gv.Wmat[:, col_index] / self.gv.Wmat[0, col_index], color='#2E8B57', marker='s', markersize=4, markevery=10, label='w')
            ax.plot(self.gv.blade_span, self.gv.Umat[:, col_index] / self.gv.Umat[0, col_index], color='#4169E1', marker='^', markersize=4, markevery=10, label='u')
            ax.plot(self.gv.blade_span, self.gv.Cumat[:, col_index] / self.gv.Cumat[0, col_index], color='#8B008B', marker='d', markersize=4, markevery=10, label='cu')
            ax.plot(self.gv.blade_span, self.gv.UCuRelativemat[:, col_index], color='#FF6B35', marker='*', markersize=6, markevery=10, label='UCu')

        # Adding legend and labels
        ax.legend()
        ax.set_xlabel('LE<-------------  Blade Span  ------------->TE')
        ax.set_ylabel('Normalized Quantities')

        # Embed the plot directly to the frame
        self.current_plot = FigureCanvasTkAgg(fig, master=self.ed_tm_plot_frame)
        self.current_plot.draw()
        self.current_plot.get_tk_widget().pack(fill="both", expand=True)

        # Add navigation toolbar
        self.current_toolbar = NavigationToolbar2Tk(self.current_plot, self.ed_tm_plot_frame)
        self.current_toolbar.update()
        self.current_toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        if hasattr(self.app, "mark_design_step_complete"):
            self.app.mark_design_step_complete(4)
