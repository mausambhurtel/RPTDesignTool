import tkinter as tk
from tkinter import ttk
from tab1_Intro import tab1_content
from tab2_MD import tab2_content
from tab3_MView import tab3_content
from tab4_BAD import tab4_content
from tab5_ED import tab5_content
from tab6_3DView import tab6_content
from tab7_BladeThickness import tab7_content
from tab8_GV import tab8_content
#from tab9_SV import tab9_content
#from tab10_SC import tab10_content
from tabx_Export import tabx_content
from globalvariables import GlobalVariables
from PIL import Image, ImageTk

# ============= FORMATTING DISPLAYING NUMBERS GLOBALLY TO 3 DECIMAL PLACES BY MONKEY PATCHING =============
def auto_format_number(value):
    try:
        if isinstance(value, (int, float)):
            if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
                return str(int(value))
            else:
                return f"{value:.3f}"
        else:
            num = float(value)
            if num.is_integer():
                return str(int(num))
            else:
                return f"{num:.3f}"
    except (ValueError, TypeError, AttributeError):
        return str(value)

original_treeview_insert = ttk.Treeview.insert

def formatted_treeview_insert(self, parent, index, iid=None, **kw):
    if 'values' in kw:
        kw['values'] = [auto_format_number(val) for val in kw['values']]
    return original_treeview_insert(self, parent, index, iid, **kw)

ttk.Treeview.insert = formatted_treeview_insert
 
original_entry_insert = ttk.Entry.insert

def formatted_entry_insert(self, index, string):
    formatted_string = auto_format_number(string)
    return original_entry_insert(self, index, formatted_string)

