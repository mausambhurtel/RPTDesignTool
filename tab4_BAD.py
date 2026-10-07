import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import math as m
import matplotlib.pyplot as plt
from scipy.special import comb
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


class tab4_content(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.gv = app.gv
        self.interactive_plot = None
        self.current_option = None
        self.curve_generated = False  # Track if curves have been generated
        self.frame()

    def frame(self): 
        # Configure grid weights for responsiveness
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=5)
        self.columnconfigure(1, weight=3)

        # LEFT SIDE (Input + Bad Distribution Graph)
        left_frame = ttk.Frame(self)
        left_frame.grid(row=0, column=0, sticky="nsew", pady=2)
        left_frame.rowconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=5)
        left_frame.columnconfigure(0, weight=1)
        left_frame.grid_propagate(False)

        # Input frame (top left)
        input_frame = ttk.Frame(left_frame)
        input_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        input_frame.grid_propagate(False)

        # Inside input_frame
        inputl_frame = ttk.LabelFrame(input_frame, text="Beta Distribution")
        inputl_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        inputl_frame.grid_propagate(False)

        inputr_frame = ttk.LabelFrame(input_frame, text="Angles")
        inputr_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        inputr_frame.grid_propagate(False)

        # Set weight proportions for resizing
        input_frame.columnconfigure(0, weight=50)
        input_frame.columnconfigure(1, weight=50)
        input_frame.rowconfigure(0, weight=1) # Make row 0 stretch

        # Widgets in input_frame
        ttk.Label(inputl_frame, text="Distribution Method:").grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Define the StringVar (to make default option)
        self.app.option = tk.StringVar()
        self.app.option.set("UCu Distribution")

        # Create the combobox and link it to the StringVar
        dist_method = ttk.Combobox(inputl_frame, values=["Linear Distribution", "UCu Distribution"], textvariable=self.app.option, state="readonly")
        dist_method.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        #Displaying Wrap Angle
        ttk.Label(inputr_frame, text="Max Wrap Angle of Blade:").grid(row=0, column=2, padx=10, pady=10, sticky="w")
        # Defining StringVar to place calculated wrap angles values
        self.app.wrap_angle_var = tk.StringVar()
        self.app.wrap_angle_var.set("")  # Initial value
        wrap_angle_label = ttk.Label(inputr_frame, textvariable=self.app.wrap_angle_var)
        wrap_angle_label.grid(row=0, column=3, padx=10, pady=10, sticky="w")

        #Lean Angle Entry
        ttk.Label(inputr_frame, text="Blade Lean Angle:").grid(row=1, column=2, padx=10, pady=10, sticky="w")
        self.app.lean_angle_deg_entry = ttk.Entry(inputr_frame)
        self.app.lean_angle_deg_entry.grid(row=1, column=3, padx=10, pady=10, sticky="w")

        # Buttons - Get, Edit, Lean
        get_button = ttk.Button(inputl_frame, text="Get Curves", command=self.get_curves)
        get_button.grid(row=0, column=2, padx=10, pady=5)

        # Create a flag to track edit state
        self.is_editing = tk.BooleanVar(value=False)
        self.edit_button = ttk.Button(inputl_frame, text="Edit BAD Curve", command=self.toggle_edit, state="disabled")
        self.edit_button.grid(row=2, column=1, padx=10, pady=5)

        self.apply_lean_button = ttk.Button(inputr_frame, text="Apply Lean", command=self.apply_lean, state="disabled")
        self.apply_lean_button.grid(row=1, column=4, padx=30, pady=5)

        # BAD Distribution Graph Frame
        bad_dist_frame = ttk.LabelFrame(left_frame, text="Beta Distribution Curve", relief="ridge")
        bad_dist_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        bad_dist_frame.pack_propagate(False)

        # RIGHT SIDE (GH and Radial Graphs)
        right_frame = ttk.Frame(self)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        right_frame.rowconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=3)
        right_frame.grid_propagate(False)

        # GH Frame (top right)
        gh_frame = ttk.LabelFrame(right_frame, text="GH Plane View", relief="ridge")
        gh_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        gh_frame.pack_propagate(False)

        # Radial Frame (bottom right)
        radial_frame = ttk.LabelFrame(right_frame, text="Radial Distribution", relief="ridge")
        radial_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        radial_frame.pack_propagate(False)

        # Create canvases
        self.bad_dist_canvas = tk.Canvas(bad_dist_frame, bg="white")
        self.bad_dist_canvas.pack(fill="both", expand=True)
        self.gh_canvas = tk.Canvas(gh_frame, bg="white")
        self.gh_canvas.pack(fill="both", expand=True)
        self.radial_canvas = tk.Canvas(radial_frame, bg="white")
        self.radial_canvas.pack(fill="both", expand=True)

    def get_curves(self):
        if self.app.option.get() not in ("Linear Distribution", "UCu Distribution"):
            messagebox.showerror("Distribution Method", "Choose Linear Distribution or UCu Distribution.")
            return False
        beta_distribution(self.app.option.get(), self.bad_dist_canvas, self.gh_canvas, self.radial_canvas, self.gv, self.app, self)
        self.current_option = self.app.option.get()
        self.curve_generated = True
        self.edit_button.config(state="normal") # Enable the edit button after generating curves
        self.apply_lean_button.config(state="normal") 
        if hasattr(self.app, "mark_design_step_complete"):
            self.app.mark_design_step_complete(3)

    def toggle_edit(self):
        if not self.curve_generated or self.interactive_plot is None:
            return
            
        if not self.is_editing.get():
            self.is_editing.set(True) # Start editing
            self.edit_button.config(text="Done Editing & Update")
            self.interactive_plot.plot_curve(interactive=True, show_control_points=True) # Show control points and enable interactivity
        else:
            self.is_editing.set(False) # Finish editing and update other plots
            self.edit_button.config(text="Edit BAD Curve")
            self.interactive_plot.plot_curve(interactive=False, show_control_points=False) # Hide control points and disable interactivity
            self.update_dependent_plots() # Update the other two plots

    def apply_lean(self):
        plot_leaned(self.radial_canvas, self.gv, self.app)

    def update_dependent_plots(self): #Update GH and radial plots based on modified control points
        if self.interactive_plot is None:
            return
        
        bzP = self.interactive_plot.bezier_points # Get the current bezier points
        
        update_plots_from_bezier(bzP, self.current_option, self.gh_canvas, self.radial_canvas, self.gv, self.app) # Update the plots using the modified curve


