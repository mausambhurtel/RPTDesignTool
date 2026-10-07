import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import Cursor
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


class tab7_content(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.gv = app.gv
        self.le_ellipse_anchor_offset = 2
        self.te_ellipse_anchor_offset = 2
        self.frame()

    def frame(self):
        # Configure grid weights for responsiveness
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=7)
        
        # Control frame (left side - 20%)
        control_frame = ttk.Frame(self)
        control_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # Configure control frame for centering
        control_frame.columnconfigure(0, weight=1)
        control_frame.rowconfigure(0, weight=1)
        control_frame.rowconfigure(1, weight=1)
        control_frame.rowconfigure(2, weight=1)
        
        # Create a centered container within control frame
        frame4centeringwidgets = ttk.Frame(control_frame)
        frame4centeringwidgets.grid(row=1, column=0, sticky="")
        
        # Section 1: Shape Selection
        ttk.Label(frame4centeringwidgets, text="Shape Selection:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, columnspan=2, padx=10, pady=(5, 2), sticky="w"
        )

        self.label = ttk.Label(frame4centeringwidgets, text="LE Shape")
        self.label.grid(row=1, column=0, padx=10, pady=5, sticky="e")

        self.le_shape_var = tk.StringVar(value="Elliptical")
        self.le_shape_combo = ttk.Combobox(
            frame4centeringwidgets,
            textvariable=self.le_shape_var,
            values=["Elliptical", "Francis Type"],
            state="readonly",
            width=18
        )
        self.le_shape_combo.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        self.label = ttk.Label(frame4centeringwidgets, text="TE Shape")
        self.label.grid(row=2, column=0, padx=10, pady=5, sticky="e")

        self.te_shape_var = tk.StringVar(value="Elliptical")
        self.te_shape_combo = ttk.Combobox(
            frame4centeringwidgets,
            textvariable=self.te_shape_var,
            values=["Elliptical", "Francis Type"],
            state="readonly",
            width=18
        )
        self.te_shape_combo.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Store defaults in global variables
        self.gv.le_shape = self.le_shape_var.get()
        self.gv.te_shape = self.te_shape_var.get()

        # Update global variables on selection change
        self.le_shape_combo.bind("<<ComboboxSelected>>", self._on_edge_shape_change)
        self.te_shape_combo.bind("<<ComboboxSelected>>", self._on_edge_shape_change)

        # Section 2: Thickness Selection
        ttk.Label(frame4centeringwidgets, text="Thickness Selection:", font=("Arial", 10, "bold")).grid(
            row=3, column=0, columnspan=2, padx=10, pady=(10, 2), sticky="w"
        )

        self.thickness_mode_var = tk.StringVar(value="manual")

        self.apply_recommend_rb = ttk.Radiobutton(
            frame4centeringwidgets,
            text="Apply Recommend Thickness",
            variable=self.thickness_mode_var,
            value="recommend",
            command=self._on_thickness_mode_change
        )
        self.apply_recommend_rb.grid(row=4, column=0, columnspan=2, padx=10, pady=2, sticky="w")

        self.apply_manual_rb = ttk.Radiobutton(
            frame4centeringwidgets,
            text="Apply Manual Thickness",
            variable=self.thickness_mode_var,
            value="manual",
            command=self._on_thickness_mode_change
        )
        self.apply_manual_rb.grid(row=10, column=0, columnspan=2, padx=10, pady=(8, 2), sticky="w")

        # Section 2a: Recommend Thickness
        self.label_thickness_title = ttk.Label(
            frame4centeringwidgets,
            text="Calculated Thickness (mm):",
            font=("Arial", 9, "normal")
        )
        self.label_thickness_title.grid(row=5, column=0, padx=10, pady=5, sticky="e")

        self.label_thickness_value = ttk.Label(
            frame4centeringwidgets,
            text="",
            font=("Arial", 9, "normal")
        )
        self.label_thickness_value.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        self.label_min_thickness_title = ttk.Label(
            frame4centeringwidgets,
            text="Minimum Thickness (mm):",
            font=("Arial", 9, "normal")
        )
        self.label_min_thickness_title.grid(row=6, column=0, padx=10, pady=5, sticky="e")

        self.label_min_thickness_value = ttk.Label(
            frame4centeringwidgets,
            text="",
            font=("Arial", 9, "normal")
        )
        self.label_min_thickness_value.grid(row=6, column=1, padx=10, pady=5, sticky="w")

        self.calc_button = ttk.Button(
            frame4centeringwidgets,
            text="Get Recommend Thickness",
            command=self.calculate_e_values
        )
        self.calc_button.grid(row=7, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        self.recommend_choice_var = tk.StringVar(value="")

        self.use_calc_radio = ttk.Radiobutton(
            frame4centeringwidgets,
            text="Use calculated thickness on both LE and TE",
            variable=self.recommend_choice_var,
            value="calc",
            command=self._on_recommend_choice
        )
        self.use_calc_radio.grid(row=8, column=0, columnspan=2, padx=10, pady=2, sticky="w")

        self.use_min_radio = ttk.Radiobutton(
            frame4centeringwidgets,
            text="Use minimum calculated thickness on both LE and TE",
            variable=self.recommend_choice_var,
            value="min",
            command=self._on_recommend_choice
        )
        self.use_min_radio.grid(row=9, column=0, columnspan=2, padx=10, pady=2, sticky="w")

        # Section 2b: Manual Thickness
        self.label = ttk.Label(frame4centeringwidgets, text="Thickness at LE (mm):")
        self.label.grid(row=11, column=0, padx=10, pady=(5, 5), sticky="e")

        self.le_thickness_entry = ttk.Entry(frame4centeringwidgets)
        self.le_thickness_entry.grid(row=11, column=1, padx=10, pady=(5, 1), sticky="ew")
        self.le_thickness_entry.insert(0, "15")

        self.label = ttk.Label(frame4centeringwidgets, text="Thickness at TE (mm):")
        self.label.grid(row=12, column=0, padx=10, pady=5, sticky="e")

        self.te_thickness_entry = ttk.Entry(frame4centeringwidgets)
        self.te_thickness_entry.grid(row=12, column=1, padx=10, pady=1, sticky="ew")
        self.te_thickness_entry.insert(0, "15")

        # Section 3: Apply / View
        self.apply_thickness_button = ttk.Button(
            frame4centeringwidgets,
            text="Apply Thickness on Blade",
            command=self._apply_thickness_on_blade
        )
        self.apply_thickness_button.grid(row=13, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="nsew")

        self.view_runner_button = ttk.Button(
            frame4centeringwidgets,
            text="View Runner with Thickness",
            command=self.plot_runner_thickness
        )
        self.view_runner_button.grid(row=14, column=0, columnspan=2, padx=10, pady=0, sticky="nsew")

        # Initial state control
        self._shape_selected = False
        self._recommend_ready = False
        self._calc_thickness_mm = None
        self._min_thickness_mm = None
        self._set_shapes_enabled(True)
        self._set_mode_enabled(True)
        self._set_recommend_enabled(False)
        self._set_manual_enabled(True)
        self._set_apply_enabled(True)
        self._set_view_runner_enabled(False)

        # 3D plot frame (right side - 80%)
        self.thickness_threeD_frame = ttk.LabelFrame(self, text="3D Visualization")
        self.thickness_threeD_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

        # Prevent the plot frame from resizing based on its contents
        self.thickness_threeD_frame.pack_propagate(False)
        self.thickness_threeD_frame.grid_propagate(False)

    def plot_single_blade_thickness(self, external_ax=None):
        
        if not self.calculate_blade_thickness_coordinates():
            return False
        
        if external_ax is None:
            # Clear previous plot
            for widget in self.thickness_threeD_frame.winfo_children():
                widget.destroy()
            
            # Create figure for 3D plot
            fig = plt.figure(figsize=(12, 10))
            fig.subplots_adjust(left=-0.5, right=1.3, top=1, bottom=-0.5)
            ax = fig.add_subplot(111, projection='3d', proj_type='ortho')
            ax.dist = 6 
            embed_plot = True
            
        else:
            # Use external axis and clear it
            ax = external_ax
            ax.clear()
            embed_plot = False

        # Plot the single blade with thickness
        self._plot_thickness_surface(ax, self.gv.bladeX, self.gv.bladeY, self.gv.bladeZ)
        ax.set_axis_off()

        # Set equal aspect ratio
        self.set_equal_aspect(ax, self.gv.bladeX, self.gv.bladeY, self.gv.bladeZ, padding_factor=0.65)

        # Set view
        ax.view_init(elev=90, azim=-90)

        if embed_plot:
            # Embed plot in tkinter frame
            canvas = FigureCanvasTkAgg(fig, master=self.thickness_threeD_frame)
            canvas.draw()

            # Add toolbar for interactive navigation
            toolbar = NavigationToolbar2Tk(canvas, self.thickness_threeD_frame)
            toolbar.update()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def plot_runner_thickness(self, external_ax=None):

        # Calculate blade thickness coordinates if not already calculated
        if not hasattr(self.gv, 'bladeX') or self.gv.bladeX is None:
            if not self.calculate_blade_thickness_coordinates():
                return False
        
        if external_ax is None:
            # Clear previous plot
            for widget in self.thickness_threeD_frame.winfo_children():
                widget.destroy()
            
            # Create figure for 3D plot
            fig = plt.figure(figsize=(12, 10))
            fig.subplots_adjust(left=-0.5, right=1.5, top=1.25, bottom=-0.3)
            ax = fig.add_subplot(111, projection='3d', proj_type='ortho')
            ax.dist = 6 
            embed_plot = True
        else:
            # Use external axis and clear it
            ax = external_ax
            embed_plot = False

        #__________________________________________________________________________________
        # Plot hub and shroud surfaces - define angular range for 360° rotation
        theta_vals = np.linspace(0, 2 * np.pi, 100)

        # Create meshgrid for rotation
        Theta, _ = np.meshgrid(theta_vals, self.gv.Zmat[:, 0])
        _, Z_hub = np.meshgrid(theta_vals, self.gv.Zmat[:, -1])
        _, Z_shroud = np.meshgrid(theta_vals, self.gv.Zmat[:, 0])

        # Expand R values for the surfaces
        R_hub = np.tile(self.gv.Rmat[:, -1], (100, 1)).T
        R_shroud = np.tile(self.gv.Rmat[:, 0], (100, 1)).T

        # Convert to Cartesian coordinates
        X_hub = R_hub * np.cos(Theta)
        Y_hub = R_hub * np.sin(Theta)
        X_shroud = R_shroud * np.cos(Theta)
        Y_shroud = R_shroud * np.sin(Theta)

        # Plot surfaces
        ax.plot_surface(X_hub, Y_hub, Z_hub, color='steelblue', alpha=0.4)
        ax.plot_surface(X_shroud, Y_shroud, Z_shroud, color='steelblue', alpha=0.4)
        #__________________________________________________________________________________
        
        # Plot multiple blades with thickness
        Line, Point = self.gv.bladeZ.shape

        # Loop for plotting multiple blade positions with thickness
        for angle in np.linspace(0, 2 * np.pi, self.gv.z["rv"], endpoint=False):
            # Convert thickness blade coordinates to polar
            theta, r, z = self.cartesian_to_polar(self.gv.bladeX, self.gv.bladeY, self.gv.bladeZ)
            
            # Rotate by the current angle
            theta += angle
            
            # Convert back to cartesian
            x, y, z = self.polar_to_cartesian(theta, r, z)

            # Reshape to ensure proper dimensions
            x = x.reshape(Line, Point)
            y = y.reshape(Line, Point)
            z = z.reshape(Line, Point)

            # Plot the surface with thickness
            self._plot_thickness_surface(ax, x, y, z)
        
        ax.set_axis_off()

        # Set view
        #ax.view_init(elev=90, azim=45)
        #__________________________________________________________________________________
        
        # Creating Circular Boundaries
        # calculating bottom and top z-limits for circular boundaries
        z_offset = self.gv.gd["B_hub"]
        z_bottom = z_offset
        z_top = self.gv.gd["B0"] + z_offset

        theta_circle = np.linspace(0, 2*np.pi, 400)

        # D1 circles
        x_D1 = (self.gv.gd["D1"]/2) * np.cos(theta_circle)
        y_D1 = (self.gv.gd["D1"]/2) * np.sin(theta_circle)
        ax.plot(x_D1, y_D1, z_bottom, 'k', linewidth=1, alpha=0.7)
        ax.plot(x_D1, y_D1, z_top, 'k', linewidth=1, alpha=0.7)

        # D2 circle
        x_D2 = (self.gv.gd["D2"]/2) * np.cos(theta_circle)
        y_D2 = (self.gv.gd["D2"]/2) * np.sin(theta_circle)
        ax.plot(x_D2, y_D2, self.gv.Zmat[-1, 0], 'k', linewidth=1, alpha=0.7)

        # D_hub circle
        x_D3 = (self.gv.gd["D_hub"]/2) * np.cos(theta_circle)
        y_D3 = (self.gv.gd["D_hub"]/2) * np.sin(theta_circle)
        ax.plot(x_D3, y_D3, self.gv.Zmat[-1, -1], 'k', linewidth=1, alpha=0.7)
        #__________________________________________________________________________________

        if embed_plot:
            # Set equal aspect ratio using blade coordinates
            self.set_equal_aspect(ax, self.gv.bladeX, self.gv.bladeY, self.gv.bladeZ, padding_factor=1)

            # Embed plot in tkinter frame
            canvas = FigureCanvasTkAgg(fig, master=self.thickness_threeD_frame)
            canvas.draw()

            # Add toolbar for interactive navigation
            toolbar = NavigationToolbar2Tk(canvas, self.thickness_threeD_frame)
            toolbar.update()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


    @staticmethod
    def _plot_thickness_surface(ax, x, y, z):
        # Keep every surface cell so short edge caps remain visible. Sample only
        # the decorative grid, otherwise dense meshes obscure the filled surface.
        ax.plot_surface(x, y, z, color="steelblue", alpha=0.7,
                        edgecolor="none", rstride=1, cstride=1)
        ax.plot_wireframe(x, y, z, color="darkblue", linewidth=0.5,
                         rstride=max(1, int(np.ceil((x.shape[0] - 1) / 50))), cstride=1)

    def calculate_blade_thickness_coordinates(self):
        try:
            # --- Get edge shape selections ---
            le_shape = self.le_shape_var.get().strip() if hasattr(self, "le_shape_var") else "Elliptical"
            te_shape = self.te_shape_var.get().strip() if hasattr(self, "te_shape_var") else "Elliptical"

            if le_shape not in ("Elliptical", "Francis Type"):
                le_shape = "Elliptical"
            if te_shape not in ("Elliptical", "Francis Type"):
                te_shape = "Elliptical"

            self.gv.le_shape = le_shape
            self.gv.te_shape = te_shape

            # --- Get entry values and handle defaults ---
            le_text = self.le_thickness_entry.get().strip()
            te_text = self.te_thickness_entry.get().strip()

            le_value = float(le_text) if le_text else 15.0  # default in mm
            te_value = float(te_text) if te_text else 15.0

            if not le_text:
                self.le_thickness_entry.insert(0, str(le_value))
            if not te_text:
                self.te_thickness_entry.insert(0, str(te_value))

            # --- Validation ---
            max_length = np.max(self.gv.Gmat[-1, :]) * 1000  # blade length in mm
            print(f"Max blade length: {max_length/1000} m")

            if (le_value <= 0 or le_value >= max_length or te_value <= 0 or te_value >= max_length):
                raise ValueError("Thickness must be > 0 and < blade length!")

            # --- Convert to meters ---
            t_le = le_value / 1000
            t_te = te_value / 1000

            # --- Get blade geometry from global variables ---
            X, Y, Z = self.gv.Xmat, self.gv.Ymat, self.gv.Zmat
            np_, ns = self.gv.Rmat.shape

            # --- Call the actual thickness calculation & plotting ---
            Xny, Yny, Zny, T = self.profile_thickness_calculation(t_le, t_te, X, Y, Z, np_, ns)
            Xle, Yle, Zle = (self.leading_edge_elliptical(t_le, Xny, Yny, Zny, ns, n_points=40)
                             if le_shape == "Elliptical"
                             else self.leading_edge(t_le, Xny, Yny, Zny, ns))
            Xte, Yte, Zte = (self.trailing_edge_elliptical(t_te, Xny, Yny, Zny, ns, n_points=40)
                             if te_shape == "Elliptical"
                             else self.trailing_edge(t_te, Xny, Yny, Zny, ns))

            # Use the physical edge joins on each side, not fixed adjacent rows.
            # At a fine mesh, a Francis bevel spans many rows of the original body.
            sides = np.stack((Xny, Yny, Zny), axis=-1)
            pressure, suction = sides[:, :, 0], sides[:, :, 1]
            pressure_distance = self._surface_distances(pressure)
            suction_distance = self._surface_distances(suction)
            n_rows = pressure.shape[0]

            if le_shape == "Francis Type":
                pressure_start = t_le / 2
                suction_start = 3 * t_le / 2
            else:
                offset = self._safe_int(getattr(self, "le_ellipse_anchor_offset", 1))
                index = min(max(offset, 0), n_rows - 2)
                pressure_start = pressure_distance[index]
                suction_start = suction_distance[index]

            if te_shape == "Francis Type":
                pressure_end = 0.0
                suction_end = (2 * t_te / 3) / np.tan(np.radians(30))
            else:
                offset = self._safe_int(getattr(self, "te_ellipse_anchor_offset", 1))
                index = max(min(n_rows - 1 - offset, n_rows - 1), 1)
                pressure_end = pressure_distance[-1] - pressure_distance[index]
                suction_end = suction_distance[-1] - suction_distance[index]

            pressure = self._trim_surface_side(pressure, pressure_start, pressure_end)
            suction = self._trim_surface_side(suction, suction_start, suction_end)
            leading = np.stack(self._get_le_curve(le_shape, Xle, Yle, Zle), axis=-1)
            trailing = np.stack((Xte, Yte, Zte), axis=-1)
            leading = self._fit_edge_endpoints(leading, suction[0], pressure[0])
            trailing = self._fit_edge_endpoints(trailing, pressure[-1], suction[-1])

            # One continuous contour for all four LE/TE combinations. Each seam
            # appears once; the final row closes the contour back to its start.
            blade = np.concatenate((
                trailing,
                suction[-2:0:-1],
                leading,
                pressure[1:-1],
                trailing[:1],
            ), axis=0)
            self.gv.bladeX, self.gv.bladeY, self.gv.bladeZ = (
                blade[:, :, coordinate] for coordinate in range(3)
            )
            # A previously previewed STL must follow the rebuilt thickness surface.
            export_tab = getattr(self.app, "tabx", None)
            if export_tab is not None:
                export_tab.blade_mesh = None

        except ValueError as e:
            messagebox.showerror("Input Error!", str(e))
            return False
        if hasattr(self.app, "mark_design_step_complete"):
            self.app.mark_design_step_complete(6)
        return True


    def _on_edge_shape_change(self, event=None):
        if hasattr(self, "le_shape_var"):
            self.gv.le_shape = self.le_shape_var.get().strip()
        if hasattr(self, "te_shape_var"):
            self.gv.te_shape = self.te_shape_var.get().strip()
        if not self._shape_selected:
            self._shape_selected = True
            self._set_mode_enabled(True)
            self._on_thickness_mode_change()


    def calculate_e_values(self):
        """
        Calculate blade thickness at leading and trailing edges using the formula:
        e = 0.02 * (u_0 / u_Ref)^0.2 * d_2
        e_min = 0.015 * d_2
        Blade Thickness = e (in mm)
        Minimum Thickness = e_min (in mm)
        where:
        - u_0 is the tangential velocity at runner inlet (m/s)
        - u_Ref is the reference velocity (100 m/s)
        - d_2 is the runner outlet diameter (m)
        """
        try:
            # Get d_2 (runner outlet diameter) from global variables
            if not hasattr(self.gv, 'gd') or 'D2' not in self.gv.gd:
                messagebox.showerror("Error", "Runner geometry not defined. Please complete Tab 2 (Machine Design) first.")
                return
            
            d_2 = self.gv.gd["D2"]  # in meters
            
            # Get u_0 (tangential velocity at runner inlet) from global variables
            if not hasattr(self.gv, 'turbine_in') or 'u1' not in self.gv.turbine_in:
                messagebox.showerror("Error", "Turbine inlet velocity not defined. Please complete Tab 2 (Machine Design) first.")
                return
            
            u_0 = self.gv.turbine_in["u1"]  # self.gv.pump_out["u1"]
            u_Ref = 100.0  # Reference velocity in m/s
            
            # Calculate e (blade thickness at leading edge in meters)
            velocity_ratio = u_0 / u_Ref
            e = 0.02 * (velocity_ratio ** 0.2) * d_2
            
            # Calculate e_min (blade thickness at trailing edge in meters)
            e_min = 0.015 * d_2
            
            # Store values in global variables
            self.gv.e = e
            self.gv.e_min = e_min
            
            # Calculate blade thickness (e) and minimum thickness (e_min) in mm
            thickness_mm = e * 1000
            min_thickness_mm = e_min * 1000

            self._calc_thickness_mm = thickness_mm
            self._min_thickness_mm = min_thickness_mm
            self._recommend_ready = True
            
            # Update the display labels
            self.label_thickness_value.config(text=f"{thickness_mm:.2f}")
            self.label_min_thickness_value.config(text=f"{min_thickness_mm:.2f}")

            # Enable recommend checkboxes after calculation (if recommend mode active)
            if self.thickness_mode_var.get() == "recommend":
                self._set_recommend_enabled(True)
                self._on_recommend_choice()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate blade thickness:\n{str(e)}")


    def _on_thickness_mode_change(self):
        mode = self.thickness_mode_var.get()

        if mode == "recommend":
            self._set_recommend_enabled(True)
            self._set_manual_enabled(False)
            self._set_apply_enabled(False)
        elif mode == "manual":
            self._set_recommend_enabled(False)
            self._set_manual_enabled(True)
            self._set_apply_enabled(True)
        else:
            self._set_recommend_enabled(False)
            self._set_manual_enabled(False)
            self._set_apply_enabled(False)

        # Reset runner view availability until apply is clicked
        self._set_view_runner_enabled(False)


    def _on_recommend_choice(self):
        if not self._recommend_ready:
            return

        choice = self.recommend_choice_var.get()
        if choice == "calc":
            self._apply_recommended_values(self._calc_thickness_mm)
            self._set_apply_enabled(True)
        elif choice == "min":
            self._apply_recommended_values(self._min_thickness_mm)
            self._set_apply_enabled(True)
        else:
            self._set_apply_enabled(False)


    def _apply_recommended_values(self, value_mm):
        if value_mm is None:
            return
        # Temporarily enable entries to update values even if manual section is disabled
        was_disabled = "disabled" in self.le_thickness_entry.state()
        if was_disabled:
            self.le_thickness_entry.state(["!disabled"])
            self.te_thickness_entry.state(["!disabled"])

        self.le_thickness_entry.delete(0, tk.END)
        self.le_thickness_entry.insert(0, f"{value_mm:.2f}")
        self.te_thickness_entry.delete(0, tk.END)
        self.te_thickness_entry.insert(0, f"{value_mm:.2f}")

        if was_disabled and self.thickness_mode_var.get() != "manual":
            self.le_thickness_entry.state(["disabled"])
            self.te_thickness_entry.state(["disabled"])


    def _apply_thickness_on_blade(self):
        if self.plot_single_blade_thickness() is not False:
            self._set_view_runner_enabled(True)


    def _set_shapes_enabled(self, enabled: bool):
        state = "readonly" if enabled else "disabled"
        self.le_shape_combo.configure(state=state)
        self.te_shape_combo.configure(state=state)


    def _set_mode_enabled(self, enabled: bool):
        state = "!disabled" if enabled else "disabled"
        self.apply_recommend_rb.state([state])
        self.apply_manual_rb.state([state])


    def _set_recommend_enabled(self, enabled: bool):
        if not enabled:
            self.calc_button.state(["disabled"])
            self.use_calc_radio.state(["disabled"])
            self.use_min_radio.state(["disabled"])
            self.recommend_choice_var.set("")
            return

        self.calc_button.state(["!disabled"])
        if self._recommend_ready:
            self.use_calc_radio.state(["!disabled"])
            self.use_min_radio.state(["!disabled"])
        else:
            self.use_calc_radio.state(["disabled"])
            self.use_min_radio.state(["disabled"])


    def _set_manual_enabled(self, enabled: bool):
        state = "!disabled" if enabled else "disabled"
        self.le_thickness_entry.state([state])
        self.te_thickness_entry.state([state])


    def _set_apply_enabled(self, enabled: bool):
        state = "!disabled" if enabled else "disabled"
        self.apply_thickness_button.state([state])


    def _set_view_runner_enabled(self, enabled: bool):
        state = "!disabled" if enabled else "disabled"
        self.view_runner_button.state([state])


    @staticmethod
    def _safe_unit_vector(vec, fallback):
        norm = np.linalg.norm(vec)
        if norm < 1e-12:
            return fallback
        return vec / norm


    @staticmethod
    def _safe_int(value, default=1):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default


    def leading_edge_elliptical(self, tmax, Xblade, Yblade, Zblade, ns, n_points=40):
        #tmax = max(tmax, 0.006)
        R = tmax / 2
        a = 3 * R  # major axis (nose length)
        b = R      # minor axis (half thickness)

        Xp = Xblade[:, :, 0]
        Xs = Xblade[:, :, 1]
        Yp = Yblade[:, :, 0]
        Ys = Yblade[:, :, 1]
        Zp = Zblade[:, :, 0]
        Zs = Zblade[:, :, 1]

        XLE = np.zeros((n_points, ns))
        YLE = np.zeros((n_points, ns))
        ZLE = np.zeros((n_points, ns))

        thetas = np.linspace(-np.pi / 2, np.pi / 2, n_points)

        n_stream = Xp.shape[0]
        le_offset = self._safe_int(getattr(self, "le_ellipse_anchor_offset", 1), default=1)
        if n_stream >= 2:
            i0 = min(max(le_offset, 0), n_stream - 2)
            i1 = i0 + 1
        else:
            i0 = 0
            i1 = 0

        for j in range(ns):
            Pp0 = np.array([Xp[i0, j], Yp[i0, j], Zp[i0, j]])
            Ps0 = np.array([Xs[i0, j], Ys[i0, j], Zs[i0, j]])
            Pp1 = np.array([Xp[i1, j], Yp[i1, j], Zp[i1, j]])
            Ps1 = np.array([Xs[i1, j], Ys[i1, j], Zs[i1, j]])

            M0 = 0.5 * (Pp0 + Ps0)
            M1 = 0.5 * (Pp1 + Ps1)

            t_hat = self._safe_unit_vector(M0 - M1, np.array([1.0, 0.0, 0.0]))  # upstream
            n_hat = self._safe_unit_vector(Pp0 - Ps0, np.array([0.0, 1.0, 0.0]))

            x_local = a * np.cos(thetas)
            y_local = b * np.sin(thetas)

            points = M0 + np.outer(x_local, t_hat) + np.outer(y_local, n_hat)
            XLE[:, j] = points[:, 0]
            YLE[:, j] = points[:, 1]
            ZLE[:, j] = points[:, 2]

        return XLE, YLE, ZLE


    def trailing_edge_elliptical(self, tout, Xblade, Yblade, Zblade, ns, n_points=40):
        #tout = max(tout, 0.006)
        R = tout / 2
        a = 3 * R  # major axis (nose length)
        b = R      # minor axis (half thickness)

        Xp = Xblade[:, :, 0]
        Xs = Xblade[:, :, 1]
        Yp = Yblade[:, :, 0]
        Ys = Yblade[:, :, 1]
        Zp = Zblade[:, :, 0]
        Zs = Zblade[:, :, 1]

        XTE = np.zeros((n_points, ns))
        YTE = np.zeros((n_points, ns))
        ZTE = np.zeros((n_points, ns))

        thetas = np.linspace(np.pi / 2, -np.pi / 2, n_points)

        n_stream = Xp.shape[0]
        te_offset = self._safe_int(getattr(self, "te_ellipse_anchor_offset", 1), default=1)
        if n_stream >= 2:
            i0_pos = max(min((n_stream - 1) - te_offset, n_stream - 1), 1)
            i1_pos = i0_pos - 1
            i0 = i0_pos
            i1 = i1_pos
        else:
            i0 = 0
            i1 = 0

        for j in range(ns):
            Pp0 = np.array([Xp[i0, j], Yp[i0, j], Zp[i0, j]])
            Ps0 = np.array([Xs[i0, j], Ys[i0, j], Zs[i0, j]])
            Pp1 = np.array([Xp[i1, j], Yp[i1, j], Zp[i1, j]])
            Ps1 = np.array([Xs[i1, j], Ys[i1, j], Zs[i1, j]])

            M0 = 0.5 * (Pp0 + Ps0)
            M1 = 0.5 * (Pp1 + Ps1)

            t_hat = self._safe_unit_vector(M0 - M1, np.array([1.0, 0.0, 0.0]))  # downstream
            n_hat = self._safe_unit_vector(Pp0 - Ps0, np.array([0.0, 1.0, 0.0]))

            x_local = a * np.cos(thetas)
            y_local = b * np.sin(thetas)

            points = M0 + np.outer(x_local, t_hat) + np.outer(y_local, n_hat)
            XTE[:, j] = points[:, 0]
            YTE[:, j] = points[:, 1]
            ZTE[:, j] = points[:, 2]

        return XTE, YTE, ZTE


    def _get_le_curve(self, le_shape, Xle, Yle, Zle):
        if le_shape == "Francis Type":
            order = [24, 38, 39, 40, 41, 42, 43, 2, 16, 17, 18, 19, 20, 21, 22, 0]
            return Xle[order, :], Yle[order, :], Zle[order, :]
        return Xle, Yle, Zle


    @staticmethod
    def _surface_distances(points):
        distances = np.linalg.norm(np.diff(points, axis=0), axis=-1)
        return np.vstack((np.zeros(points.shape[1]), np.cumsum(distances, axis=0)))

    @classmethod
    def _trim_surface_side(cls, points, start_distance, end_distance):
        """Sample the retained side between exact physical edge junctions."""
        distances = cls._surface_distances(points)
        starts = np.broadcast_to(start_distance, (points.shape[1],))
        ends = distances[-1] - np.broadcast_to(end_distance, (points.shape[1],))
        if np.any(ends <= starts) or not np.isfinite(distances).all():
            raise ValueError("The edge thickness leaves no room for the blade surface.")
        trimmed = np.empty_like(points)
        for span in range(points.shape[1]):
            positions = np.linspace(starts[span], ends[span], points.shape[0])
            for coordinate in range(3):
                trimmed[:, span, coordinate] = np.interp(
                    positions, distances[:, span], points[:, span, coordinate]
                )
        return trimmed

    @staticmethod
    def _fit_edge_endpoints(curve, start, end):
        # Thickness can vary at elliptical anchors, and curved sides differ from
        # the tangent extrapolation used by the Francis leading-edge construction.
        fraction = np.linspace(0, 1, curve.shape[0])[:, None, None]
        fitted = (curve + (1 - fraction) * (start - curve[0])
                  + fraction * (end - curve[-1]))
        fitted[0], fitted[-1] = start, end
        return fitted


    def profile_thickness_calculation(self, tmax, tmin, X, Y, Z, np_points, ns_points):
        T = np.zeros(np_points)
        T[0] = tmax
        T[np_points - 1] = tmin

        # Set thickness for first few points
        tstart = 5
        for i in range(1, tstart):
            T[i] = tmax

        # Linear distribution of thickness
        dT = (T[0] - T[np_points - 1]) / (np_points - tstart)
        for i in range(tstart, np_points - 1):
            T[i] = T[i - 1] - dT

        # Prepare empty arrays for blade coordinates
        Xblade = np.zeros((np_points, ns_points, 2))
        Yblade = np.zeros((np_points, ns_points, 2))
        Zblade = np.zeros((np_points, ns_points, 2))

        # Loop over the mesh to calculate new coordinates
        for J in range(ns_points - 1):
            for I in range(np_points - 1):
                Xa = X[I, J] - X[I + 1, J]
                Ya = Y[I, J] - Y[I + 1, J]
                Za = Z[I, J] - Z[I + 1, J]
                Xb = X[I, J] - X[I, J + 1]
                Yb = Y[I, J] - Y[I, J + 1]
                Zb = Z[I, J] - Z[I, J + 1]
                
                Xc = Ya * Zb - Yb * Za
                Yc = -(Xa * Zb - Xb * Za)
                Zc = Xa * Yb - Xb * Ya
                L = np.sqrt(Xc**2 + Yc**2 + Zc**2)
                
                A = L  # This value is not used further, but could be if needed

                # Thickness at current point
                Thickness = T[I] / (2 * L)

                Xblade[I, J, 0] = X[I, J] + (T[I] / 2) / L * Xc
                Xblade[I, J, 1] = X[I, J] - Thickness * Xc
                Yblade[I, J, 0] = Y[I, J] + Thickness * Yc
                Yblade[I, J, 1] = Y[I, J] - Thickness * Yc
                Zblade[I, J, 0] = Z[I, J] + Thickness * Zc
                Zblade[I, J, 1] = Z[I, J] - Thickness * Zc

        # Handle the last row (J = ns)
        J = ns_points - 1
        for I in range(np_points - 1):
            Xa = X[I, J] - X[I, J - 1]
            Ya = Y[I, J] - Y[I, J - 1]
            Za = Z[I, J] - Z[I, J - 1]
            Xb = X[I, J] - X[I + 1, J]
            Yb = Y[I, J] - Y[I + 1, J]
            Zb = Z[I, J] - Z[I + 1, J]
            
            Xc = Ya * Zb - Yb * Za
            Yc = -(Xa * Zb - Xb * Za)
            Zc = Xa * Yb - Xb * Ya
            L = np.sqrt(Xc**2 + Yc**2 + Zc**2)
            
            A = L  # This value is not used further

            Thickness = T[I] / (2 * L)
            
            Xblade[I, J, 0] = X[I, J] + Thickness * Xc
            Xblade[I, J, 1] = X[I, J] - Thickness * Xc
            Yblade[I, J, 0] = Y[I, J] + Thickness * Yc
            Yblade[I, J, 1] = Y[I, J] - Thickness * Yc
            Zblade[I, J, 0] = Z[I, J] + Thickness * Zc
            Zblade[I, J, 1] = Z[I, J] - Thickness * Zc

        # Handle the last column (I = np)
        I = np_points - 1
        for J in range(ns_points - 1):
            Xa = X[I, J] - X[I - 1, J]
            Ya = Y[I, J] - Y[I - 1, J]
            Za = Z[I, J] - Z[I - 1, J]
            Xb = X[I, J] - X[I, J + 1]
            Yb = Y[I, J] - Y[I, J + 1]
            Zb = Z[I, J] - Z[I, J + 1]
            
            Xc = -(Ya * Zb - Yb * Za)
            Yc = (Xa * Zb - Xb * Za)
            Zc = -(Xa * Yb - Xb * Ya)
            L = np.sqrt(Xc**2 + Yc**2 + Zc**2)
            
            A = L  # This value is not used further

            Thickness = T[I] / (2 * L)
            
            Xblade[I, J, 0] = X[I, J] + Thickness * Xc
            Xblade[I, J, 1] = X[I, J] - Thickness * Xc
            Yblade[I, J, 0] = Y[I, J] + Thickness * Yc
            Yblade[I, J, 1] = Y[I, J] - Thickness * Yc
            Zblade[I, J, 0] = Z[I, J] + Thickness * Zc
            Zblade[I, J, 1] = Z[I, J] - Thickness * Zc

        # Handle the final point (J = ns, I = np)
        J = ns_points - 1
        I = np_points - 1
        Xa = X[I, J] - X[I - 1, J]
        Ya = Y[I, J] - Y[I - 1, J]
        Za = Z[I, J] - Z[I - 1, J]
        Xb = X[I, J] - X[I, J - 1]
        Yb = Y[I, J] - Y[I, J - 1]
        Zb = Z[I, J] - Z[I, J - 1]

        Xc = Ya * Zb - Yb * Za
        Yc = -(Xa * Zb - Xb * Za)
        Zc = Xa * Yb - Xb * Ya
        L = np.sqrt(Xc**2 + Yc**2 + Zc**2)

        A = L  # This value is not used further

        Thickness = T[I] / (2 * L)

        Xblade[I, J, 0] = X[I, J] + Thickness * Xc
        Xblade[I, J, 1] = X[I, J] - Thickness * Xc
        Yblade[I, J, 0] = Y[I, J] + Thickness * Yc
        Yblade[I, J, 1] = Y[I, J] - Thickness * Yc
        Zblade[I, J, 0] = Z[I, J] + Thickness * Zc
        Zblade[I, J, 1] = Z[I, J] - Thickness * Zc

        return Xblade, Yblade, Zblade, T
        


    def leading_edge(self, tmax, Xblade, Yblade, Zblade, ns):
        #tmax = max(tmax, 0.006)
        R = tmax / 2
        
        Xp = Xblade[:, :, 0]
        Xs = Xblade[:, :, 1]
        
        Yp = Yblade[:, :, 0]
        Ys = Yblade[:, :, 1]
        
        Zp = Zblade[:, :, 0]
        Zs = Zblade[:, :, 1]
        
        XLE = np.zeros((44, ns))
        YLE = np.zeros((44, ns))
        ZLE = np.zeros((44, ns))
        
        for j in range(ns):
            # Step 1
            Xa = Xp[0, j] - Xp[1, j]
            Ya = Yp[0, j] - Yp[1, j]
            Za = Zp[0, j] - Zp[1, j]
            La = np.sqrt(Xa**2 + Ya**2 + Za**2)
            Lb = R
            XLE[0, j] = Xp[0, j] - (Lb / La) * Xa
            YLE[0, j] = Yp[0, j] - (Lb / La) * Ya
            ZLE[0, j] = Zp[0, j] - (Lb / La) * Za
            
            # Step 2
            Xc = Xs[0, j] - Xs[1, j]
            Yc = Ys[0, j] - Ys[1, j]
            Zc = Zs[0, j] - Zs[1, j]
            Lc = np.sqrt(Xc**2 + Yc**2 + Zc**2)
            Ld = R
            XLE[1, j] = Xs[0, j] - (Ld / Lc) * Xc
            YLE[1, j] = Ys[0, j] - (Ld / Lc) * Yc
            ZLE[1, j] = Zs[0, j] - (Ld / Lc) * Zc
            
            # Step 3
            Xe = Xp[0, j] - Xs[0, j]
            Ye = Yp[0, j] - Ys[0, j]
            Ze = Zp[0, j] - Zs[0, j]
            Le = np.sqrt(Xe**2 + Ye**2 + Ze**2)
            Lf = R
            XLE[2, j] = Xp[0, j] - (Lf / Le) * Xe
            YLE[2, j] = Yp[0, j] - (Lf / Le) * Ye
            ZLE[2, j] = Zp[0, j] - (Lf / Le) * Ze
            
            # Step 4
            Xg = XLE[0, j] - XLE[1, j]
            Yg = YLE[0, j] - YLE[1, j]
            Zg = ZLE[0, j] - ZLE[1, j]
            Lg = np.sqrt(Xg**2 + Yg**2 + Zg**2)
            Lh = R
            XLE[3, j] = XLE[0, j] - (Lh / Lg) * Xg
            YLE[3, j] = YLE[0, j] - (Lh / Lg) * Yg
            ZLE[3, j] = ZLE[0, j] - (Lh / Lg) * Zg
            
            # Step 5
            Xh = XLE[0, j] - XLE[3, j]
            Yh = YLE[0, j] - YLE[3, j]
            Zh = ZLE[0, j] - ZLE[3, j]

            Ll = R / 6

            XLE[4, j] = XLE[3, j] + (Ll / Lh) * Xh
            YLE[4, j] = YLE[3, j] + (Ll / Lh) * Yh
            ZLE[4, j] = ZLE[3, j] + (Ll / Lh) * Zh

            XLE[5, j] = XLE[4, j] + (Ll / Lh) * Xh
            YLE[5, j] = YLE[4, j] + (Ll / Lh) * Yh
            ZLE[5, j] = ZLE[4, j] + (Ll / Lh) * Zh

            XLE[6, j] = XLE[5, j] + (Ll / Lh) * Xh
            YLE[6, j] = YLE[5, j] + (Ll / Lh) * Yh
            ZLE[6, j] = ZLE[5, j] + (Ll / Lh) * Zh

            XLE[7, j] = XLE[6, j] + (Ll / Lh) * Xh
            YLE[7, j] = YLE[6, j] + (Ll / Lh) * Yh
            ZLE[7, j] = ZLE[6, j] + (Ll / Lh) * Zh

            XLE[8, j] = XLE[7, j] + (Ll / Lh) * Xh
            YLE[8, j] = YLE[7, j] + (Ll / Lh) * Yh
            ZLE[8, j] = ZLE[7, j] + (Ll / Lh) * Zh

            XLE[9, j] = XLE[8, j] + (Ll / (2 * Lh)) * Xh
            YLE[9, j] = YLE[8, j] + (Ll / (2 * Lh)) * Yh
            ZLE[9, j] = ZLE[8, j] + (Ll / (2 * Lh)) * Zh

            XLE[10, j] = XLE[9, j] + (Ll / (4 * Lh)) * Xh
            YLE[10, j] = YLE[9, j] + (Ll / (4 * Lh)) * Yh
            ZLE[10, j] = ZLE[9, j] + (Ll / (4 * Lh)) * Zh

            # Step 6
            Xm = Xp[0, j] - XLE[2, j]
            Ym = Yp[0, j] - YLE[2, j]
            Zm = Zp[0, j] - ZLE[2, j]

            Lm = (Xm ** 2 + Ym ** 2 + Zm ** 2) ** 0.5

            XLE[11, j] = XLE[2, j] + (Ll / Lm) * Xh
            YLE[11, j] = YLE[2, j] + (Ll / Lm) * Yh
            ZLE[11, j] = ZLE[2, j] + (Ll / Lm) * Zh

            XLE[12, j] = XLE[11, j] + (Ll / Lm) * Xh
            YLE[12, j] = YLE[11, j] + (Ll / Lm) * Yh
            ZLE[12, j] = ZLE[11, j] + (Ll / Lm) * Zh

            XLE[13, j] = XLE[12, j] + (Ll / Lm) * Xh
            YLE[13, j] = YLE[12, j] + (Ll / Lm) * Yh
            ZLE[13, j] = ZLE[12, j] + (Ll / Lm) * Zh

            XLE[14, j] = XLE[13, j] + (Ll / Lm) * Xh
            YLE[14, j] = YLE[13, j] + (Ll / Lm) * Yh
            ZLE[14, j] = ZLE[13, j] + (Ll / Lm) * Zh

            XLE[15, j] = XLE[14, j] + (Ll / Lm) * Xh
            YLE[15, j] = YLE[14, j] + (Ll / Lm) * Yh
            ZLE[15, j] = ZLE[14, j] + (Ll / Lm) * Zh

            # Step 7
            Xpv = XLE[15, j] - XLE[8, j]
            Ypv = YLE[15, j] - YLE[8, j]
            Zpv = ZLE[15, j] - ZLE[8, j]

            Lp = R
            Lq = (R ** 2 - (R / 6) ** 2) ** 0.5

            XLE[16, j] = XLE[4, j] + (Lq / Lp) * Xpv
            YLE[16, j] = YLE[4, j] + (Lq / Lp) * Ypv
            ZLE[16, j] = ZLE[4, j] + (Lq / Lp) * Zpv

            Lq = (R ** 2 - (2 / 6 * R) ** 2) ** 0.5

            XLE[17, j] = XLE[5, j] + (Lq / Lp) * Xpv
            YLE[17, j] = YLE[5, j] + (Lq / Lp) * Ypv
            ZLE[17, j] = ZLE[5, j] + (Lq / Lp) * Zpv

            Lq = (R ** 2 - (3 / 6 * R) ** 2) ** 0.5

            XLE[18, j] = XLE[6, j] + (Lq / Lp) * Xpv
            YLE[18, j] = YLE[6, j] + (Lq / Lp) * Ypv
            ZLE[18, j] = ZLE[6, j] + (Lq / Lp) * Zpv

            Lq = (R ** 2 - (4 / 6 * R) ** 2) ** 0.5

            XLE[19, j] = XLE[7, j] + (Lq / Lp) * Xpv
            YLE[19, j] = YLE[7, j] + (Lq / Lp) * Ypv
            ZLE[19, j] = ZLE[7, j] + (Lq / Lp) * Zpv

            Lq = (R ** 2 - (5 / 6 * R) ** 2) ** 0.5

            XLE[20, j] = XLE[8, j] + (Lq / Lp) * Xpv
            YLE[20, j] = YLE[8, j] + (Lq / Lp) * Ypv
            ZLE[20, j] = ZLE[8, j] + (Lq / Lp) * Zpv

            Lq = (R ** 2 - (11 / 12 * R) ** 2) ** 0.5

            XLE[21, j] = XLE[9, j] + (Lq / Lp) * Xpv
            YLE[21, j] = YLE[9, j] + (Lq / Lp) * Ypv
            ZLE[21, j] = ZLE[9, j] + (Lq / Lp) * Zpv

            Lq = (R ** 2 - (23 / 24 * R) ** 2) ** 0.5

            XLE[22, j] = XLE[10, j] + (Lq / Lp) * Xpv
            YLE[22, j] = YLE[10, j] + (Lq / Lp) * Ypv
            ZLE[22, j] = ZLE[10, j] + (Lq / Lp) * Zpv

            # Step 8 (Suction side)
            Xsa = Xp[0, j] - Xp[2, j]
            Ysa = Yp[0, j] - Yp[2, j]
            Zsa = Zp[0, j] - Zp[2, j]
            Lsa = (Xsa ** 2 + Ysa ** 2 + Zsa ** 2) ** 0.5
            Lsb = 3 * R

            XLE[23, j] = Xp[0, j] - (Lsb / Lsa) * Xsa
            YLE[23, j] = Yp[0, j] - (Lsb / Lsa) * Ysa
            ZLE[23, j] = Zp[0, j] - (Lsb / Lsa) * Zsa

            # Step 9
            Xsc = Xs[0, j] - Xs[2, j]
            Ysc = Ys[0, j] - Ys[2, j]
            Zsc = Zs[0, j] - Zs[2, j]

            Lsc = (Xsc ** 2 + Ysc ** 2 + Zsc ** 2) ** 0.5
            Lsd = 3 * R

            XLE[24, j] = Xs[0, j] - (Lsd / Lsc) * Xsc
            YLE[24, j] = Ys[0, j] - (Lsd / Lsc) * Ysc
            ZLE[24, j] = Zs[0, j] - (Lsd / Lsc) * Zsc

            # Step 10
            Xsg = XLE[23, j] - XLE[24, j]
            Ysg = YLE[23, j] - YLE[24, j]
            Zsg = ZLE[23, j] - ZLE[24, j]

            Lsg = (Xsg ** 2 + Ysg ** 2 + Zsg ** 2) ** 0.5
            Lsh = R

            XLE[25, j] = XLE[24, j] + (Lsh / Lsg) * Xsg
            YLE[25, j] = YLE[24, j] + (Lsh / Lsg) * Ysg
            ZLE[25, j] = ZLE[24, j] + (Lsh / Lsg) * Zsg


            # Step 11
            Xsh = XLE[25, j] - XLE[24, j]
            Ysh = YLE[25, j] - YLE[24, j]
            Zsh = ZLE[25, j] - ZLE[24, j]

            Lsl = R / 6

            XLE[26, j] = XLE[24, j] + (Lsl / (2 * Lsh)) * Xsh
            YLE[26, j] = YLE[24, j] + (Lsl / (2 * Lsh)) * Ysh
            ZLE[26, j] = ZLE[24, j] + (Lsl / (2 * Lsh)) * Zsh

            XLE[27, j] = XLE[26, j] + (Lsl / (2 * Lsh)) * Xsh
            YLE[27, j] = YLE[26, j] + (Lsl / (2 * Lsh)) * Ysh
            ZLE[27, j] = ZLE[26, j] + (Lsl / (2 * Lsh)) * Zsh

            XLE[28, j] = XLE[27, j] + (Lsl / Lsh) * Xsh
            YLE[28, j] = YLE[27, j] + (Lsl / Lsh) * Ysh
            ZLE[28, j] = ZLE[27, j] + (Lsl / Lsh) * Zsh

            XLE[29, j] = XLE[28, j] + (Lsl / Lsh) * Xsh
            YLE[29, j] = YLE[28, j] + (Lsl / Lsh) * Ysh
            ZLE[29, j] = ZLE[28, j] + (Lsl / Lsh) * Zsh

            XLE[30, j] = XLE[29, j] + (Lsl / Lsh) * Xsh
            YLE[30, j] = YLE[29, j] + (Lsl / Lsh) * Ysh
            ZLE[30, j] = ZLE[29, j] + (Lsl / Lsh) * Zsh

            XLE[31, j] = XLE[30, j] + (Lsl / Lsh) * Xsh
            YLE[31, j] = YLE[30, j] + (Lsl / Lsh) * Ysh
            ZLE[31, j] = ZLE[30, j] + (Lsl / Lsh) * Zsh

            # Step 12
            Xsm = XLE[2, j] - Xs[0, j]
            Ysm = YLE[2, j] - Ys[0, j]
            Zsm = ZLE[2, j] - Zs[0, j]

            Lsm = R
            Lsn = R / 6

            XLE[32, j] = Xs[0, j] + (Lsn / (2 * Lsm)) * Xsm
            YLE[32, j] = Ys[0, j] + (Lsn / (2 * Lsm)) * Ysm
            ZLE[32, j] = Zs[0, j] + (Lsn / (2 * Lsm)) * Zsm

            XLE[33, j] = XLE[32, j] + (Lsn / (2 * Lsm)) * Xsm
            YLE[33, j] = YLE[32, j] + (Lsn / (2 * Lsm)) * Ysm
            ZLE[33, j] = ZLE[32, j] + (Lsn / (2 * Lsm)) * Zsm

            XLE[34, j] = XLE[33, j] + (Lsn / Lsm) * Xsm
            YLE[34, j] = YLE[33, j] + (Lsn / Lsm) * Ysm
            ZLE[34, j] = ZLE[33, j] + (Lsn / Lsm) * Zsm

            XLE[35, j] = XLE[34, j] + (Lsn / Lsm) * Xsm
            YLE[35, j] = YLE[34, j] + (Lsn / Lsm) * Ysm
            ZLE[35, j] = ZLE[34, j] + (Lsn / Lsm) * Zsm

            XLE[36, j] = XLE[35, j] + (Lsn / Lsm) * Xsm
            YLE[36, j] = YLE[35, j] + (Lsn / Lsm) * Ysm
            ZLE[36, j] = ZLE[35, j] + (Lsn / Lsm) * Zsm

            XLE[37, j] = XLE[36, j] + (Lsn / Lsm) * Xsm
            YLE[37, j] = YLE[36, j] + (Lsn / Lsm) * Ysm
            ZLE[37, j] = ZLE[36, j] + (Lsn / Lsm) * Zsm

            # Step 13
            Xsp = XLE[32, j] - XLE[26, j]
            Ysp = YLE[32, j] - YLE[26, j]
            Zsp = ZLE[32, j] - ZLE[26, j]

            Lsp = np.sqrt(Xsp**2 + Ysp**2 + Zsp**2)
            a = R
            b = 3 * R  # Elliptic parameters
            x = R - R / 12
            Lsq = np.sqrt((1 - (x**2) / (a**2)) * b**2)

            XLE[38, j] = XLE[26, j] + (Lsq / Lsp) * Xsp
            YLE[38, j] = YLE[26, j] + (Lsq / Lsp) * Ysp
            ZLE[38, j] = ZLE[26, j] + (Lsq / Lsp) * Zsp

            x = R - R / 6
            Lsq = np.sqrt((1 - ((x**2) / (a**2))) * b**2)
            XLE[39, j] = XLE[27, j] + (Lsq / Lsp) * Xsp
            YLE[39, j] = YLE[27, j] + (Lsq / Lsp) * Ysp
            ZLE[39, j] = ZLE[27, j] + (Lsq / Lsp) * Zsp

            x = R - 2 * R / 6
            Lsq = np.sqrt((1 - ((x**2) / (a**2))) * b**2)
            XLE[40, j] = XLE[28, j] + (Lsq / Lsp) * Xsp
            YLE[40, j] = YLE[28, j] + (Lsq / Lsp) * Ysp
            ZLE[40, j] = ZLE[28, j] + (Lsq / Lsp) * Zsp

            x = R - 3 * R / 6
            Lsq = np.sqrt((1 - ((x**2) / (a**2))) * b**2)
            XLE[41, j] = XLE[29, j] + (Lsq / Lsp) * Xsp
            YLE[41, j] = YLE[29, j] + (Lsq / Lsp) * Ysp
            ZLE[41, j] = ZLE[29, j] + (Lsq / Lsp) * Zsp

            x = R - 4 * R / 6
            Lsq = np.sqrt((1 - ((x**2) / (a**2))) * b**2)
            XLE[42, j] = XLE[30, j] + (Lsq / Lsp) * Xsp
            YLE[42, j] = YLE[30, j] + (Lsq / Lsp) * Ysp
            ZLE[42, j] = ZLE[30, j] + (Lsq / Lsp) * Zsp

            x = R - 5 * R / 6
            Lsq = np.sqrt((1 - ((x**2) / (a**2))) * b**2)
            XLE[43, j] = XLE[31, j] + (Lsq / Lsp) * Xsp
            YLE[43, j] = YLE[31, j] + (Lsq / Lsp) * Ysp
            ZLE[43, j] = ZLE[31, j] + (Lsq / Lsp) * Zsp
                
        return XLE, YLE, ZLE

    def trailing_edge(self, tout, Xblade, Yblade, Zblade, ns):
        """Francis edge: residual face followed by a nominal 30-degree bevel.

        The returned rows run from the pressure tip to the suction-side join.
        The suction join is interpolated on the actual surface at the bevel's
        physical setback, which stays valid as the mesh resolution changes.
        """
        sides = np.stack((Xblade, Yblade, Zblade), axis=-1)
        pressure, suction = sides[:, :, 0], sides[:, :, 1]
        distances = self._surface_distances(suction)
        residual_fraction = 1 / 3
        setback = tout * (1 - residual_fraction) / np.tan(np.radians(30))
        if np.any(distances[-1] <= setback):
            raise ValueError("The trailing-edge bevel is longer than the blade.")
        edge = np.empty((11, ns, 3))
        for span in range(ns):
            pressure_tip = pressure[-1, span]
            residual_tip = pressure_tip + residual_fraction * (suction[-1, span] - pressure_tip)
            join_distance = distances[-1, span] - setback
            suction_join = np.array([
                np.interp(join_distance, distances[:, span], suction[:, span, coordinate])
                for coordinate in range(3)
            ])
            face = np.linspace(pressure_tip, residual_tip, 4)
            bevel = np.linspace(residual_tip, suction_join, 8)
            edge[:, span] = np.vstack((face, bevel[1:]))
        return edge[:, :, 0], edge[:, :, 1], edge[:, :, 2]

    # Set the aspect ratio of the 3D plot to be equal and centered with optional padding
    def set_equal_aspect(self, ax, xvalues, yvalues, zvalues, padding_factor):
       # Get data ranges
        xlim = [np.nanmin(xvalues), np.nanmax(xvalues)]
        ylim = [np.nanmin(yvalues), np.nanmax(yvalues)]
        zlim = [np.nanmin(zvalues), np.nanmax(zvalues)]
        
        # Center x,y at origin (rotation center), z at data center
        xcenter = 0
        ycenter = 0
        zcenter = (zlim[1] + zlim[0]) / 2
        
        # Find maximum radius in x-y plane and z-range
        max_xy_radius = max(abs(xlim[0]), abs(xlim[1]), abs(ylim[0]), abs(ylim[1]))
        zrange = (zlim[1] - zlim[0]) / 2
        
        # Use the larger of xy-radius or z-range for equal scaling
        max_range = max(max_xy_radius, zrange)
        extended_range = max_range * padding_factor
        
        # Set equal limits
        ax.set_xlim([xcenter - extended_range, xcenter + extended_range])
        ax.set_ylim([ycenter - extended_range, ycenter + extended_range])
        ax.set_zlim([zcenter - extended_range, zcenter + extended_range])
        
        # Force equal aspect ratio
        ax.set_box_aspect([1, 1, 1])

    @staticmethod
    def cartesian_to_polar(x, y, z):
        r = np.sqrt(x**2 + y**2)
        theta = np.arctan2(y, x)
        return theta, r, z

    @staticmethod
    def polar_to_cartesian(theta, r, z):
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        return x, y, z
