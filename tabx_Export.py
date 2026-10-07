import tkinter as tk
from tkinter import ttk
import numpy as np
import math as m
from stl import mesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from tkinter import filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import os
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from project_io import build_project_filename, write_design_info_file, write_design_info_to_directory

# Set to True to show and enable both spanwise-coordinate exports again.
ENABLE_SPANWISE_EXPORTS = False

class tabx_content(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.gv = app.gv
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
        frame4centeringwidgets.grid(row=1, column=0, sticky="")

        # Buttons
        self.visualize_blade_button = ttk.Button(
            frame4centeringwidgets,
            text="View Single Blade STL",
            command=self.visualize_blade_stl
        )
        self.visualize_blade_button.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

        self.export_blade_button = ttk.Button(
            frame4centeringwidgets,
            text="Export Single Blade STL",
            command=self.export_stl_blade
        )
        self.export_blade_button.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        self.export_curve_button = ttk.Button(frame4centeringwidgets, text="Export Curve Files", command=self.export_curve_files)
        self.export_curve_button.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        if ENABLE_SPANWISE_EXPORTS:
            self.export_spanwise_button = ttk.Button(
                frame4centeringwidgets,
                text="Export Spanwise Coordinates (No Thickness)",
                command=self.export_spanwise_splines_no_thickness
            )
            self.export_spanwise_button.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")

            self.export_spanwise_thickness_button = ttk.Button(
                frame4centeringwidgets,
                text="Export Spanwise Coordinates (With Thickness)",
                command=self.export_spanwise_splines_with_thickness
            )
            self.export_spanwise_thickness_button.grid(row=4, column=0, padx=10, pady=0, sticky="nsew")

        self.save_project_button = ttk.Button(
            frame4centeringwidgets,
            text="Save Project",
            command=self.save_project
        )
        self.save_project_button.grid(row=5 if ENABLE_SPANWISE_EXPORTS else 3, column=0, padx=10, pady=10, sticky="nsew")
        
        # 3D plot frame (right side - 80%)
        self.stl_visualization_frame = ttk.LabelFrame(self, text="3D Visualization - STL Triangles")
        self.stl_visualization_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        
        # Prevent the plot frame from resizing based on its contents
        self.stl_visualization_frame.pack_propagate(False)
        self.stl_visualization_frame.grid_propagate(False)
        
        # Store the single-blade mesh as an instance variable
        self.blade_mesh = None

    def visualize_blade_stl(self):
        try:
            self.blade_mesh = self._build_single_blade_mesh()
            self._render_visualization(self.blade_mesh)
        except Exception as e:
            messagebox.showerror("Visualization Error!", str(e))

    def _get_blade_surface_xyz(self):
        if hasattr(self.gv, "bladeX") and self.gv.bladeX is not None:
            blade_x = np.asarray(self.gv.bladeX, dtype=float)
            blade_y = np.asarray(self.gv.bladeY, dtype=float)
            blade_z = np.asarray(self.gv.bladeZ, dtype=float)
        elif hasattr(self.gv, "Rmat") and self.gv.Rmat is not None and hasattr(self.gv, "Theta") and self.gv.Theta is not None and hasattr(self.gv, "Zmat") and self.gv.Zmat is not None:
            blade_x = np.asarray(self.gv.Rmat * np.cos(self.gv.Theta), dtype=float)
            blade_y = np.asarray(self.gv.Rmat * np.sin(self.gv.Theta), dtype=float)
            blade_z = np.asarray(self.gv.Zmat, dtype=float)
        else:
            raise ValueError("No blade geometry found. Generate runner geometry first (Tab 3/7).")

        if blade_x.ndim != 2 or blade_y.ndim != 2 or blade_z.ndim != 2:
            raise ValueError("Blade coordinates must be 2D matrices.")

        return blade_x, blade_y, blade_z

    def _build_single_blade_mesh(self):
        blade_x, blade_y, blade_z = self._get_blade_surface_xyz()
        faces = self._surface_to_faces(blade_x, blade_y, blade_z, wrap_circumference=False)

        if not faces:
            raise ValueError("Failed to build STL triangles for single blade geometry.")

        blade_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
        for i, face in enumerate(faces):
            blade_mesh.vectors[i] = np.asarray(face, dtype=float)

        return blade_mesh

    @staticmethod
    def _surface_to_faces(x_mat, y_mat, z_mat, wrap_circumference=False):
        x_mat = np.asarray(x_mat, dtype=float)
        y_mat = np.asarray(y_mat, dtype=float)
        z_mat = np.asarray(z_mat, dtype=float)

        if x_mat.shape != y_mat.shape or x_mat.shape != z_mat.shape:
            raise ValueError("Surface coordinate matrices must have identical shapes.")
        if x_mat.ndim != 2:
            raise ValueError("Surface coordinate matrices must be 2D.")

        rows, cols = x_mat.shape
        if rows < 2 or cols < 2:
            return []

        faces = []
        max_j = cols if wrap_circumference else cols - 1

        for i in range(rows - 1):
            for j in range(max_j):
                j_next = (j + 1) % cols
                if not wrap_circumference and j_next == 0:
                    continue

                v1 = (x_mat[i, j], y_mat[i, j], z_mat[i, j])
                v2 = (x_mat[i + 1, j], y_mat[i + 1, j], z_mat[i + 1, j])
                v3 = (x_mat[i, j_next], y_mat[i, j_next], z_mat[i, j_next])
                v4 = (x_mat[i + 1, j], y_mat[i + 1, j], z_mat[i + 1, j])
                v5 = (x_mat[i + 1, j_next], y_mat[i + 1, j_next], z_mat[i + 1, j_next])
                v6 = (x_mat[i, j_next], y_mat[i, j_next], z_mat[i, j_next])

                faces.append([v1, v2, v3])
                faces.append([v4, v5, v6])

        return faces

    # Render the stl triangular mesh visualization
    def _render_visualization(self, blade_mesh):
        # Clear previous plot
        for widget in self.stl_visualization_frame.winfo_children():
            widget.destroy()

        # Create figure for 3D plot
        fig = plt.figure(figsize=(12, 10))
        fig.subplots_adjust(left=-0.5, right=1.4, top=1, bottom=-0.5)
        ax = fig.add_subplot(111, projection='3d', proj_type='ortho')
        ax.dist = 6 

        # Use Poly3DCollection for faster rendering
        vectors = blade_mesh.vectors
        mesh_collection = Poly3DCollection(vectors, alpha=0.7)
        mesh_collection.set_facecolor('steelblue')
        mesh_collection.set_edgecolor('darkblue')
        mesh_collection.set_linewidth(0.1)
        ax.add_collection3d(mesh_collection)
        
        # Set equal aspect ratio
        all_points = vectors.reshape(-1, 3)
        self.set_equal_aspect(ax, all_points[:, 0], all_points[:, 1], all_points[:, 2], padding_factor=0.63)
        
        ax.set_axis_off()

        # Adjust the view angle
        ax.view_init(elev=90, azim=-90)
        
        # Embed plot in tkinter frame
        self._embed_plot(fig)
    
    # Embed matplotlib figure in tkinter frame
    def _embed_plot(self, fig):
        # Embed plot in tkinter frame
        canvas = FigureCanvasTkAgg(fig, master=self.stl_visualization_frame)
        canvas.draw()

        # Add toolbar for interactive navigation
        toolbar = NavigationToolbar2Tk(canvas, self.stl_visualization_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Set the aspect ratio of the plot to be equal
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

    # Open a file dialog to choose where to save the STL file
    def export_stl_blade(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".stl",
            filetypes=[("STL files", "*.stl"), ("All files", "*.*")],
            title="Save Single Blade STL File As"
        )

        if not file_path:
            return

        try:
            if not hasattr(self, 'blade_mesh') or self.blade_mesh is None:
                self.blade_mesh = self._build_single_blade_mesh()

            self.blade_mesh.save(file_path)
            self._write_design_info_in_dir(os.path.dirname(file_path))
            messagebox.showinfo("Export Successful!", f"Find single blade STL file in {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error!", f"Failed to save STL file: {str(e)}")

    # Open a directory dialog to choose where to save the curve files
    def export_curve_files(self):
        # Ask user for save directory
        directory_path = filedialog.askdirectory(
            title="Select Directory to Save Curve Files"
        )
        
        if not directory_path:  # User canceled the dialog
            return
        
        try:
            # Check if blade data is available
            if not hasattr(self.gv, 'bladeX') or self.gv.bladeX is None:
                messagebox.showerror("Export Error!", "No blade geometry data available!")
                return
            
            # Get blade geometry data
            bladeX = self.gv.bladeX
            bladeY = self.gv.bladeY  
            bladeZ = self.gv.bladeZ
            
            # Define file paths
            hub_file = os.path.join(directory_path, "hub.curve")
            blade_file = os.path.join(directory_path, "blade.curve")
            shroud_file = os.path.join(directory_path, "shroud.curve")
            

            #Extend meridional curves a little bit
            D_GVout = self.gv.gv_out["D2"] #(1.05 * self.gv.gd["D1"])
            gap_GV_RV = (D_GVout - self.gv.gd["D1"]) / 2


            """
            shroudX = np.array([self.gv.ShroudXmat[0] + gap_GV_RV / 2, *self.gv.ShroudXmat, self.gv.ShroudXmat[-1]])
            shroudY = np.array([0, *self.gv.ShroudYmat, 0])
            shroud_outlet_extend = 1.0
            shroudZ = np.array([self.gv.ShroudZmat[0], *self.gv.ShroudZmat, self.gv.ShroudZmat[-1] - shroud_outlet_extend])

            hubX = np.array([self.gv.HubXmat[0] + gap_GV_RV / 2, *self.gv.HubXmat, self.gv.HubXmat[-1]/2, self.gv.HubXmat[-1]/2, 0]) #(first element of HubXmat + offset, all elements except last, last) 
            hubY = np.array([0, *self.gv.HubYmat, 0, 0, 0])
            hub_outlet_extend = 0.3
            hubZ = np.array([self.gv.HubZmat[0], *self.gv.HubZmat, self.gv.HubZmat[-1]/2, self.gv.HubZmat[-1]/2, shroudZ[-1]])
           


            # Hub X coordinates
            hubX = np.concatenate([
                np.ravel([self.gv.HubXmat[0] + gap_GV_RV / 2]),
                np.ravel(self.gv.HubXmat[:-1]),
                np.ravel(np.repeat(self.gv.HubXmat[-1], 6))
            ])

            # Hub Y coordinates
            hubY = np.concatenate([
                np.ravel([0]),
                np.ravel(self.gv.HubYmat),
                np.ravel(np.zeros(6))
            ])

            # Calculate draft length
            Ldraft = (self.gv.Zmat[0] - self.gv.Zmat[-1])*4

            # Hub Z coordinates
            hubZ = np.concatenate([
                np.ravel([self.gv.HubZmat[0]]),
                np.ravel(self.gv.HubZmat),
                np.ravel([self.gv.Zmat[-1] - i * Ldraft / 2 for i in range(1, 30)])
            ])

            # Shroud X coordinates
            shroudX = np.concatenate([
                np.ravel([self.gv.ShroudXmat[0] + gap_GV_RV / 2]),
                np.ravel(self.gv.ShroudXmat),
                np.ravel(np.repeat(self.gv.ShroudXmat[-1], 6))
            ])

            # Shroud Y coordinates
            shroudY = np.concatenate([
                np.ravel([0]),
                np.ravel(self.gv.ShroudYmat),
                np.ravel(np.zeros(6))
            ])

            # Shroud Z coordinates
            shroudZ = np.concatenate([
                np.ravel([self.gv.ShroudZmat[0]]),
                np.ravel(self.gv.ShroudZmat),
                np.ravel([self.gv.Zmat[-1] - i * Ldraft / 2 for i in range(1, 50)])
            ])
        """
            # Hub X coordinates
            hubX = np.concatenate([
                np.ravel([self.gv.HubXmat[0] + gap_GV_RV / 2]),
                np.ravel(self.gv.HubXmat),
                np.ravel(np.repeat(0.1, 11))  # Last value 0.1 is assumed -- this means 0.2 m diameter of the cone tip, which is repeated 7 times to prolong the fluid domain
            ])

            # Hub Y coordinates
            hubY = np.concatenate([
                np.ravel([0]),
                np.ravel(self.gv.HubYmat),
                np.ravel(np.zeros(11))
            ])

            # Hub Z coordinates
            hubZ = np.concatenate([
                np.ravel([self.gv.HubZmat[0]]),
                np.ravel(self.gv.HubZmat),
                np.array([0.1, -0.1, -0.2, -0.3, -0.4, -0.5, -0.6, -0.7, -0.8, -0.9, -1.0]) # just repeated 11 times, constantly decreasing radially to prolong the fluid domain
            ])

            # Shroud X coordinates
            shroudX = np.concatenate([
                np.ravel([self.gv.ShroudXmat[0] + gap_GV_RV / 2]),
                np.ravel(self.gv.ShroudXmat),
                np.ravel(np.repeat(self.gv.ShroudXmat[-1], 10))
            ])

            # Shroud Y coordinates
            shroudY = np.concatenate([
                np.ravel([0]),
                np.ravel(self.gv.ShroudYmat),
                np.ravel(np.zeros(10))
            ])

            # Shroud Z coordinates
            shroudZ = np.concatenate([
                np.ravel([self.gv.ShroudZmat[0]]),
                np.ravel(self.gv.ShroudZmat),
                np.array([-0.1, -0.2, -0.3, -0.4, -0.5, -0.6, -0.7, -0.8, -0.9, -1.0])
            ])
            

            # GV angle parameters
            c_mrin = self.gv.turbine_in["cm1"] * ((D_GVout / 2) / shroudX[0]) ** 2
            c_urin = self.gv.turbine_in["cu1"] * ((D_GVout / 2) / shroudX[0])
            c_rin = m.sqrt(c_urin ** 2 + c_mrin ** 2)

            print("\n")
            print("Inlet Velocity Components (from GV Outlet):")
            print(f"C_theta\t{c_urin / c_rin}")
            print(f"C_r\t{c_mrin / c_rin}")
            print(f"C_z\t{0}")


            # Export Hub curve
            with open(hub_file, 'w') as f:
                    for i in range(len(hubX)):
                        f.write(f"{hubX[i]:.6f} {hubY[i]:.6f} {hubZ[i]:.6f}\n")

            # Export Shroud curve (first column)
            with open(shroud_file, 'w') as f:
                for i in range(len(shroudX)):
                    f.write(f"{shroudX[i]:.6f} {shroudY[i]:.6f} {shroudZ[i]:.6f}\n")

            
            # Export Blade curve - each streamline as a closed profile
            with open(blade_file, "w") as f:
                n_profiles = bladeX.shape[1]  # Number of streamline profiles
                n_points = bladeX.shape[0]    # Points per profile

                for i in reversed(range(n_profiles)):
                    f.write(f"# Profile {n_profiles - i} ({n_points + 1} points)\n")
                    # Write all profile points
                    for j in range(n_points):
                        x = bladeX[j, i]
                        y = bladeY[j, i]
                        z = bladeZ[j, i]
                        f.write(f"{x:.6f} {y:.6f} {z:.6f}\n")
                    # Close the profile by repeating the first point
                    x = bladeX[0, i]
                    y = bladeY[0, i]
                    z = bladeZ[0, i]
                    f.write(f"{x:.6f} {y:.6f} {z:.6f}\n")
            
            messagebox.showinfo("Export Successful!", 
                              f"Curve files exported successfully to:\n"
                              f"• {hub_file}\n"
                              f"• {blade_file}\n"
                              f"• {shroud_file}")
            self._write_design_info_in_dir(directory_path)
                              
        except Exception as e:
            messagebox.showerror("Export Error!", f"Failed to save curve files: {str(e)}")

    def _write_design_info_in_dir(self, directory_path):
        if not directory_path:
            return
        try:
            write_design_info_to_directory(self.app, self.gv, directory_path)
            self.gv.last_export_dir = directory_path
        except Exception as e:
            messagebox.showwarning("Save Project", f"Design info was not saved:\n{str(e)}")

    def save_project(self):
        try:
            initial_dir = self.gv.last_export_dir if self.gv.last_export_dir else None
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All files", "*.*")],
                title="Save Project Info",
                initialdir=initial_dir,
                initialfile=build_project_filename(self.gv)
            )

            if not file_path:
                return

            write_design_info_file(self.app, self.gv, file_path)
            self.gv.last_export_dir = os.path.dirname(file_path)
            messagebox.showinfo("Save Project", f"Project info saved:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Save Project", f"Failed to save project info:\n{str(e)}")

    def export_spanwise_splines_no_thickness(self):
        if not ENABLE_SPANWISE_EXPORTS:
            return

        directory_path = filedialog.askdirectory(
            title="Select Directory to Save Spanwise Coordinates"
        )

        if not directory_path:
            return

        try:
            self._write_fluid_domain_centerline_csv(
                directory_path,
                "spanwise coords"
            )
        except ValueError as e:
            messagebox.showerror("Export Error!", str(e))

    def export_spanwise_splines_with_thickness(self):
        if not ENABLE_SPANWISE_EXPORTS:
            return

        directory_path = filedialog.askdirectory(
            title="Select Directory to Save Spanwise Coordinates (With Thickness)"
        )

        if not directory_path:
            return

        try:
            x_mat, y_mat, z_mat = self._get_blade_surface_with_thickness()
            self._write_spanwise_csvs(
                directory_path,
                "spanwise coords w t",
                x_mat,
                y_mat,
                z_mat,
                spans=(0.2, 0.5, 0.8),
                include_mode_side_exports=True
            )
        except ValueError as e:
            messagebox.showerror("Export Error!", str(e))

    def _get_blade_surface_no_thickness(self):
        if not hasattr(self.gv, "Rmat") or self.gv.Rmat is None:
            raise ValueError("No meridional geometry found. Please generate the runner geometry first (Tab 3).")
        if not hasattr(self.gv, "Theta") or self.gv.Theta is None:
            raise ValueError("Blade angles are missing. Please generate the beta distribution first (Tab 4).")
        if not hasattr(self.gv, "Zmat") or self.gv.Zmat is None:
            raise ValueError("No blade surface data found. Please generate the runner geometry first (Tab 3).")

        x_mat = self.gv.Rmat * np.cos(self.gv.Theta)
        y_mat = self.gv.Rmat * np.sin(self.gv.Theta)
        z_mat = self.gv.Zmat
        return x_mat, y_mat, z_mat

    def _get_blade_surface_with_thickness(self):
        if not hasattr(self.gv, "bladeX") or self.gv.bladeX is None:
            raise ValueError("No blade thickness data found. Please apply thickness in Tab 7.")
        if not hasattr(self.gv, "bladeY") or self.gv.bladeY is None:
            raise ValueError("No blade thickness data found. Please apply thickness in Tab 7.")
        if not hasattr(self.gv, "bladeZ") or self.gv.bladeZ is None:
            raise ValueError("No blade thickness data found. Please apply thickness in Tab 7.")

        return self.gv.bladeX, self.gv.bladeY, self.gv.bladeZ

    def _write_spanwise_csvs(self, base_directory, folder_name, x_mat, y_mat, z_mat, spans, include_mode_side_exports=False):
        x_mat = np.asarray(x_mat)
        y_mat = np.asarray(y_mat)
        z_mat = np.asarray(z_mat)

        if x_mat.ndim != 2 or y_mat.ndim != 2 or z_mat.ndim != 2:
            raise ValueError("Blade coordinate arrays must be 2D matrices.")

        if x_mat.shape != y_mat.shape or x_mat.shape != z_mat.shape:
            raise ValueError("Blade coordinate matrices must have matching shapes.")

        target_dir = os.path.join(base_directory, folder_name)
        os.makedirs(target_dir, exist_ok=True)

        n_streamlines = x_mat.shape[1]
        if n_streamlines < 2:
            raise ValueError("Not enough streamlines to extract spanwise coordinates.")

        for span in spans:
            idx = self._span_to_index(span, n_streamlines)
            coords = np.column_stack((x_mat[:, idx], y_mat[:, idx], z_mat[:, idx]))
            file_path = os.path.join(target_dir, f"span_{span:.1f}.csv")
            np.savetxt(file_path, coords, delimiter=",", header="x,y,z", comments="", fmt="%.6f")

            if include_mode_side_exports:
                tm_ps, tm_ss = self._extract_pressure_suction_paths(coords, mode="TM")
                pm_ps, pm_ss = self._extract_pressure_suction_paths(coords, mode="PM")

                np.savetxt(
                    os.path.join(target_dir, f"span_{span:.1f}_TM_PS.csv"),
                    tm_ps,
                    delimiter=",",
                    header="x,y,z",
                    comments="",
                    fmt="%.6f"
                )
                np.savetxt(
                    os.path.join(target_dir, f"span_{span:.1f}_TM_SS.csv"),
                    tm_ss,
                    delimiter=",",
                    header="x,y,z",
                    comments="",
                    fmt="%.6f"
                )
                np.savetxt(
                    os.path.join(target_dir, f"span_{span:.1f}_PM_PS.csv"),
                    pm_ps,
                    delimiter=",",
                    header="x,y,z",
                    comments="",
                    fmt="%.6f"
                )
                np.savetxt(
                    os.path.join(target_dir, f"span_{span:.1f}_PM_SS.csv"),
                    pm_ss,
                    delimiter=",",
                    header="x,y,z",
                    comments="",
                    fmt="%.6f"
                )

        messagebox.showinfo(
            "Export Successful!",
            f"Spanwise spline coordinates exported to:\n{target_dir}"
        )

    def _write_fluid_domain_centerline_csv(self, base_directory, folder_name):
        target_dir = os.path.join(base_directory, folder_name)
        os.makedirs(target_dir, exist_ok=True)

        hub_coords, shroud_coords = self._get_fluid_domain_hub_shroud_curves()
        center_coords = self._average_two_curves(hub_coords, shroud_coords)

        file_path = os.path.join(target_dir, "centerline_whole_fluid_domain.csv")
        np.savetxt(file_path, center_coords, delimiter=",", header="x,y,z", comments="", fmt="%.6f")

        messagebox.showinfo(
            "Export Successful!",
            f"Whole fluid-domain centerline coordinates exported to:\n{file_path}"
        )

    def _get_fluid_domain_hub_shroud_curves(self):
        if not hasattr(self.gv, 'HubXmat') or self.gv.HubXmat is None:
            raise ValueError("Hub geometry missing. Please generate meridional geometry first (Tab 3).")
        if not hasattr(self.gv, 'ShroudXmat') or self.gv.ShroudXmat is None:
            raise ValueError("Shroud geometry missing. Please generate meridional geometry first (Tab 3).")
        if not hasattr(self.gv, 'HubYmat') or self.gv.HubYmat is None or not hasattr(self.gv, 'HubZmat') or self.gv.HubZmat is None:
            raise ValueError("Hub coordinate matrices are incomplete.")
        if not hasattr(self.gv, 'ShroudYmat') or self.gv.ShroudYmat is None or not hasattr(self.gv, 'ShroudZmat') or self.gv.ShroudZmat is None:
            raise ValueError("Shroud coordinate matrices are incomplete.")
        if not hasattr(self.gv, 'gv_out') or not isinstance(self.gv.gv_out, dict) or 'D2' not in self.gv.gv_out:
            raise ValueError("GV outlet diameter missing. Please complete preceding design tabs.")
        if not hasattr(self.gv, 'gd') or not isinstance(self.gv.gd, dict) or 'D1' not in self.gv.gd:
            raise ValueError("Runner inlet diameter missing. Please complete preceding design tabs.")

        D_GVout = self.gv.gv_out["D2"]
        gap_GV_RV = (D_GVout - self.gv.gd["D1"]) / 2

        hubX = np.concatenate([
            np.ravel([self.gv.HubXmat[0] + gap_GV_RV / 2]),
            np.ravel(self.gv.HubXmat),
            np.ravel(np.repeat(0.1, 11))
        ])
        hubY = np.concatenate([
            np.ravel([0]),
            np.ravel(self.gv.HubYmat),
            np.ravel(np.zeros(11))
        ])
        hubZ = np.concatenate([
            np.ravel([self.gv.HubZmat[0]]),
            np.ravel(self.gv.HubZmat),
            np.array([0.1, -0.1, -0.2, -0.3, -0.4, -0.5, -0.6, -0.7, -0.8, -0.9, -1.0])
        ])

        shroudX = np.concatenate([
            np.ravel([self.gv.ShroudXmat[0] + gap_GV_RV / 2]),
            np.ravel(self.gv.ShroudXmat),
            np.ravel(np.repeat(self.gv.ShroudXmat[-1], 10))
        ])
        shroudY = np.concatenate([
            np.ravel([0]),
            np.ravel(self.gv.ShroudYmat),
            np.ravel(np.zeros(10))
        ])
        shroudZ = np.concatenate([
            np.ravel([self.gv.ShroudZmat[0]]),
            np.ravel(self.gv.ShroudZmat),
            np.array([-0.1, -0.2, -0.3, -0.4, -0.5, -0.6, -0.7, -0.8, -0.9, -1.0])
        ])

        hub_coords = np.column_stack((hubX, hubY, hubZ))
        shroud_coords = np.column_stack((shroudX, shroudY, shroudZ))
        return hub_coords, shroud_coords

    @staticmethod
    def _average_two_curves(curve_a, curve_b):
        curve_a = np.asarray(curve_a, dtype=float)
        curve_b = np.asarray(curve_b, dtype=float)

        if curve_a.ndim != 2 or curve_b.ndim != 2 or curve_a.shape[1] != 3 or curve_b.shape[1] != 3:
            raise ValueError("Curves to average must be Nx3 arrays.")

        n_points = max(curve_a.shape[0], curve_b.shape[0])
        if n_points < 2:
            raise ValueError("Not enough points to build fluid-domain centerline.")

        t_target = np.linspace(0.0, 1.0, n_points)

        def resample(curve):
            if curve.shape[0] == n_points:
                return curve
            t_source = np.linspace(0.0, 1.0, curve.shape[0])
            out = np.empty((n_points, 3), dtype=float)
            for k in range(3):
                out[:, k] = np.interp(t_target, t_source, curve[:, k])
            return out

        curve_a_rs = resample(curve_a)
        curve_b_rs = resample(curve_b)
        return 0.5 * (curve_a_rs + curve_b_rs)

    @staticmethod
    def _span_to_index(span, n_streamlines):
        span_clamped = max(0.0, min(1.0, float(span)))
        return int(round(span_clamped * (n_streamlines - 1)))

    def _order_curve_le_to_te(self, coords):
        coords = np.asarray(coords, dtype=float)
        if coords.ndim != 2 or coords.shape[1] != 3 or coords.shape[0] < 2:
            return coords

        radius = np.sqrt(coords[:, 0] ** 2 + coords[:, 1] ** 2)
        d1 = float(self.gv.gd.get("D1", 0.0)) if hasattr(self.gv, "gd") and isinstance(self.gv.gd, dict) else 0.0

        if d1 > 0:
            start_err = abs(radius[0] - (d1 / 2.0))
            end_err = abs(radius[-1] - (d1 / 2.0))
            if start_err > end_err:
                return coords[::-1, :]
        else:
            if radius[0] < radius[-1]:
                return coords[::-1, :]

        return coords

    def _extract_pressure_suction_paths(self, closed_coords, mode="TM"):
        coords = np.asarray(closed_coords, dtype=float)
        if coords.ndim != 2 or coords.shape[1] != 3:
            raise ValueError("Spanwise coordinates must be Nx3 arrays.")

        if coords.shape[0] > 1 and np.allclose(coords[0], coords[-1]):
            coords = coords[:-1]

        if coords.shape[0] < 4:
            raise ValueError("Not enough points to extract pressure/suction side paths.")

        radius = np.sqrt(coords[:, 0] ** 2 + coords[:, 1] ** 2)
        d1 = float(self.gv.gd.get("D1", 0.0)) if hasattr(self.gv, "gd") and isinstance(self.gv.gd, dict) else 0.0
        d2 = float(self.gv.gd.get("D2", 0.0)) if hasattr(self.gv, "gd") and isinstance(self.gv.gd, dict) else 0.0

        d1_idx = int(np.argmax(radius))
        if d1 > 0:
            d1_idx = int(np.argmin(np.abs(radius - (d1 / 2.0))))

        d2_idx = int(np.argmin(radius))
        if d2 > 0:
            d2_idx = int(np.argmin(np.abs(radius - (d2 / 2.0))))

        if d1_idx == d2_idx:
            d2_idx = (d1_idx + (coords.shape[0] // 2)) % coords.shape[0]

        mode_upper = str(mode).strip().upper()
        if mode_upper == "PM":
            le_idx = d2_idx
            te_idx = d1_idx
        else:
            le_idx = d1_idx
            te_idx = d2_idx

        path_forward = coords[self._path_indices_forward(le_idx, te_idx, coords.shape[0])]
        path_backward = coords[self._path_indices_backward(le_idx, te_idx, coords.shape[0])]

        len_forward = self._path_length(path_forward)
        len_backward = self._path_length(path_backward)

        if mode_upper == "PM":
            pressure_side = path_forward if len_forward <= len_backward else path_backward
            suction_side = path_backward if len_forward <= len_backward else path_forward
        else:
            pressure_side = path_forward if len_forward >= len_backward else path_backward
            suction_side = path_backward if len_forward >= len_backward else path_forward

        return pressure_side, suction_side

    @staticmethod
    def _path_indices_forward(start_idx, end_idx, n_points):
        indices = [start_idx]
        i = start_idx
        while i != end_idx:
            i = (i + 1) % n_points
            indices.append(i)
        return indices

    @staticmethod
    def _path_indices_backward(start_idx, end_idx, n_points):
        indices = [start_idx]
        i = start_idx
        while i != end_idx:
            i = (i - 1) % n_points
            indices.append(i)
        return indices

    @staticmethod
    def _path_length(path_coords):
        if path_coords.shape[0] < 2:
            return 0.0
        segments = np.diff(path_coords, axis=0)
        return float(np.sum(np.linalg.norm(segments, axis=1)))