def beta_distribution(option, bad_dist_canvas, gh_canvas, radial_canvas, gv, app, tab_instance=None):
    fig_bad, ax_bad = plt.subplots(figsize=(10,5))
    fig_gh, ax_gh = plt.subplots(figsize=(5,5))
    fig_po, ax_po = plt.subplots(subplot_kw={'projection': 'polar'})

    p = gv.cpoints
    P, L = gv.Rmat.shape
    
    # Initialize control points based on distribution type
    if isinstance(getattr(gv, "bad_distribution_control_points", None), np.ndarray):
        saved_points = gv.bad_distribution_control_points
        if saved_points.shape == (5, 2):
            control_points = saved_points.copy()
        else:
            control_points = None
    else:
        control_points = None

    if control_points is None:
        if option == "Linear Distribution":
            #control_points = np.array([[0, 0], [0.25, 0.25], [0.5, 0.5], [0.75, 0.75], [1, 1]])
            control_points = np.array([[0, 1], [0.25, 0.75], [0.5, 0.5], [0.75, 0.25], [1, 0]])
        else:  # UCu Distribution
            #control_points = np.array([[0, 0], [0.25, 0.05], [0.45, 0.23], [0.75, 0.88], [1, 1]])
            control_points = np.array([[0, 1], [0.25, 0.88], [0.45, 0.23], [0.75, 0.05], [1, 0]])
        
    
    # Create interactive plot instance
    if tab_instance:
        tab_instance.interactive_plot = InteractiveBezierPlot(fig_bad, ax_bad, control_points, gv)
        tab_instance.interactive_plot.option = option
        # Initially plot without visible control points
        tab_instance.interactive_plot.plot_curve(interactive=False, show_control_points=False)
    
    gv.bad_distribution_control_points = np.array(control_points, copy=True)

    # Generate Bezier curve
    bzP = BezierCurve(control_points, p)
    gv.blade_span = bzP[:, 0]
    
    # Perform calculations and plot other graphs
    calculate_and_plot(bzP, option, ax_gh, ax_po, gv, app)
    
    # Embed plots in canvases
    embed_plots(fig_bad, fig_gh, fig_po, bad_dist_canvas, gh_canvas, radial_canvas)

