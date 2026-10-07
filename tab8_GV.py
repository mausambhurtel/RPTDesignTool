import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import pandas as pd
from scipy import interpolate
import os
import math as m
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.tri as mtri


class tab8_content(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.gv = app.gv
        self.current_plot = None  # To keep track of current plot for clearing
        self.current_toolbar = None  # To keep track of current toolbar
        self.create_frame()

    def create_frame(self):
        # Configure grid weights for responsiveness
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=7)
        
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
        frame4centeringwidgets.grid(row=1, column=0, sticky="")

        # GV Number Label and Entry
        self.label = ttk.Label(frame4centeringwidgets, text="No. of GVs:")
        self.label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        # Initially disabled entry
        self.z_gv_entry = ttk.Entry(frame4centeringwidgets, state="disabled")
        self.z_gv_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # GV No Label and Entry
        self.label = ttk.Label(frame4centeringwidgets, text="GV Angle:")
        self.label.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.label = ttk.Label(frame4centeringwidgets, text="*At first, it shows for BEP")
        self.label.grid(row=3, column=0, columnspan = 2, sticky="ew")
        self.label = ttk.Label(frame4centeringwidgets, text="*Adjust it for different loading conditions")
        self.label.grid(row=4, column=0, columnspan = 2, sticky="ew")

        # Initially disabled spinbox
        self.gv_angle_spinbox = ttk.Spinbox(frame4centeringwidgets, from_=0, to=50, width=10, state="disabled")
        self.gv_angle_spinbox.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Button for 3D guide vane plot only
        GV_button = ttk.Button(frame4centeringwidgets, text="View GV Arrangement",  command=self.plot_gv_only)
        GV_button.grid(row=5, column=0, columnspan=2, padx=10, pady=30, sticky="nsew")

        # Button for combined plot
        combined_button = ttk.Button(frame4centeringwidgets, text="View GV with Runner", command=self.plot_combined_gv_runner)
        combined_button.grid(row=6, column=0, columnspan=2, padx=10, pady=0, sticky="nsew")


        # 3D plot frame (right side - 80%)
        self.threed_plot_frame = ttk.LabelFrame(self, text="3D Visualization")
        self.threed_plot_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

        # Prevent the plot frame from resizing based on its contents
        self.threed_plot_frame.pack_propagate(False)
        self.threed_plot_frame.grid_propagate(False)


    def calculate_GV_cascade(self):
        #__________________________________________________________________________________________________________________
        # Enable controls first so we can access the entry
        self.z_gv_entry.config(state="normal")
        
        # Process and validate GV number entry
        try:
            gv_text = self.z_gv_entry.get().strip()

            # Set default GV number based on runner vane count
            self.gv.z["gv_default"] = 24 if self.gv.z["rv"] % 2 != 0 else 23

            # If entry is empty, use default; otherwise use user input
            if not gv_text:
                self.gv.z["gv"] = self.gv.z["gv_default"]
                self.z_gv_entry.insert(0, str(self.gv.z["gv"]))
            else:
                self.gv.z["gv"] = int(gv_text)

                # Validate: GV count must not be integer multiple of runner vanes
                if self.gv.z["gv"] % self.gv.z["rv"] == 0:
                    raise ValueError("The ratio of guide vanes number to runner vanes number should not be an integer!")

        except ValueError as e:
            messagebox.showerror("Input Error!", str(e))
            # Disable controls again if calculation failed
            self.z_gv_entry.config(state="disabled")
            self.gv_angle_spinbox.config(state="disabled")
            return None
        #__________________________________________________________________________________________________________________

        # Check if this is the first calculation (BEP condition)
        # We'll use a flag or check if these values don't exist yet
        is_first_calculation = not hasattr(self.gv.gv_in, 'D1') or 'D1' not in self.gv.gv_in

        # 1 Guide vane outlet dimensions
        self.gv.gv_out["D2"] = 1.05 * self.gv.gd["D1"]
        self.gv.gd_gv["B0"] = self.gv.gd["B0"] + 0.001
        self.gv.gv_out["cu"] = self.gv.turbine_in["cu1"] *  (self.gv.gd["D1"] / self.gv.gv_out["D2"])
        self.gv.gv_out["cm"] = self.gv.flows["Qt"] / (m.pi * self.gv.gv_out["D2"] * self.gv.gd_gv["B0"])
        calculated_angle_bep = m.degrees(m.atan(self.gv.gv_out["cm"] / self.gv.gv_out["cu"]))

        #Print calculated GV outlet angle for BEP
        print("\n")
        print(f"Calculated GV Outlet Angle Parameters at BEP:")
        print(f"cu: {self.gv.gv_out["cu"]} m/s, cm: {self.gv.gv_out["cm"]} m/s, alpha2 (BEP): {calculated_angle_bep} deg")
        c_urin = self.gv.gv_out["cu"]
        c_mrin = self.gv.gv_out["cm"]
        c_rin = m.sqrt(c_urin ** 2 + c_mrin ** 2)
        print(f"C_theta:\t{c_urin / c_rin}")
        print(f"C_r:\t{c_mrin / c_rin}")
        print(f"C_z:\t{0}")
        
        # Only calculate the fixed dimensions if this is the first time (BEP condition)
        if is_first_calculation:
            # 2 Iterative calculation for axis location (ONLY for BEP condition)
            multiplication_factor = 1.001   # initial assumption
            gv_axis_location = 0.58      # initial value

            # self.gv.gv_ax["D"] should be adjusted until the guide vane shaft is located close to the center of the chord line
            while gv_axis_location < 0.6 or gv_axis_location > 0.7: 
                self.gv.gv_ax["D0"] = multiplication_factor * self.gv.gv_out["D2"]
                multiplication_factor += 0.01

                # Using sine law
                angleB = m.degrees(m.asin((self.gv.gv_out["D2"] / self.gv.gv_ax["D0"]) * m.sin(m.radians(calculated_angle_bep + 90))))
                angleC = 180 - (angleB + calculated_angle_bep + 90)
                self.gv.gd_gv["l2"] = m.sin(m.radians(angleC)) * self.gv.gv_ax["D0"] / (2 * m.sin(m.radians(calculated_angle_bep + 90)))

                # Length of guide vane with 10% coverage factor
                self.gv.gd_gv["l"] = 1.1 * m.pi * self.gv.gv_ax["D0"] /  self.gv.z["gv"]

                # Axis location
                gv_axis_location = self.gv.gd_gv["l2"] / self.gv.gd_gv["l"]

            self.gv.gd_gv["alpha0"] = 90 - angleB

            # 3 Guide vane inlet dimensions - using cosine law (ONLY for BEP condition)
            self.gv.gv_in["D1"] = 2 * np.sqrt(self.gv.gd_gv["l"]**2 + (self.gv.gv_out["D2"]/2)**2 - (2 * self.gv.gd_gv["l"] * (self.gv.gv_out["D2"]/2) * np.cos(np.radians(calculated_angle_bep + 90))))
            self.gv.gv_in["alpha1"] = 90 - np.degrees(np.arccos((self.gv.gd_gv["l"]**2 + (self.gv.gv_in["D1"]/2)**2 - (self.gv.gv_out["D2"]/2)**2) / (self.gv.gd_gv["l"] * self.gv.gv_in["D1"])))
            
            self.gv.gv_in["cm"] = self.gv.flows["Qt"] / (np.pi * self.gv.gv_in["D1"] * self.gv.gd_gv["B0"] )
            self.gv.gv_out["cu"] = self.gv.gv_in["cm"] / np.tan(np.radians(self.gv.gv_in["alpha1"]))
            
            # Store BEP angle for reference
            self.gv.gv_out["alpha2_bep"] = calculated_angle_bep

        #__________________________________________________________________________________________________________________
        # Handling GV angle in spinbox
        calculated_angle = calculated_angle_bep if is_first_calculation else self.gv.gv_out["alpha2_bep"]
        
        # Set spinbox range based on calculated angle
        min_angle = max(0, calculated_angle - 15)
        max_angle = min(50, calculated_angle + 15)
        
        # Enable and configure spinbox
        self.gv_angle_spinbox.config(from_=min_angle, to=max_angle, state="normal")
        
        # Only set calculated value if spinbox is empty (first time) or user hasn't made changes
        current_spinbox_value = self.gv_angle_spinbox.get().strip()
        if not current_spinbox_value:
            self.gv_angle_spinbox.delete(0, 'end')
            self.gv_angle_spinbox.insert(0, f"{calculated_angle:.2f}")
            effective_angle = calculated_angle
        else:
            # Use user's adjusted value for different loading conditions
            try:
                effective_angle = float(current_spinbox_value)
            except (ValueError, TypeError):
                # If user entered invalid value, fallback to calculated
                effective_angle = calculated_angle
                self.gv_angle_spinbox.delete(0, 'end')
                self.gv_angle_spinbox.insert(0, f"{calculated_angle:.2f}")

        self.gv.gv_out["alpha2"] = effective_angle  # Update alpha2 to effective angle
        #__________________________________________________________________________________________________________________

        # Generate NACA 0012 profile (replacing Excel read)
        Gv_x_profile, Gv_y_profile = self.get_naca_0012_profile(chord_length=self.gv.gd_gv["l"], num_points=200)
        
        # Adjust profile position
        Gvx = Gv_x_profile - (self.gv.gd_gv["l"] - self.gv.gd_gv["l2"])
        Gvy = Gv_y_profile
        
        # Convert to polar coordinates and rotate
        theta_profile = np.arctan2(Gvy, Gvx)
        r_profile = np.sqrt(Gvx**2 + Gvy**2)
        
        theta_profile = theta_profile + (np.pi/2 - np.radians(self.gv.gd_gv["alpha0"])) - np.pi
        
        # Convert back to cartesian
        Gvx = r_profile * np.cos(theta_profile) + self.gv.gv_ax["D0"]/2
        Gvy = r_profile * np.sin(theta_profile)
        
        # Generate coordinates for all guide vanes
        gv_coordinates = []
        angles = np.linspace(0, 2*np.pi, self.gv.z["gv"], endpoint=False)
        
        for angle in angles:
            # Convert profile to polar coordinates relative to center
            theta_gv = np.arctan2(Gvy, Gvx)
            r_gv = np.sqrt(Gvx**2 + Gvy**2)
            
            # Rotate by the current angle
            theta_rotated = theta_gv + angle
            
            # Convert back to cartesian
            x_rotated = r_gv * np.cos(theta_rotated)
            y_rotated = r_gv * np.sin(theta_rotated)
            
            gv_coordinates.append((x_rotated, y_rotated))
        
        # Return all necessary variables for 3D plotting
        return {
            'gv_coordinates': gv_coordinates,
            'self.gv.z["gv"]': self.gv.z["gv"],
            'self.gv.gv_ax["D0"]': self.gv.gv_ax["D0"],
            'self.gv.gv_out["D2"]': self.gv.gv_out["D2"],
            'self.gv.gv_in["D1"]': self.gv.gv_in["D1"],
            'self.gv.gd_gv["B0"]': self.gv.gd_gv["B0"],
            'self.gv.gd_gv["l"]': self.gv.gd_gv["l"],
            'self.gv.gv_out["alpha2"]': self.gv.gv_out["alpha2"],
            'self.gv.gv_out["alpha2_bep"]': self.gv.gv_out["alpha2_bep"]
        }

    def get_naca_0012_profile(self, chord_length, num_points):
        # Generate x coordinates (0 to 1)
        x = np.linspace(0, 1, num_points)
        
        # NACA 0012 thickness distribution
        t = 0.12  # 12% thickness
        yt = 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1015 * x**4)
        
        # Upper and lower surfaces
        x_upper = x
        y_upper = yt
        x_lower = x
        y_lower = -yt
        
        # Combine upper and lower surfaces (starting from trailing edge, going around)
        x_airfoil = np.concatenate([np.flip(x_upper), x_lower[1:]])
        y_airfoil = np.concatenate([np.flip(y_upper), y_lower[1:]])
        
        # Scale by chord length
        x_airfoil *= chord_length
        y_airfoil *= chord_length
        
        return x_airfoil, y_airfoil

  
    def plot_guide_vanes(self, ax, gv_data):
        if gv_data is None:
            return
            
        # Extract data
        gv_coordinates = gv_data['gv_coordinates']
        Z_gv = gv_data['self.gv.z["gv"]']
        B_gvout = gv_data['self.gv.gd_gv["B0"]']
        current_angle = gv_data['self.gv.gv_out["alpha2"]']  # Current effective angle
        
        # Apply z-offset to align guide vanes with runner inlet
        z_offset = self.gv.gd["B_hub"] + (0.001/2)
        z_bottom = z_offset
        z_top = B_gvout + z_offset
        
        # Recalculate guide vane profile orientation based on current angle
        # Generate NACA 0012 profile
        Gv_x_profile, Gv_y_profile = self.get_naca_0012_profile(chord_length=self.gv.gd_gv["l"], num_points=200)
        
        # Adjust profile position (same as in calculate_GV_cascade)
        Gvx = Gv_x_profile - (self.gv.gd_gv["l"] - self.gv.gd_gv["l2"])
        Gvy = Gv_y_profile
        
        # Convert to polar coordinates and rotate based on CURRENT angle
        theta_profile = np.arctan2(Gvy, Gvx)
        r_profile = np.sqrt(Gvx**2 + Gvy**2)
        
        # Calculate the rotation angle based on current effective angle
        # We need to recalculate the geometric relationship for the current angle
        angleB_current = m.degrees(m.asin((self.gv.gv_out["D2"] / self.gv.gv_ax["D0"]) * m.sin(m.radians(current_angle + 90))))
        alpha0_current = 90 - angleB_current
        
        theta_profile = theta_profile + (np.pi/2 - np.radians(alpha0_current)) - np.pi
        
        # Convert back to cartesian
        Gvx = r_profile * np.cos(theta_profile) + self.gv.gv_ax["D0"]/2
        Gvy = r_profile * np.sin(theta_profile)
        
        # Generate coordinates for all guide vanes with updated orientation
        gv_coordinates_updated = []
        angles = np.linspace(0, 2*np.pi, Z_gv, endpoint=False)
        
        for angle in angles:
            # Convert profile to polar coordinates relative to center
            theta_gv = np.arctan2(Gvy, Gvx)
            r_gv = np.sqrt(Gvx**2 + Gvy**2)
            
            # Rotate by the current angle
            theta_rotated = theta_gv + angle
            
            # Convert back to cartesian
            x_rotated = r_gv * np.cos(theta_rotated)
            y_rotated = r_gv * np.sin(theta_rotated)
            
            gv_coordinates_updated.append((x_rotated, y_rotated))
        
        # Plot each guide vane as a surface using updated coordinates
        for i, (x_profile, y_profile) in enumerate(gv_coordinates_updated):
            # Create meshgrid for the surface
            # Duplicate the profile for top and bottom
            X_surface = np.array([x_profile, x_profile])
            Y_surface = np.array([y_profile, y_profile])
            Z_surface = np.array([[z_bottom] * len(x_profile), [z_top] * len(x_profile)])
            
            # Plot the guide vane surface
            ax.plot_surface(X_surface, Y_surface, Z_surface, color='steelblue', alpha=0.7, edgecolor='darkblue')
            
            # Optional: Plot profile edges for better definition
            ax.plot(x_profile, y_profile, z_bottom, 'b', linewidth=1, alpha=0.9)
            ax.plot(x_profile, y_profile, z_top, 'b', linewidth=1, alpha=0.9)
        
        #__________________________________________________________________________________________________________________
        # Add circular boundaries
        theta_circle = np.linspace(0, 2*np.pi, 400)
        
        # Inner circle
        D_gvin = gv_data['self.gv.gv_in["D1"]']
        x_inner = (D_gvin/2) * np.cos(theta_circle)
        y_inner = (D_gvin/2) * np.sin(theta_circle)
        ax.plot(x_inner, y_inner, z_bottom, 'k', linewidth=1, alpha=0.7)
        ax.plot(x_inner, y_inner, z_top, 'k', linewidth=1, alpha=0.7)
        
        # Outer circle
        D_gvout = gv_data['self.gv.gv_out["D2"]']
        x_outer = (D_gvout/2) * np.cos(theta_circle)
        y_outer = (D_gvout/2) * np.sin(theta_circle)
        ax.plot(x_outer, y_outer, z_bottom, 'k', linewidth=1, alpha=0.7)
        ax.plot(x_outer, y_outer, z_top, 'k', linewidth=1, alpha=0.7)

        # Create meshgrid for circular surfaces
        r_range = np.linspace(D_gvin/2, D_gvout/2, 30)
        theta_range = np.linspace(0, 2*np.pi, 60)
        R, THETA = np.meshgrid(r_range, theta_range)
        X_surf = R * np.cos(THETA)
        Y_surf = R * np.sin(THETA)

        # Top surface
        Z_top = np.full_like(X_surf, z_top)
        ax.plot_surface(X_surf, Y_surf, Z_top, color='seagreen', alpha=0.3)

        # Bottom surface
        Z_bottom = np.full_like(X_surf, z_bottom)
        ax.plot_surface(X_surf, Y_surf, Z_bottom, color='seagreen', alpha=0.3)
        #__________________________________________________________________________________________________________________

        print("Guide Vane Dimensions:")
        print(f"D1: {D_gvin:.4f} m, D2: {D_gvout:.4f} m, D0: {self.gv.gv_ax['D0']:.4f} m, Alpha2: {current_angle:.2f} deg, Alpha0: {alpha0_current:.2f} deg")
        return z_bottom, z_top
        

    def plot_gv_only(self):
        self.clear_previous_plot()
        
        # Create figure
        fig = plt.figure(figsize=(12, 10))
        fig.subplots_adjust(left=-0.5, right=1.5, top=1.25, bottom=-0.3)
        ax = self.setup_3d_axes(fig, show_axes=False)
        ax.dist = 6
        
        # Get and plot guide vane data
        gv_data = self.calculate_GV_cascade()
        if gv_data:
            z_bottom, z_top = self.plot_guide_vanes(ax, gv_data)
            
            # Set title and limits
            #ax.set_title(f'3D Guide Vane Cascade (Z_gv = {gv_data["self.gv.z["gv"]"]})')
            
            # Set appropriate limits for GV only
            self.set_gv_aspect(ax, gv_data, z_bottom, z_top)

            # Set view angle for better visualization
            ax.view_init(elev=90, azim=45)
            
            #ax.legend()
            
            # Add to GUI
            self.embed_plot(fig)
            if hasattr(self.app, "mark_design_step_complete"):
                self.app.mark_design_step_complete(7)

    def plot_combined_gv_runner(self, external_ax=None):
        if external_ax is None:
            # Create standalone plot
            self.clear_previous_plot()
            
            # Create figure
            fig = plt.figure(figsize=(12, 10))
            fig.subplots_adjust(left=-0.5, right=1.5, top=1.25, bottom=-0.3)
            ax = self.setup_3d_axes(fig, show_axes=False)
            ax.dist = 6 
            embed_plot = True
            
        else:
            # Use external axis without clearing it
            ax = external_ax
            embed_plot = False
        
        # Get and plot guide vane data
        gv_data = self.calculate_GV_cascade()
        z_bottom, z_top = None, None

        if gv_data:
            z_bottom, z_top = self.plot_guide_vanes(ax, gv_data)
        
        # Plot runner using tab7 function
        try:
            self.app.tab7.plot_runner_thickness(external_ax=ax)
        except AttributeError:
            if embed_plot:  # Only show warning for standalone plots
                messagebox.showwarning("ERROR!! Plot the runner with thickness at first!")
        except Exception as e:
            if embed_plot:  # Only show error for standalone plots
                messagebox.showerror("Runner Plot Error", f"Error plotting runner: {str(e)}")
        
        # Only view standalone plots
        if embed_plot:
            #ax.view_init(elev=90, azim=45)
            
            # Set appropriate limits for combined view
            if gv_data and hasattr(self.gv, 'bladeX'):
                self.set_combined_aspect(ax, gv_data, z_bottom, z_top)
            
            # Add to GUI
            self.embed_plot(fig)
            if gv_data and hasattr(self.app, "mark_design_step_complete"):
                self.app.mark_design_step_complete(7)

    # Clear all children widgets from the plot frame
    def clear_previous_plot(self):
        for widget in self.threed_plot_frame.winfo_children():
            widget.destroy()
        self.current_plot = None
        self.current_toolbar = None

    def setup_3d_axes(self, fig, show_axes):
        ax = fig.add_subplot(111, projection='3d', proj_type='ortho')
        ax.set_box_aspect([1, 1, 1])  # Set equal aspect ratio for all dimensions
        
        if show_axes:
            ax.grid(True)
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.set_zlabel('Z (m)')
        else:
            ax.grid(False)
            ax.set_axis_off()
        
        return ax

    def embed_plot(self, fig):
        canvas = FigureCanvasTkAgg(fig, master=self.threed_plot_frame)
        canvas.draw()
        
        # Add toolbar
        toolbar = NavigationToolbar2Tk(canvas, self.threed_plot_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.current_plot = canvas
        self.current_toolbar = toolbar

    def set_gv_aspect(self, ax, gv_data, z_bottom, z_top):
        B_gvout = gv_data['self.gv.gd_gv["B0"]']
        D_gvout = gv_data['self.gv.gv_out["D2"]']
        
        max_range = max(D_gvout/2, B_gvout) * 1.35   # 90% of the larger dimension for padding -- increase 0.9 to (1.2 - 1.5) to get smaller plot
        
        ax.set_xlim([-max_range, max_range])
        ax.set_ylim([-max_range, max_range])
        ax.set_zlim([z_bottom - 0.05, z_top + 0.05])
        ax.set_box_aspect([1, 1, (z_top - z_bottom + 0.1) / (2 * max_range)])

    def set_combined_aspect(self, ax, gv_data, z_bottom, z_top):
        # Get guide vane dimensions
        D_gvout = gv_data['self.gv.gv_out["D2"]']
        
        # Get runner dimensions
        r_max = np.max(self.gv.Rmat) if hasattr(self.gv, 'Rmat') else 0
        z_min = np.min(self.gv.Zmat) if hasattr(self.gv, 'Zmat') else 0
        z_max = np.max(self.gv.Zmat) if hasattr(self.gv, 'Zmat') else 0
        
        # Use the larger of GV or runner radial dimensions
        max_radius = max(D_gvout/2, r_max) * 1.35   # 90% of the larger dimension for padding -- increase 0.9 to (1.2 - 1.5) to get smaller plot
        
        # Determine z-limits considering both GV and runner
        z_min_plot = min(z_min - 0.05, z_bottom - 0.05) if z_bottom is not None else z_min - 0.05
        z_max_plot = max(z_max + 0.05, z_top + 0.05) if z_top is not None else z_max + 0.05
        
        ax.set_xlim([-max_radius, max_radius])
        ax.set_ylim([-max_radius, max_radius])
        ax.set_zlim([z_min_plot, z_max_plot])
        
        # Calculate aspect ratio based on the actual dimensions
        z_range = z_max_plot - z_min_plot
        xy_range = 2 * max_radius
        z_aspect = z_range / xy_range if xy_range > 0 else 1
        
        ax.set_box_aspect([1, 1, z_aspect])
    


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
