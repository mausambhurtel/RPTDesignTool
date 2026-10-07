import tkinter as tk
from tkinter import ttk, messagebox
import math as m
import numpy as np
from scipy.special import comb
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from scipy.interpolate import interp1d
from shapely.geometry import LineString, Point
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from PIL import Image, ImageTk
from matplotlib.patches import FancyArrowPatch

class tab3_content(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.gv = app.gv
        self.edit_mode = False
        self.selected_point = None
        self.dragging = False
        
        # Store editable control points
        self.editable_shroud_indices = [1, 2, 3]  # mvscp2, mvscp3, mvscp4
        self.editable_outlet_indices = [1, 2]     # mvocp2, mvocp3
        
        # Initialize attributes that will be set later
        self.canvas = None
        self.fig = None
        self.ax = None
        self.mvscps = None
        self.mvocps = None
        self.outletLine = None
        self._design_needs_refresh = True
        self._default_hub_entry_text = None
        
        self.frame()

    def frame(self):
        # Configure grid weights for responsiveness
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        # Create frames for the input data and meridional plot sections
        input_frame = ttk.Frame(self, relief="ridge", padding=5)
        meridional_frame = ttk.Frame(self, relief="ridge", padding=5)
        image_frame = ttk.Frame(self, relief="flat")

        # Arrange the frames using grid
        input_frame.grid(row=0, column=0, sticky="nsew")
        meridional_frame.grid(row=0, column=1, rowspan=2, sticky="nsew")
        image_frame.grid(row=1, column=0, sticky="nsew")

        # Configure input frame for centering
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(0, weight=1)
        input_frame.rowconfigure(1, weight=1)
        input_frame.rowconfigure(2, weight=1)

        # Create a centered container within input frame
        frame4centeringwidgets = ttk.Frame(input_frame)
        frame4centeringwidgets.grid(row=1, column=0, sticky="ns")

        #ttk.Label(input_frame, text="Input Values", font=("Arial", 12)).grid(row=0, column=0, columnspan=2, padx=5, pady=10, sticky="n")

        # For "No. of Streamlines"
        ttk.Label(frame4centeringwidgets, text="No. of Streamlines:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.app.no_streamlines_spinbox = ttk.Spinbox(frame4centeringwidgets, from_=3, to=50, width=10)
        self.app.no_streamlines_spinbox.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # For Hub Outlet Diameter
        ttk.Label(frame4centeringwidgets, text="Hub Outlet Diameter, D_hub:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.app.d_hub_entry = ttk.Entry(frame4centeringwidgets, width=10)
        self.app.d_hub_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Get Axial View button (unchanged)
        self.get_axial_button = ttk.Button(frame4centeringwidgets, text="Update Axial View", command=self.get_axial_view)
        self.get_axial_button.grid(row=4, column=0, columnspan=2, padx=5, pady=30, sticky="nsew")

        # New Edit Axial View button
        self.edit_av_button = ttk.Button(frame4centeringwidgets, text="Edit Axial View", command=self.toggle_edit_mode, state='disabled')
        self.edit_av_button.grid(row=5, column=0, columnspan=2, padx=5, pady=0, sticky="nsew")


        image_path = 'meridional.png'
        # Load meridional image file
        image = Image.open(image_path)
        # Resize image if needed
        image = image.resize((300, 150), Image.Resampling.LANCZOS)
        # Convert to PhotoImage for tkinter
        self.photo = ImageTk.PhotoImage(image)
        image_frame.configure(width=300, height=150)
        image_frame.grid_propagate(False)  # Prevent frame from shrinking
        
        # Create label with image
        image_label = ttk.Label(image_frame, image=self.photo)
        image_label.place(relx=0.5, rely=0.5, anchor='center')
            
        # Populate the "Meridional Contour" frame
        ttk.Label(meridional_frame, text="Meridional Contour", font=("Arial", 12)).pack(pady=5)
        self.app.meridional_canvas = tk.Canvas(meridional_frame, bg="white")
        self.app.meridional_canvas.pack(fill="both", expand=True)

    def get_axial_view(self):
        used_default_hub = not self.app.d_hub_entry.get().strip()
        try:
            meridional_plot(self.app, self.gv, self)
        except (ValueError, KeyError, ZeroDivisionError) as error:
            messagebox.showerror("Meridional View", f"Could not generate the meridional view:\n{error}")
            return False
        if used_default_hub:
            self._default_hub_entry_text = self.app.d_hub_entry.get()
        self._design_needs_refresh = False
        # Enable the edit button after generating the plot
        self.edit_av_button.config(state='normal')
        if hasattr(self.app, "mark_design_step_complete"):
            self.app.mark_design_step_complete(2)
        return True

    def invalidate_design(self):
        """Discard the old contour when another main-dimensions condition is selected."""
        self._design_needs_refresh = True
        self.edit_mode = False
        self.interaction_enabled = False
        self.selected_point = None
        self.dragging = False
        self.edit_av_button.config(state="disabled", text="Edit Axial View")
        for widget in self.app.meridional_canvas.winfo_children():
            widget.destroy()
        if self.fig is not None:
            plt.close(self.fig)
        self.canvas = self.fig = self.ax = None
        self.mvscps = self.mvocps = self.outletLine = None
        # Recompute an automatically filled diameter, while preserving custom input.
        if self.app.d_hub_entry.get() == self._default_hub_entry_text:
            self.app.d_hub_entry.delete(0, tk.END)
        self._default_hub_entry_text = None

    def refresh_if_needed(self):
        if self._design_needs_refresh:
            return self.get_axial_view()
        return True

    def toggle_edit_mode(self):
        self.setup_interactive_plot()
        if not self.edit_mode:
            self.enable_editing()
            self.edit_av_button.config(text="Done Editing")
        else:
            self.disable_editing()
            self.edit_av_button.config(text="Edit Axial View")

    def setup_interactive_plot(self):
        if self.canvas is None:
            print("Warning: Canvas not initialized. Cannot setup interactive plot.")
            return
            
        self.fig = self.canvas.figure
        self.ax = self.fig.axes[0]
        self.ax.set_aspect('equal')
        
        # Connect mouse events
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_drag)

    def on_click(self, event):
        if not hasattr(self, 'interaction_enabled') or not self.interaction_enabled or event.inaxes != self.ax:
            return
            
        click_tolerance = 0.05
        
        # Check shroud control points
        for i in self.editable_shroud_indices:
            point = self.mvscps[i]
            distance = np.sqrt((event.xdata - point[0])**2 + (event.ydata - point[1])**2)
            if distance < click_tolerance:
                self.selected_point = ('shroud', i)
                self.dragging = True
                self.update_plot_colors()
                return
        
        # Check outlet control points
        for i in self.editable_outlet_indices:
            point = self.mvocps[i]
            distance = np.sqrt((event.xdata - point[0])**2 + (event.ydata - point[1])**2)
            if distance < click_tolerance:
                self.selected_point = ('outlet', i)
                self.dragging = True
                self.update_plot_colors()
                return
        
        # If no point selected, deselect current selection
        if self.selected_point:
            self.selected_point = None
            self.update_plot_colors()

    def on_drag(self, event):
        if not self.dragging or not self.selected_point or event.inaxes != self.ax:
            return
            
        point_type, point_index = self.selected_point
        
        # Update the control point position
        if point_type == 'shroud':
            self.mvscps[point_index] = [event.xdata, event.ydata]
        elif point_type == 'outlet':
            self.mvocps[point_index] = [event.xdata, event.ydata]
        
        # Recalculate and update the plot in real-time
        self.recalculate_curves()
        self.update_plot_colors()

    def on_release(self, event):
        self.dragging = False

    def enable_editing(self):
        self.edit_mode = True
        self.interaction_enabled = True
        self.update_plot_colors()

    def disable_editing(self):
        self.edit_mode = False
        self.interaction_enabled = False
        self.selected_point = None
        self.dragging = False
        self.update_plot_colors()

    def update_plot_colors(self):
        if self.ax is None:
            return
            
        self.ax.clear()
        self.plot_streamlines_and_points()
        self.canvas.draw()

    def find_intersection_points(self, temp_Rmat=None, temp_Zmat=None):
        # Use temporary matrices if provided, otherwise use main matrices
        R_matrix = temp_Rmat if temp_Rmat is not None else self.gv.Rmat
        Z_matrix = temp_Zmat if temp_Zmat is not None else self.gv.Zmat
        
        intersection_indices = {}
        
        for SL in range(self.gv.ns):
            min_distance = float('inf')
            best_idx = len(R_matrix) - 1
            
            for SLP in range(len(R_matrix)):
                for OLP in range(len(self.outletLine)):
                    distance = np.sqrt((R_matrix[SLP, SL] - self.outletLine[OLP, 0]) ** 2 + 
                                     (Z_matrix[SLP, SL] - self.outletLine[OLP, 1]) ** 2)
                    if distance < min_distance:
                        min_distance = distance
                        best_idx = SLP
            
            intersection_indices[SL] = best_idx
        
        return intersection_indices

    def update_outlet_control_points(self, temp_Rmat=None, temp_Zmat=None):
        # Use temporary matrices if provided, otherwise use main matrices
        R_matrix = temp_Rmat if temp_Rmat is not None else self.gv.Rmat
        Z_matrix = temp_Zmat if temp_Zmat is not None else self.gv.Zmat
        
        # mvocp1 stays at shroud outlet
        mvocp1 = np.array([R_matrix[-1, 0], Z_matrix[-1, 0]])
        
        # Find mvocp4 based on hub outlet diameter
        hub_outlet_radius = self.gv.gd["D_hub"] / 2
        radius_diff = np.abs(R_matrix[:, -1] - hub_outlet_radius)
        nearest_index = np.argmin(radius_diff)
        mvocp4 = np.array([R_matrix[nearest_index, -1], Z_matrix[nearest_index, -1]])
        
        # Update mvocp2 and mvocp3 to maintain their relative positions
        # If they were being dragged, keep their current positions
        # Otherwise, recalculate based on the new endpoints
        if self.selected_point is None or self.selected_point[0] != 'outlet':
            direction = mvocp4 - mvocp1
            perp_direction = np.array([-direction[1], direction[0]])
            if np.linalg.norm(perp_direction) > 0:
                perp_direction = perp_direction / np.linalg.norm(perp_direction)
            total_dist = np.linalg.norm(direction)
            offset = 0.1 * total_dist
            base_mvocp2 = mvocp1 + direction * (1 / 3)
            base_mvocp3 = mvocp1 + direction * (2 / 3)

            mvocp2 = base_mvocp2 + perp_direction * offset
            mvocp3 = base_mvocp3 + perp_direction * offset
            
            # Update the control points array
            self.mvocps[1] = mvocp2
            self.mvocps[2] = mvocp3
        
        # Always update the endpoints
        self.mvocps[0] = mvocp1
        self.mvocps[3] = mvocp4

    def plot_streamlines_and_points(self):
        if self.mvscps is None or self.mvocps is None or self.outletLine is None:
            return
        
        # Only plot control points when in edit mode
        if hasattr(self, 'edit_mode') and self.edit_mode:
            # Plot shroud control points
            for i, point in enumerate(self.mvscps):
                if i in self.editable_shroud_indices:
                    color = 'orange' if self.selected_point == ('shroud', i) else 'blue'
                else:
                    color = 'red'
                self.ax.scatter(point[0], point[1], color=color, s=40, zorder=5)

            # Plot outlet control points
            for i, point in enumerate(self.mvocps):
                if i in self.editable_outlet_indices:
                    color = 'orange' if self.selected_point == ('outlet', i) else 'blue'
                else:
                    color = 'red'
                self.ax.scatter(point[0], point[1], color=color, s=40, zorder=5)
            
        # Find intersection points for proper streamline trimming
        intersection_points = self.find_intersection_points()
            
        # Plot streamlines with arrows
        for L in range(self.gv.ns):
            # Get the trimmed streamline up to intersection point
            end_idx = intersection_points.get(L, len(self.gv.Rmat))
            end_idx = min(end_idx, len(self.gv.Rmat) - 1)
            
            R_trimmed = self.gv.Rmat[:end_idx+1, L]
            Z_trimmed = self.gv.Zmat[:end_idx+1, L]
            
            
            n_arrows = 20
            stride = max(1, int(self.gv.cpoints / n_arrows))
            self.ax.plot(R_trimmed, Z_trimmed, color="black", linewidth=1)

            for P in range(stride, len(R_trimmed) - 1, stride):
                arrow = FancyArrowPatch(
                    (R_trimmed[P], Z_trimmed[P]),
                    (R_trimmed[P + 1], Z_trimmed[P + 1]),
                    arrowstyle='->',
                    linewidth=1,
                    color='black',
                    mutation_scale=8
                )
                self.ax.add_patch(arrow)

        # Plot inlet line
        x_coords = [self.gv.Rmat[0, 0], self.gv.Rmat[0, self.gv.ns - 1]]
        y_coords = [self.gv.Zmat[0, 0], self.gv.Zmat[0, self.gv.ns - 1]]
        self.ax.plot(x_coords, y_coords, color='k', linewidth=1, label='Inlet Line')
        
        # Plot outlet line
        self.ax.plot(self.outletLine[:, 0], self.outletLine[:, 1], color='k', linewidth=1, label='Outlet Line')

    def recalculate_curves(self):
        # Recalculate Bezier curves with updated control points
        shroud_bezier_curve_points = BezierCurve(self.mvscps, 500)
        distributed_points = Distribute(shroud_bezier_curve_points, 500)
        
        # Create temporary matrices with 500 points for calculations
        espoints = 500
        temp_Rmat = np.zeros((espoints, self.gv.ns))
        temp_Zmat = np.zeros((espoints, self.gv.ns))
        
        # Update shroud streamline
        temp_Rmat[:, 0] = distributed_points[:, 0]
        temp_Zmat[:, 0] = distributed_points[:, 1]
        
        # Initialize streamline starting points
        temp_Rmat[0, :] = temp_Rmat[0, 0]
        for L in range(1, self.gv.ns):
            temp_Zmat[0, L] = temp_Zmat[0, 0] + self.gv.gd["B0"] * (L / (self.gv.ns - 1))
        
        # Recalculate streamlines with 500 points
        self.calculate_streamlines(temp_Rmat, temp_Zmat, espoints)
        
        # Update outlet control points based on new hub line position
        self.update_outlet_control_points(temp_Rmat, temp_Zmat)
        
        # Recalculate outlet line with updated control points
        outlet_bzcurve_points = 200
        self.outletLine = BezierCurve(self.mvocps, outlet_bzcurve_points)
        
        # Find intersection points and redistribute to curve points
        intersection_points = self.find_intersection_points(temp_Rmat, temp_Zmat)
        self.redistribute_points(temp_Rmat, temp_Zmat, intersection_points)

    def calculate_streamlines(self, temp_Rmat, temp_Zmat, espoints):
        A2_per_stline = self.gv.gd["A2s"] / (self.gv.ns - 1)
        
        for L in range(1, self.gv.ns):
            for P in range(1, espoints - 1):
                dy = temp_Zmat[P - 1, L - 1] - temp_Zmat[P + 1, L - 1]
                dx = temp_Rmat[P - 1, L - 1] - temp_Rmat[P + 1, L - 1]
                if dx != 0:
                    theta = abs(np.arctan(dy / dx))
                    A_sec = (self.gv.gd["A1"] - (self.gv.gd["A1"] - self.gv.gd["A2s"]) * ((P - 1) / (espoints - 1))) / (self.gv.ns - 1)
                    
                    temp_Rmat[P, L] = np.sqrt(max(0, temp_Rmat[P, L - 1] ** 2 - A_sec * np.sin(theta) / np.pi))
                    if np.sin(theta) != 0:
                        temp_Zmat[P, L] = temp_Zmat[P, L - 1] - (temp_Rmat[P, L] - temp_Rmat[P, L - 1]) * np.cos(theta) / np.sin(theta)
            
            # Last point
            P = espoints - 1
            if L - 1 >= 0:
                temp_Rmat[P, L] = np.sqrt(max(0, temp_Rmat[P, L - 1] ** 2 - A2_per_stline / np.pi))
                temp_Zmat[P, L] = temp_Zmat[P, 0]

    def redistribute_points(self, temp_Rmat, temp_Zmat, intersection_points):
        p = self.gv.cpoints
        Rtemp = np.zeros((p, self.gv.ns))
        Ztemp = np.zeros((p, self.gv.ns))
        
        for L in range(self.gv.ns):
            end_idx = intersection_points.get(L, len(temp_Rmat) - 1)
            end_idx = min(end_idx, len(temp_Rmat) - 1)
            
            # Extract the streamline points up to intersection
            R_streamline = temp_Rmat[:end_idx+1, L]
            Z_streamline = temp_Zmat[:end_idx+1, L]
            
            # Calculate cumulative arc length along the streamline
            arc_lengths = np.zeros(len(R_streamline))
            for i in range(1, len(R_streamline)):
                arc_lengths[i] = arc_lengths[i-1] + np.sqrt(
                    (R_streamline[i] - R_streamline[i-1])**2 + 
                    (Z_streamline[i] - Z_streamline[i-1])**2
                )
            
            # Total arc length
            total_length = arc_lengths[-1]
            
            if total_length > 0:  # Avoid division by zero
                # Create equally spaced arc length positions
                target_arc_lengths = np.linspace(0, total_length, p)
                
                # Interpolate to find R and Z coordinates at equally spaced arc lengths
                from scipy.interpolate import interp1d
                
                # Create interpolation functions
                R_interp = interp1d(arc_lengths, R_streamline, kind='linear', 
                                bounds_error=False, fill_value='extrapolate')
                Z_interp = interp1d(arc_lengths, Z_streamline, kind='linear', 
                                bounds_error=False, fill_value='extrapolate')
                
                # Get redistributed points
                Rtemp[:, L] = R_interp(target_arc_lengths)
                Ztemp[:, L] = Z_interp(target_arc_lengths)
            else:
                # If streamline has zero length, just repeat the first point
                Rtemp[:, L] = R_streamline[0]
                Ztemp[:, L] = Z_streamline[0]
        
        # Update the main matrices with redistributed points
        self.gv.Rmat = Rtemp
        self.gv.Zmat = Ztemp
        
        # Update other matrices and properties
        self.update_velocity_and_geometry()

    def update_velocity_and_geometry(self):
        # Recalculate velocity components for the new point distribution
        self.gv.C_mMat = np.zeros_like(self.gv.Rmat)
        self.gv.C_mMatPM = np.zeros_like(self.gv.Rmat)
        for i in range(self.gv.Rmat.shape[1]):
            self.gv.C_mMat[:, i] = np.linspace(self.gv.turbine_in["cm1"], self.gv.turbine_out["cm2"], self.gv.Rmat.shape[0])
            self.gv.C_mMatPM[:, i] = np.linspace(self.gv.pump_in["cm2"], self.gv.pump_out["cm1"], self.gv.Rmat.shape[0])

        # Update hub and shroud points
        self.gv.HubXmat = self.gv.Rmat[:, -1]
        self.gv.HubZmat = self.gv.Zmat[:, -1]
        self.gv.ShroudXmat = self.gv.Rmat[:, 0]
        self.gv.ShroudZmat = self.gv.Zmat[:, 0]
        self.gv.HubYmat = np.zeros_like(self.gv.HubXmat)
        self.gv.ShroudYmat = np.zeros_like(self.gv.ShroudXmat)


def meridional_plot(app, gv, tab3_instance=None):
    gv.ns = int(app.no_streamlines_spinbox.get()) if app.no_streamlines_spinbox.get() else 12
    # Insert default values
    if not app.no_streamlines_spinbox.get():
        app.no_streamlines_spinbox.insert(0, str(gv.ns))

    # Calculate shroud control points
    mvscp1 = [gv.gd["D1"] / 2, gv.gd["B_hub"]]
    mvscp2 = [gv.gd["D1"] / 2 - 2 * (gv.gd["D1"] - gv.gd["D2"]) / 10, gv.gd["B_hub"] * 9 / 10]
    mvscp3 = [gv.gd["D1"] / 2 - 4 * (gv.gd["D1"] - gv.gd["D2"]) / 10, gv.gd["B_hub"] * 8 / 10]
    mvscp4 = [gv.gd["D2"] / 2, gv.gd["B_hub"] / 10]
    mvscp5 = [gv.gd["D2"] / 2, 0]

    mvscps = np.array([mvscp1, mvscp2, mvscp3, mvscp4, mvscp5])

    # Store control points in the tab3_content instance
    if tab3_instance:
        tab3_instance.mvscps = mvscps

    # Area calculations
    gv.gd["A1"] = m.pi * gv.gd["D1"] * gv.gd["B0"]
    gv.gd["Dx"] = 0.05 * gv.gd["D2"]
    gv.gd["A2"] = (m.pi * (gv.gd["D2"]) ** 2) / 4
    gv.gd["A2s"] = (m.pi * (gv.gd["D2"] - gv.gd["Dx"]) ** 2) / 4

    # Initialize matrices
    espoints = 500
    gv.Rmat = np.zeros((espoints, gv.ns))
    gv.Zmat = np.zeros((espoints, gv.ns))

    # Calculate shroud streamline
    shroud_bezier_curve_points = BezierCurve(mvscps, 200)
    distributed_points = Distribute(shroud_bezier_curve_points, espoints)

    gv.Rmat[:, 0] = distributed_points[:, 0]
    gv.Zmat[:, 0] = distributed_points[:, 1]

    # Initialize streamline starting points
    gv.Rmat[0, :] = gv.Rmat[0, 0]
    for L in range(1, gv.ns):
        gv.Zmat[0, L] = gv.Zmat[0, 0] + gv.gd["B0"] * (L / (gv.ns - 1))

    # Calculate streamlines using the helper function
    if tab3_instance:
        tab3_instance.calculate_streamlines(gv.Rmat, gv.Zmat, espoints)

    # Calculate velocity components
    gv.C_mMat = np.zeros_like(gv.Rmat)
    gv.C_mMatPM = np.zeros_like(gv.Rmat)
    for i in range(gv.Rmat.shape[1]):
        gv.C_mMat[:, i] = np.linspace(gv.turbine_in["cm1"], gv.turbine_out["cm2"], gv.Rmat.shape[0])
        gv.C_mMatPM[:, i] = np.linspace(gv.pump_in["cm2"], gv.pump_out["cm1"], gv.Rmat.shape[0])

    # Update hub and shroud points
    gv.HubXmat = gv.Rmat[:, -1]
    gv.HubZmat = gv.Zmat[:, -1]
    gv.ShroudXmat = gv.Rmat[:, 0]
    gv.ShroudZmat = gv.Zmat[:, 0]
    gv.HubYmat = np.zeros_like(gv.HubXmat)
    gv.ShroudYmat = np.zeros_like(gv.ShroudXmat)

    # Calculate outlet control points
    mvocp1 = np.array([gv.Rmat[-1, 0], gv.Zmat[-1, 0]])
    
    gv.gd["D_hub"] = float(app.d_hub_entry.get()) if app.d_hub_entry.get() else (0.5 * gv.gd["D2"])
    if not app.d_hub_entry.get():
        app.d_hub_entry.insert(0, str(gv.gd["D_hub"]))
    
    hub_outlet_radius = gv.gd["D_hub"] / 2
    radius_diff = np.abs(gv.Rmat[:, -1] - hub_outlet_radius)
    nearest_index = np.argmin(radius_diff)
    mvocp4 = np.array([gv.Rmat[nearest_index, -1], gv.Zmat[nearest_index, -1]])

    direction = mvocp4 - mvocp1
    perp_direction = np.array([-direction[1], direction[0]])
    perp_direction = perp_direction / np.linalg.norm(perp_direction)
    total_dist = np.linalg.norm(direction)
    offset = 0.1 * total_dist
    base_mvocp2 = mvocp1 + direction * (1 / 3)
    base_mvocp3 = mvocp1 + direction * (2 / 3)

    mvocp2 = base_mvocp2 + perp_direction * offset
    mvocp3 = base_mvocp3 + perp_direction * offset

    mvocps = np.array([mvocp1, mvocp2, mvocp3, mvocp4])
    
    # Store outlet control points
    if tab3_instance:
        tab3_instance.mvocps = mvocps

    # Generate outlet line
    outlet_bzcurve_points = 200
    outletLine = BezierCurve(mvocps, outlet_bzcurve_points)

    # Store outlet line
    if tab3_instance:
        tab3_instance.outletLine = outletLine

    # Find intersection points and redistribute
    intersection_points = {}
    for SL in range(gv.ns):
        min_distance = float('inf')
        best_idx = espoints - 1
        
        for SLP in range(espoints):
            for OLP in range(len(outletLine)):
                distance = np.sqrt((gv.Rmat[SLP, SL] - outletLine[OLP, 0]) ** 2 + 
                                 (gv.Zmat[SLP, SL] - outletLine[OLP, 1]) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    best_idx = SLP
        
        intersection_points[SL] = best_idx

    # Redistribute to no of points defined using the helper function
    if tab3_instance:
        tab3_instance.redistribute_points(gv.Rmat, gv.Zmat, intersection_points)

    # Clear previous plot
    for widget in app.meridional_canvas.winfo_children():
        widget.destroy()

    # Create new plot with larger figure size and higher DPI
    fig, ax = plt.subplots(figsize=(16, 10), dpi=100)
    ax.set_aspect('equal')
    fig.tight_layout()
    
    # Plot the initial streamlines
    n_arrows = 20
    stride = max(1, int(gv.cpoints / n_arrows))

    for L in range(gv.ns):
        ax.plot(gv.Rmat[:, L], gv.Zmat[:, L], color='black', linewidth=1)

        for P in range(stride, len(gv.Rmat) - 1, stride):
            arrow = FancyArrowPatch(
                (gv.Rmat[P, L], gv.Zmat[P, L]),
                (gv.Rmat[P + 1, L], gv.Zmat[P + 1, L]),
                arrowstyle='->',
                linewidth=1,
                color='black',
                mutation_scale=8
            )
            ax.add_patch(arrow)


    # Plot inlet and outlet lines
    x_coords = [gv.Rmat[0, 0], gv.Rmat[0, gv.ns - 1]]
    y_coords = [gv.Zmat[0, 0], gv.Zmat[0, gv.ns - 1]]
    ax.plot(x_coords, y_coords, color='k', linewidth=1, label='Inlet Line')
    ax.plot(outletLine[:, 0], outletLine[:, 1], color='k', linewidth=1, label='Outlet Line')
    ax.set_axis_off()
    

    # Create canvas and store reference in the tab3_content instance
    canvas = FigureCanvasTkAgg(fig, master=app.meridional_canvas)
    canvas.draw()
    
    
    # Store references in tab3_content instance
    if tab3_instance:
        tab3_instance.canvas = canvas
        tab3_instance.fig = fig
        tab3_instance.ax = ax

    # Add toolbar
    toolbar = NavigationToolbar2Tk(canvas, app.meridional_canvas)
    toolbar.update()
    toolbar.pack(side="bottom", fill="x")
    canvas.get_tk_widget().pack(fill='both', expand=True)


##### Bezier curve function definition
def BezierCurve(p, m):
    t = np.linspace(0, 1, m)  # Parameter values from 0 to 1
    n = len(p) - 1  # Degree of the Bezier curve (n = number of control points - 1)

    Bx = np.zeros(m)  # X-coordinates of the Bezier curve
    By = np.zeros(m)  # Y-coordinates of the Bezier curve

    # Loop over the control points and calculate the Bezier curve using Bergv.nstein polynomials
    for i in range(n + 1): #i= 0 to 4
        # Binomial coefficient and Bergv.nstein basis functiogv.ns
        binomial_coeff = comb(n, i) #binomial coefficient determines weight of each control points
        Bx += binomial_coeff * (1 - t)**(n - i) * t**i * p[i, 0]  # X-coordinate = [0,0], [1,0], [2,0] ..... [0,0] maa s0 ko x co-ordinate >>>>first iterationmai yesmaa Bx maa 100 wta points haru store vako hunchha bewcause of ligv.nspace t
        By += binomial_coeff * (1 - t)**(n - i) * t**i * p[i, 1]  # Y-coordinate = [0,1], [1,1], [2,1], .... [0,1] maa s0 ko y coordinate

    # Return the points as an array of shape (m, 2)
    return np.column_stack((Bx, By))


##### Distribute function definition
#####redistributes points along a given bcp such that they are evenly spaced in terms of arc length. this helps in redistributing points based on actual curve length, rather than just interpolating based on index
def Distribute(bcp, m):
    # Step 1: Calculate cumulative arc length (s) along the curve
    #print(bcp)
    s = np.zeros(len(bcp))
    #print (s)
    for i in range(1, len(bcp)):
        s[i] = s[i - 1] + np.sqrt((bcp[i, 0] - bcp[i - 1, 0]) ** 2 + (bcp[i, 1] - bcp[i - 1, 1]) ** 2)
        #print(f's[{i}] = {s[i]}')

    # Step 2: Offset to shift points into the second quadrant
    minusX = np.max(bcp[:, 0]) * 1.1
    #print(minusX)
    minusY = np.max(bcp[:, 1]) * 1.1
    #print(minusY)
    xy = np.zeros_like(bcp)
    xy[:, 0] = bcp[:, 0] - minusX
    xy[:, 1] = bcp[:, 1] - minusY
    #print(xy)
    #plt.plot(xy[:,0], xy[:,1], 'o', markersize=6, color='black', label="Distributed Points")

    # Step 3: Calculate radius and angle for polar coordinates
    r = np.sqrt(xy[:, 0] ** 2 + xy[:, 1] ** 2)
    theta = np.arctan2(xy[:, 1], -xy[:, 0])

    # Step 4: Interpolate to distribute points evenly along the curve
    S = np.linspace(0, s[-1], m)
    theta_interp = PchipInterpolator(s, theta)(S)
    r_interp = PchipInterpolator(s, r)(S)

    # Step 5: Convert back to Cartesian coordinates and apply offset
    xy_out = np.zeros((m, 2))
    xy_out[:, 0] = -r_interp * np.cos(theta_interp) + minusX
    xy_out[:, 1] = r_interp * np.sin(theta_interp) + minusY

    return xy_out