# Update GH and radial plots from modified Bezier curve
def update_plots_from_bezier(bzP, option, gh_canvas, radial_canvas, gv, app):
    fig_gh, ax_gh = plt.subplots(figsize=(5,5))
    fig_po, ax_po = plt.subplots(subplot_kw={'projection': 'polar'})
    
    # Perform calculations with modified curve
    calculate_and_plot(bzP, option, ax_gh, ax_po, gv, app)
    
    # Embed updated plots
    embed_plots(None, fig_gh, fig_po, None, gh_canvas, radial_canvas)


def render_bad_from_bezier(bzP, bad_dist_canvas, gv, option):
    fig_bad, ax_bad = plt.subplots(figsize=(10, 5))
    ax_bad.plot(bzP[:, 0], bzP[:, 1], 'b-', linewidth=2)
    ax_bad.set_xlabel("LE<-------------  Blade Span  ------------->TE")
    if option == "Linear Distribution":
        ax_bad.set_ylabel("Beta Angle")
    else:
        ax_bad.set_ylabel("UCu")
    ax_bad.grid(True, alpha=0.3)
    embed_plots(fig_bad, None, None, bad_dist_canvas, None, None)

# Perform calculations and plot GH and polar graphs
def calculate_and_plot(bzP, option, ax_gh, ax_po, gv, app):
    gv.bad_distribution_points = np.array(bzP, copy=True)
    gv.bad_distribution_method = option
    gv.blade_span = bzP[:, 0]
    P, L = gv.Rmat.shape
    gv.Umat = np.zeros((P, L))
    gv.Cumat = np.zeros((P, L))
    gv.Wmat = np.zeros((P, L))
    gv.UCumat = np.zeros((P, L))
    gv.Gmat = np.zeros((P, L))
    gv.Hmat = np.zeros((P, L))
    gv.beta = np.zeros((P, L))
    gv.UCuRelativemat = np.zeros((P, L))


    gv.UCuRelativematPM = np.zeros((P, L))
    gv.UmatPM = np.zeros((P, L))
    gv.CumatPM = np.zeros((P, L))
    gv.UCumatPM = np.zeros((P, L))
    gv.WmatPM = np.zeros((P, L))


    if option == "Linear Distribution":
        # Initialize first row values
        gv.UCumat[0, :] = gv.turbine_in["u1"] * gv.turbine_in["cu1"]
        gv.Umat[0, :] = gv.turbine_in["u1"]
        gv.Wmat[0, :] = gv.turbine_in["w1"]
        gv.Cumat[0, :] = gv.turbine_in["cu1"]
        gv.beta[0, :] = gv.turbine_in["beta1_deg"]

        # Initialize matrices as zero
        beta_1vect = np.zeros(L)
        deltabetaRelative = np.zeros((P, L))
        deltabeta = np.zeros((P, L))

        # Loop through the lines and update beta_1vect, deltabetaRelative
        for l in range(L):
            beta_1vect[l] = gv.turbine_in["beta1_deg"] * np.pi / 180
            deltabetaRelative[:, l] = bzP[:, 1]

        # Calculate beta_2vect and deltabetavect
        beta_2vect = np.arctan(gv.C_mMat[-1, :] / (gv.omega_tm * gv.Rmat[-1, :]))
        deltabetavect = beta_1vect - beta_2vect

        # Update deltabeta and beta
        for l in range(L):
            deltabeta[:, l] = deltabetaRelative[:, l] * deltabetavect[l]
            gv.beta[:, l] = deltabeta[:, l] + beta_2vect[l]

        # Loop through the points to calculate gv.Gmat & update gv.Hmat
        for l in range(L):
            for p in range(1, P):
                gv.Gmat[p, l] = gv.Gmat[p - 1, l] + np.sqrt((gv.Rmat[p, l] - gv.Rmat[p - 1, l]) ** 2 + (gv.Zmat[p, l] - gv.Zmat[p - 1, l]) ** 2)
                deltaG = gv.Gmat[p, l] - gv.Gmat[p - 1, l]
                deltaH = deltaG / np.tan(gv.beta[p, l])
                gv.Hmat[p, l] = gv.Hmat[p - 1, l] + deltaH

    elif option == "UCu Distribution":
        Point, Line = gv.Rmat.shape
        Relative = gv.turbine_in["u1"] * gv.turbine_in["cu1"]
        #Relative = gv.pump_out["u1"] * gv.pump_out["cu1"]
        gv.Umat = gv.omega_tm * gv.Rmat # omega = 2 * pi * N / 60....calculated u at every radial point

        for l in range(Line):
            gv.UCuRelativemat[:, l] = bzP[:, 1]

        gv.UCumat = gv.UCuRelativemat * Relative
        gv.Cumat = gv.UCumat / gv.Umat
        Wumat = gv.Umat - gv.Cumat

        for l in range(Line):
            for p in range(Point):
                if Wumat[p, l] > 0:
                    gv.beta[p, l] = np.degrees(m.atan(gv.C_mMat[p, l] / Wumat[p, l]))
                else:
                    gv.beta[p, l] = 180 + np.degrees(m.atan(gv.C_mMat[p, l] / Wumat[p, l]))

        gv.Wmat = gv.C_mMat / np.sin(np.radians(gv.beta))

        for l in range(Line):
            for p in range(1, Point):
                gv.Gmat[p, l] = gv.Gmat[p - 1, l] + np.sqrt((gv.Rmat[p - 1, l] - gv.Rmat[p, l]) ** 2 + (gv.Zmat[p - 1, l] - gv.Zmat[p, l]) ** 2)
                deltaG = gv.Gmat[p, l] - gv.Gmat[p - 1, l]
                deltaH = deltaG / np.tan(np.radians(gv.beta[p, l]))
                gv.Hmat[p, l] = gv.Hmat[p - 1, l] + deltaH

        """ #___________________PM Energy Distribution_____________________
        RelativePM = gv.pump_out["u1"] * gv.pump_out["cu1"]
        gv.UmatPM = gv.omega_pm * gv.Rmat[::-1, :] 

        for l in range(Line):
            gv.UCuRelativematPM[:, l] = bzP[::-1, 1]

        gv.UCumatPM = gv.UCuRelativematPM * RelativePM
        gv.CumatPM = gv.UCumatPM / gv.UmatPM
        gv.WmatPM = gv.C_mMatPM / np.sin(np.radians(gv.beta[::-1]))

        #__________________________________________________________________ """

    # GH Plane graph (Top View)
    ax_gh.plot(-gv.Gmat, -gv.Hmat, marker='x', linestyle='-', markersize=0.2, label="GH Plane Curve")
    ax_gh.set_xlabel("G")
    ax_gh.set_ylabel("H")

    # Initialize gv.Theta to store the full theta matrix
    gv.Theta = np.zeros_like(gv.Rmat)

    # Loop to incrementally calculate theta from deltaH and Rmat
    for p in range(1, P):
        deltaH = gv.Hmat[p, :] - gv.Hmat[p - 1, :]
        gv.Theta[p, :] = gv.Theta[p - 1, :] + deltaH / gv.Rmat[p, :]

    # Plot the radial view
    ax_po.plot(gv.Theta, gv.Rmat)
    ax_po.set_yticklabels([])
    ax_po.grid(True)

    
    # CACLCULATING AND DISPLAYING MAX WRAP 
    # For each streamline (Line), sum all theta values and find the maximum among each
    streamlines_wrap = []

    for line in range(L):  # Loop through each streamline
        theta_line = gv.Theta[:, line]  # Get all theta values for this streamline
        wrap_angle = theta_line[-1] - theta_line[0]  # Total span: last - first
        streamlines_wrap.append(wrap_angle)

    # Get maximum wrap and convert to degrees
    max_wrap_angle_deg = np.degrees(max(streamlines_wrap))

    # Update the GUI label with the calculated value
    app.wrap_angle_var.set(f"{max_wrap_angle_deg:.2f}°")

