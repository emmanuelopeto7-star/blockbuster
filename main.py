import customtkinter as ctk

from database import initialize_db
from gui_pages import LoginScreen, configure_treeview_style

# Make sure the SQLite tables exist before any screen tries to query them.
initialize_db()

# Global CustomTkinter look and feel for the whole app.
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class BlockbusterApp(ctk.CTk):
    """Root window. Holds whichever screen (Login/Customer/Clerk/Admin) is currently active."""

    def __init__(self):
        super().__init__()
        self.title("Modern Blockbuster System")
        self.geometry("900x600")
        self.current_frame = None
        configure_treeview_style()  # ttk.Treeview needs manual theming to match CTk's dark mode
        self.switch_frame(LoginScreen, self)

    def switch_frame(self, frame_class, *args):
        """Tears down the current screen and replaces it with a new one (e.g. Login -> Dashboard)."""
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame=frame_class(self, *args)
        self.current_frame.pack(fill="both", expand=True)


if __name__=="__main__":
    app = BlockbusterApp()
    app.mainloop()
