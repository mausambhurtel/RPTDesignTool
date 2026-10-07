import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

class tab6_content(tk.Frame):
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
        self.columnconfigure(1, weight=9)
        
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
        
        # Button for 3D Blade Plot
        blade_button = ttk.Button(frame4centeringwidgets, text="View 3D Blade", command=self.plot_3d_blade)
        blade_button.grid(row=0, column=0, padx=10, pady=30, sticky="nsew")
        
        # Button for 3D Runner Plot
        runner_button = ttk.Button(frame4centeringwidgets, text="View 3D Runner", command=self.plot_3d_runner)
        runner_button.grid(row=2, column=0, padx=10, pady=0, sticky="nsew")
        
        # 3D plot frame
        self.threed_plot_frame = ttk.LabelFrame(self, text="3D Visualization")
        self.threed_plot_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        
        # Prevent the plot frame from resizing based on its contents
        self.threed_plot_frame.pack_propagate(False)
        self.threed_plot_frame.grid_propagate(False)

    def plot_3d_blade(self):
        self.clear_previous_plot()
        
        # Create figure to fill the frame
        threed_blade_figure = plt.figure(figsize=(12, 10))
        threed_blade_figure.subplots_adjust(left=-0.5, right=1.4, top=1, bottom=-0.5)
        ax = self.setup_3d_axes(threed_blade_figure)

        # Convert polar to Cartesian coordinates
        self.gv.Xmat = self.gv.Rmat * np.cos(self.gv.Theta)
        self.gv.Ymat = self.gv.Rmat * np.sin(self.gv.Theta)

        # Plot the surface with styling
        ax.plot_surface(self.gv.Xmat, self.gv.Ymat, self.gv.Zmat, color='steelblue', alpha=0.7, edgecolor='darkblue')

        # Adjust the view angle
        ax.view_init(elev=90, azim=-90)

        # Set equal scaling and adjust limits
        self.set_equal_aspect(ax, self.gv.Xmat, self.gv.Ymat, self.gv.Zmat, padding_factor=0.63)
        
        # Zoom in by reducing the camera distance (smaller = more zoomed in)
        ax.dist = 6  # Default is ~10, lower values zoom in

        # Embed the plot to the frame
        self.current_plot = FigureCanvasTkAgg(threed_blade_figure, master=self.threed_plot_frame)
        self.current_plot.draw()

        # Add navigation toolbar
        self.current_toolbar = NavigationToolbar2Tk(self.current_plot, self.threed_plot_frame)
        self.current_toolbar.update()
        self.current_toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.current_plot.get_tk_widget().pack(fill="both", expand=True)
        if hasattr(self.app, "mark_design_step_complete"):
            self.app.mark_design_step_complete(5)

    def plot_3d_runner(self, external_ax=None):
        if external_ax is None:
            self.clear_previous_plot()
            # Create a figure with a specific size
            threed_runner_figure = plt.figure(figsize=(12, 10))
            threed_runner_figure.subplots_adjust(left=-0.5, right=1.5, top=1.3, bottom=-0.5)
            ax = self.setup_3d_axes(threed_runner_figure)
            ax.dist = 6 
            embed_plot = True
        else:
            # Use the provided external axis
            ax = external_ax
            embed_plot = False

        #__________________________________________________________________________________
        ## Creating Hub and Shroud Surfaces - defining the angular range for 360° rotation
        theta_vals = np.linspace(0, 2 * np.pi, 100)  # 100 points around the circle

        # Create a meshgrid for rotation
        Theta, _ = np.meshgrid(theta_vals, self.gv.Zmat[:, 0])  # Shroud line
        _, Z_hub = np.meshgrid(theta_vals, self.gv.Zmat[:, -1])  # Hub line
        _, Z_shroud = np.meshgrid(theta_vals, self.gv.Zmat[:, 0])  # Shroud line

        # Expand R values for the surfaces
        R_hub = np.tile(self.gv.Rmat[:, -1], (100, 1)).T  # Hub radius profile
        R_shroud = np.tile(self.gv.Rmat[:, 0], (100, 1)).T  # Shroud radius profile

        # Convert to Cartesian coordinates
        X_hub = R_hub * np.cos(Theta)
        Y_hub = R_hub * np.sin(Theta)
        X_shroud = R_shroud * np.cos(Theta)
        Y_shroud = R_shroud * np.sin(Theta)

        # Plot the hub and shroud surfaces
        ax.plot_surface(X_hub, Y_hub, Z_hub, color='steelblue', alpha=0.4)  # Hub Surface
        ax.plot_surface(X_shroud, Y_shroud, Z_shroud, color='steelblue', alpha=0.4)  # Shroud Surface
        #__________________________________________________________________________________

        ## Copying and Plotting Multiple Blades - converting polar to cartesian coordinates at first
        self.gv.Xmat = self.gv.Rmat * np.cos(self.gv.Theta)
        self.gv.Ymat = self.gv.Rmat * np.sin(self.gv.Theta)

        # Initialize arrays for storing x, y, and z values
        Line, Point = self.gv.Zmat.shape
        xvalues = np.zeros((Line, Point))
        yvalues = np.zeros((Line, Point))
        zvalues = np.zeros((Line, Point))

        # Loop for plotting multiple blade positions
        for i, angle in enumerate(np.linspace(0, 2 * np.pi, self.gv.z["rv"], endpoint=False)):
            theta, r, z = self.cartesian_to_polar(self.gv.Xmat, self.gv.Ymat, self.gv.Zmat)
            theta += angle
            x, y, z = self.polar_to_cartesian(theta, r, z)

            # Reshape to ensure proper dimensions
            x = x.reshape(Line, Point)
            y = y.reshape(Line, Point)
            z = z.reshape(Line, Point)

            # Store values (for the last iteration)
            xvalues = x
            yvalues = y
            zvalues = z

            # Plot the surface with custom color and transparency
            ax.plot_surface(xvalues, yvalues, zvalues, color='steelblue', alpha=0.7, edgecolor='darkblue')
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
            # Set equal scaling and adjust limits for standalone plot
            # Get some sample coordinates for aspect setting
            self.gv.Xmat = self.gv.Rmat * np.cos(self.gv.Theta)
            self.gv.Ymat = self.gv.Rmat * np.sin(self.gv.Theta)
            self.set_equal_aspect(ax, self.gv.Xmat, self.gv.Ymat, self.gv.Zmat, padding_factor=1.0)
            
            # Embed the plot to the frame
            self.current_plot = FigureCanvasTkAgg(threed_runner_figure, master=self.threed_plot_frame)
            self.current_plot.draw()
            
            # Add navigation toolbar
            self.current_toolbar = NavigationToolbar2Tk(self.current_plot, self.threed_plot_frame)
            self.current_toolbar.update()
            self.current_toolbar.pack(side=tk.BOTTOM, fill=tk.X)
            self.current_plot.get_tk_widget().pack(fill="both", expand=True)
            if hasattr(self.app, "mark_design_step_complete"):
                self.app.mark_design_step_complete(5)
  
    # Clear all children widgets from the plot frame
    def clear_previous_plot(self):
        for widget in self.threed_plot_frame.winfo_children():
            widget.destroy()
        self.current_plot = None
        self.current_toolbar = None

    def setup_3d_axes(self, fig):
        ax = fig.add_subplot(111, projection='3d', proj_type='ortho')
        ax.set_box_aspect([1, 1, 1])  # Equal aspect ratio for all dimensions
        ax.grid(False)
        # Axis labels
        #ax.set_xlabel("X-axis")
        #ax.set_ylabel("Y-axis")
        #ax.set_zlabel("Z-axis")
        ax.set_axis_off()  # Hide axis lines and labels
        return ax

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