"""     print("\n=== Mid Streamline ===")
    print(f"   G: {gv.Gmat[:,5]}")
    print(f"   H: {gv.Hmat[:,5]}")
    print(f"   Beta: {gv.beta[:,5]}")
    print(f"   Theta: {gv.Theta[:,5]}")
    print(f"   R: {gv.Rmat[:,5]}") """


# Embed matplotlib figures in tkinter canvases
def embed_plots(fig_bad, fig_gh, fig_po, bad_dist_canvas, gh_canvas, radial_canvas):
    if fig_bad and bad_dist_canvas:
        # Clear and embed BAD canvas
        for widget in bad_dist_canvas.winfo_children():
            widget.destroy()
        bad_plot = FigureCanvasTkAgg(fig_bad, master=bad_dist_canvas)
        bad_plot.draw()
        bad_plot.get_tk_widget().pack(fill="both", expand=True)

    if fig_gh and gh_canvas:
        # Clear and embed GH canvas
        for widget in gh_canvas.winfo_children():
            widget.destroy()
        gh_plot = FigureCanvasTkAgg(fig_gh, master=gh_canvas)
        gh_plot.draw()

        """ # Add toolbar for interactive navigation
        toolbar = NavigationToolbar2Tk(gh_plot, gh_canvas)
        toolbar.update()

        # Place toolbar vertically on the right
        toolbar.pack(side=tk.RIGHT, fill=tk.Y)
        for widget in toolbar.winfo_children():
            widget.pack_configure(side=tk.TOP, padx=2, pady=2) """
        gh_plot.get_tk_widget().pack(side=tk.LEFT, fill="both", expand=True)

    if fig_po and radial_canvas:
        # Clear and embed POLAR canvas
        for widget in radial_canvas.winfo_children():
            widget.destroy()
        po_plot = FigureCanvasTkAgg(fig_po, master=radial_canvas)
        po_plot.draw()
        po_plot.get_tk_widget().pack(fill="both", expand=True)


