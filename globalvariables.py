# globalvariables.py
import numpy as np

class GlobalVariables:
    def __init__(self):
        # Constants
        self.g = 9.81
        self.rho = 1000
        self.eta_p = 0.90
        self.eta_t = 0.95
        #self.grav = 9.81  # Acceleration due to gravity (m/s²)
        #self.etah = 0.9  # Turbine efficiency
        #self.rho = 1000  # Water density (kg/m³)

        self.cpoints = 800


        ## variables >> tab 2
        self.gd = {}
        self.z = {}
        self.heads = {}
        self.speeds = {}
        self.flows = {}
        self.pump_in = {}
        self.pump_out = {}
        self.turbine_in = {}
        self.turbine_out = {}
        self.pm_other = {}
        self.tm_other = {}
        self.omega_tm = 0
        self.omega_pm = 0

        ## variables >> tab 3
        self.ns = 0
        self.Rmat = 0
        self.Zmat = 0
        self.C_mMat = 0
        
        self.HubXmat = 0
        self.HubYmat = 0
        self.HubZmat = 0
        self.ShroudXmat = 0
        self.ShroudYmat = 0
        self.ShroudZmat = 0
        
        
        ## variables >> tab 4
        self.Theta = 0
        self.Gmat = 0
        self.Hmat = 0
        self.blade_span = 0
        self.Umat = 0
        self.Cumat = 0
        self.Wmat = 0
        self.UCumat = 0
        self.beta = 0
        self.UCuRelativemat = 0
        self.bad_distribution_points = None
        self.bad_distribution_control_points = None
        self.bad_distribution_method = ""

        
        self.UCuRelativematPM = 0
        self.UmatPM = 0
        self.CumatPM = 0
        self.WmatPM = 0
        self.UCumatPM = 0
        self.CmmatPM = 0
        self.C_mMatPM = 0


        ## variables >> tab 5


        ## variables >> tab 6
        self.Xmat = 0
        self.Ymat = 0
        self.Zmat = 0

         ## variables >> tab 7
        self.bladeX = 0
        self.bladeY = 0
        self.bladeZ = 0
        self.le_shape = "Elliptical"
        self.te_shape = "Elliptical"
        self.e = 0  # Blade thickness at leading edge (m)
        self.e_min = 0  # Blade thickness at trailing edge (m)

        ## variables >> tab 8 (GV design)
        self.gv_ax = {}
        self.gv_out = {}
        self.gv_in = {}
        self.gd_gv = {}

        ## export tracking
        self.last_export_dir = ""