ttk.Entry.insert = formatted_entry_insert
# ===============================================================================================


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RPT Design Tool")

        # Get screen width and height
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()

        # Set window size to 80% of screen resolution
        self.window_width = int(self.screen_width * 0.8)
        self.window_height = int(self.screen_height * 0.8)

        # Center the window
        self.x_pos = (self.screen_width - self.window_width) // 2
        self.y_pos = (self.screen_height - 80 - self.window_height) // 2

        self.geometry(f"{self.window_width}x{self.window_height}+{self.x_pos}+{self.y_pos}")
        self.resizable(width=True, height=True)

        # Creating a shared instance of global variables
        self.gv = GlobalVariables()

        # Configuring grid layout
        self.grid_rowconfigure(0, weight=1)  # Notebook expands
        self.grid_rowconfigure(1, weight=0)  # Navigation frame fixed
        self.grid_columnconfigure(0, weight=1)
        self._configure_tab_styles()
        

        # Creating a notebook
        self.notebook = ttk.Notebook(self, style="RPT.TNotebook")
        self.notebook.grid(row=0, column=0, sticky="nsew")
        self.design_step_indexes = frozenset(range(1, 8))
        self.completed_design_steps = set()
        self.direct_tab_navigation_enabled = False
        self.configure_tab_navigation()

        # Adding tabs
        self.tabs = []

        # Tab 1
        self.tab1 = tab1_content(self.notebook, self)
        self.tabs.append(self.tab1)
        self.notebook.add(self.tab1, text="Start")

        # Tab 2
        self.tab2 = tab2_content(self.notebook, self)
        self.tabs.append(self.tab2)
        self.notebook.add(self.tab2, text="Main Dimensions")

        # Tab 3
        self.tab3 = tab3_content(self.notebook, self)
        self.tabs.append(self.tab3)
        self.notebook.add(self.tab3, text="Meridional View")

        # Tab 4
        self.tab4 = tab4_content(self.notebook, self)
        self.tabs.append(self.tab4)
        self.notebook.add(self.tab4, text="Blade Angle Distribution & Radial View")

        # Tab 5
        self.tab5 = tab5_content(self.notebook, self)
        self.tabs.append(self.tab5)
        self.notebook.add(self.tab5, text="Energy Distribution")

        # Tab 6
        self.tab6 = tab6_content(self.notebook, self)
        self.tabs.append(self.tab6)
        self.notebook.add(self.tab6, text="3D View")

        # Tab 7
        self.tab7 = tab7_content(self.notebook, self)
        self.tabs.append(self.tab7)
        self.notebook.add(self.tab7, text="Blade Thickness")

        # Tab 8
        self.tab8 = tab8_content(self.notebook, self)
        self.tabs.append(self.tab8)
        self.notebook.add(self.tab8, text="GV Design")

        """ # Tab 9
        self.tab9 = tab9_content(self.notebook, self)
        self.tabs.append(self.tab9)
        self.notebook.add(self.tab9, text="SV Design")

        # Tab 10
        self.tab10 = tab10_content(self.notebook, self)
        self.tabs.append(self.tab10)
        self.notebook.add(self.tab10, text="SC Design") """

        # Tab X
        self.tabx = tabx_content(self.notebook, self)
        self.tabs.append(self.tabx)
        self.notebook.add(self.tabx, text="Export Design")


        # Navigation setup
        self.notebook_tab_count = len(self.tabs)  # Tracking total tabs
        self.hidden_nav_tabs = [0]  # Tabs where nav frame should be hidden
        self.create_navigation_frame()  # Create nav frame
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.on_tab_changed()

    def _configure_tab_styles(self):
        style = ttk.Style(self)
        style.map(
            "RPT.TNotebook.Tab",
            foreground=[
                ("disabled", "#8f96a3"),
                ("selected", "#111111"),
                ("!disabled", "#2f3540"),
            ],
        )

    def can_user_open_tab(self, index):
        if self.direct_tab_navigation_enabled:
            return True
        if index == 0:
            return True
        return index in self.completed_design_steps

    def can_advance_from_tab(self, index):
        if index not in self.design_step_indexes:
            return True
        return index in self.completed_design_steps

    def update_tab_accessibility(self):
        if not hasattr(self, "notebook_tab_count"):
            return
        current_tab = self.notebook.index(self.notebook.select())
        for index in range(self.notebook_tab_count):
            can_open = self.can_user_open_tab(index) or index == current_tab
            self.notebook.tab(index, state="normal" if can_open else "disabled")

    def on_tab_changed(self, event=None):
        self.update_navigation_visibility()
        self.update_tab_accessibility()

    def configure_tab_navigation(self):
        # Intercept user navigation before ttk's class bindings. Programmatic
        # selection remains available to the workflow buttons and project loading.
        navigation_events = (
            "<Button-1>", "<Key-Left>", "<Key-Right>",
            "<Control-Key-Tab>", "<Control-Shift-Key-Tab>",
            "<Control-Key-ISO_Left_Tab>", "<MouseWheel>",
            "<Shift-MouseWheel>", "<Alt-MouseWheel>",
            "<Shift-Alt-MouseWheel>", "<Button-4>", "<Button-5>",
        )
        for sequence in navigation_events:
            self.notebook.bind(sequence, self.guard_tab_navigation)
        # TouchpadScroll is supported by newer Tk builds only.
        if "<TouchpadScroll>" in self.notebook.bind_class("TNotebook"):
            self.notebook.bind("<TouchpadScroll>", self.guard_tab_navigation)

    def guard_tab_navigation(self, event=None):
        if self.direct_tab_navigation_enabled:
            return
        if event is not None and hasattr(event, "x") and hasattr(event, "y"):
            try:
                target_tab = self.notebook.index(f"@{event.x},{event.y}")
            except tk.TclError:
                return "break"
            if self.can_user_open_tab(target_tab):
                return
        return "break"

    def mark_design_step_complete(self, index):
        if index in self.design_step_indexes:
            self.completed_design_steps.add(index)
            self.update_tab_accessibility()
            self.update_navigation_visibility()

    def on_main_dimensions_changed(self):
        # A different calculation needs a new downstream design before the tab
        # headers can be used freely again.
        self.completed_design_steps.intersection_update({1})
        self.completed_design_steps.add(1)
        self.direct_tab_navigation_enabled = False
        self.update_tab_accessibility()
        self.update_navigation_visibility()
        meridional_tab = getattr(self, "tab3", None)
        invalidate = getattr(meridional_tab, "invalidate_design", None)
        if callable(invalidate):
            invalidate()
        # Thickness and STL meshes are cached separately from the main dimensions.
        # They must be rebuilt for the newly selected operating condition.
        for name in ("bladeX", "bladeY", "bladeZ"):
            setattr(self.gv, name, None)
        thickness_tab = getattr(self, "tab7", None)
        if thickness_tab is not None:
            thickness_tab._set_view_runner_enabled(False)
        export_tab = getattr(self, "tabx", None)
        if export_tab is not None:
            export_tab.blade_mesh = None

    def create_navigation_frame(self):
        self.navigation_frame = ttk.Frame(self, relief="ridge", padding=5)
        self.navigation_frame.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(1, weight=0)

        # Prev / Next
        self.previous_button = ttk.Button(self.navigation_frame, text="<< Previous",
                command=self.previous_page)
        self.previous_button.pack(side="left", padx=50, pady=2)
        self.next_button = ttk.Button(self.navigation_frame, text="Update & Next >>",
                command=self.next_page)
        self.next_button.pack(side="right", padx=50, pady=2)

    def update_navigation_visibility(self, event=None):
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab in self.hidden_nav_tabs:
            self.navigation_frame.grid_remove()
        else:
            self.navigation_frame.grid()
        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        if not hasattr(self, "next_button"):
            return
        current_tab = self.notebook.index(self.notebook.select())
        on_export_tab = current_tab == self.notebook_tab_count - 1
        if current_tab > 0:
            self.previous_button.state(["!disabled"])
        else:
            self.previous_button.state(["disabled"])

        if on_export_tab:
            if self.next_button.winfo_manager():
                self.next_button.pack_forget()
        elif not self.next_button.winfo_manager():
            self.next_button.pack(side="right", padx=50, pady=2)

        can_advance = (
            not on_export_tab
            and self.can_advance_from_tab(current_tab)
        )
        if can_advance:
            self.next_button.state(["!disabled"])
        else:
            self.next_button.state(["disabled"])

    def next_page(self):
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab < self.notebook_tab_count - 1:
            prepare = getattr(self.tabs[current_tab], "prepare_for_next", None)
            if callable(prepare) and prepare() is False:
                return
            if not self.can_advance_from_tab(current_tab):
                self.update_navigation_buttons()
                return
            next_tab = current_tab + 1
            self.notebook.tab(next_tab, state="normal")
            self.notebook.select(next_tab)
            if current_tab == 1:
                refresh = getattr(self.tab3, "refresh_if_needed", None)
                if callable(refresh):
                    refresh()
            if (next_tab == self.notebook_tab_count - 1
                    and self.design_step_indexes <= self.completed_design_steps):
                self.direct_tab_navigation_enabled = True
            self.update_navigation_visibility()

    def previous_page(self):
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab > 0:
            self.notebook.select(current_tab - 1)
            self.update_navigation_visibility()




if __name__ == "__main__":
    app = MainApp()
    app.mainloop()

"""
***In case github pulling doesn't work:
git reset --hard
git pull origin main
"""