def plot_leaned(radial_canvas, gv, app):
    Point, Line = gv.Rmat.shape
    fig_po, ax_po = plt.subplots(subplot_kw={'projection': 'polar'})

    ### Apply Lean as Initial Theta Offset
    theta_max_lean_deg = int(app.lean_angle_deg_entry.get()) if app.lean_angle_deg_entry.get() else -5
    theta_max_lean = np.radians(theta_max_lean_deg)

    # Inserting default lean
    if not app.lean_angle_deg_entry.get():
        app.lean_angle_deg_entry.insert(0, str(theta_max_lean_deg))

    # Initialize gv.Theta to store the full theta matrix
    gv.Theta = np.zeros_like(gv.Rmat)

    # Create base theta offset per streamline _____ tp produce linear blade lean
    theta_offset = np.linspace(0, theta_max_lean, gv.ns)

    # Broadcasting the lean offset along each point in streamline
    for l in range(gv.ns):
        gv.Theta[:, l] = theta_offset[l]

    # Loop to incrementally calculate theta from deltaH and Rmat
    for p in range(1, Point):
        deltaH = gv.Hmat[p, :] - gv.Hmat[p - 1, :]
        gv.Theta[p, :] = gv.Theta[p - 1, :] + deltaH / gv.Rmat[p, :]

    # Plot the radial view
    ax_po.plot(gv.Theta, gv.Rmat)
    ax_po.set_yticklabels([])
    ax_po.grid(True)


    # Clear and embed POLAR canvas
    for widget in radial_canvas.winfo_children():
        widget.destroy()
    po_plot = FigureCanvasTkAgg(fig_po, master=radial_canvas)
    po_plot.draw()
    po_plot.get_tk_widget().pack(fill="both", expand=True)


def BezierCurve(p, m):
    t = np.linspace(0, 1, m)
    n = len(p) - 1

    Bx = np.zeros(m)
    By = np.zeros(m)

    for i in range(n + 1):
        binomial_coeff = comb(n, i)
        Bx += binomial_coeff * (1 - t)**(n - i) * t**i * p[i, 0]
        By += binomial_coeff * (1 - t)**(n - i) * t**i * p[i, 1]

    return np.column_stack((Bx, By))

class InteractiveBezierPlot:
    def __init__(self, fig, ax, control_points, gv, update_callback=None):
        self.fig = fig
        self.ax = ax
        self.gv = gv
        self.control_points = control_points.copy()
        self.original_points = control_points.copy()
        self.update_callback = update_callback
        self.selected_point = None
        self.is_interactive = False
        
        # Plot elements
        self.curve_line = None
        self.control_scatter = None
        self.bezier_points = None
        
        # Event connections
        self.press_event = None
        self.release_event = None
        self.motion_event = None
        self.key_event = None

    # Plot the Bezier curve and control points optionally 
    def plot_curve(self, interactive=False, show_control_points=False):

        self.ax.clear()
        
        # Generate Bezier curve
        self.bezier_points = self.BezierCurve(self.control_points, self.gv.cpoints)
        
        # Plot curve
        self.curve_line, = self.ax.plot(self.bezier_points[:, 0], self.bezier_points[:, 1], 'b-', linewidth=2)
        
        if show_control_points:
            # Plot control points
            self.control_scatter = self.ax.scatter(self.control_points[:, 0], self.control_points[:, 1], color="blue", s=40, zorder=5, picker=True)
        
        # Axis Labelling
        self.ax.set_xlabel("LE<-------------  Blade Span  ------------->TE")
        if hasattr(self, 'option') and self.option == "Linear Distribution":
            self.ax.set_ylabel("Beta Angle")
        else:
            self.ax.set_ylabel("UCu")
        
        self.ax.grid(True, alpha=0.3)
        self.is_interactive = interactive
        
        if interactive and show_control_points:
            self.connect_events()
        else:
            self.disconnect_events()
        
        self.fig.canvas.draw()
    
    # Connect mouse events for interactivity
    def connect_events(self):
        self.press_event = self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.release_event = self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.motion_event = self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
    
    # Disconnect all events
    def disconnect_events(self):
        if self.press_event:
            self.fig.canvas.mpl_disconnect(self.press_event)
        if self.release_event:
            self.fig.canvas.mpl_disconnect(self.release_event)
        if self.motion_event:
            self.fig.canvas.mpl_disconnect(self.motion_event)
    
    # Handling mouse press events
    def on_press(self, event):
        if not self.is_interactive or event.inaxes != self.ax or self.control_scatter is None:
            return
        
        # Find closest control point
        x_coords = self.control_points[:, 0]
        y_coords = self.control_points[:, 1]
        distances = np.sqrt((x_coords - event.xdata)**2 + (y_coords - event.ydata)**2)
        
        if np.min(distances) < 0.05:  # Threshold for selection
            self.selected_point = np.argmin(distances)
            self.update_point_colors() # Update colors to show selection
    
    # Handle mouse release events
    def on_release(self, event):
        if self.selected_point is not None:
            self.selected_point = None
            self.update_point_colors() # Reset colors when releasing
    
    # Handle mouse motion events
    def on_motion(self, event):
        if not self.is_interactive or self.selected_point is None or event.inaxes != self.ax:
            return
        
        # Update control point position
        if self.selected_point == 0 or self.selected_point == len(self.control_points) - 1:
            self.control_points[self.selected_point, 1] = max(0, min(1, event.ydata)) # First and last points: only allow movement in y-direction
        else:
            # Middle points: allow both x and y movement
            self.control_points[self.selected_point, 0] = max(0, min(1, event.xdata))
            self.control_points[self.selected_point, 1] = max(0, min(1, event.ydata))
        
        self.update_plot()
    
    # Update the plot with new control points
    def update_plot(self):
        # Regenerate Bezier curve
        self.bezier_points = self.BezierCurve(self.control_points, self.gv.cpoints)

        if hasattr(self.gv, "bad_distribution_control_points"):
            self.gv.bad_distribution_control_points = np.array(self.control_points, copy=True)
        
        # Update curve
        self.curve_line.set_data(self.bezier_points[:, 0], self.bezier_points[:, 1])
        
        if self.control_scatter is not None:
            # Update control points
            self.control_scatter.set_offsets(np.column_stack((self.control_points[:, 0], self.control_points[:, 1])))
        
        # Update point colors
        self.update_point_colors()
        
        self.fig.canvas.draw()
    
    # Update control point colors based on selection
    def update_point_colors(self):
        if self.control_scatter is None:
            return
        
        colors = []
        base_color = "blue"  # Default color for all control points
        selected_color = "orange"  # Highlight color for selected point
        
        for i in range(len(self.control_points)):
            if i == self.selected_point:
                colors.append(selected_color)
            else:
                colors.append(base_color)
        
        self.control_scatter.set_color(colors) # Update scatter plot colors
    
    def BezierCurve(self, p, m):
        t = np.linspace(0, 1, m)
        n = len(p) - 1
        
        Bx = np.zeros(m)
        By = np.zeros(m)
        
        for i in range(n + 1):
            binomial_coeff = comb(n, i)
            Bx += binomial_coeff * (1 - t)**(n - i) * t**i * p[i, 0]
            By += binomial_coeff * (1 - t)**(n - i) * t**i * p[i, 1]
        
        return np.column_stack((Bx, By))
