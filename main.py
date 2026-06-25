import customtkinter as ctk

from gui_pages import LoginScreen, configure_treeview_style

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class BlockbusterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Modern Blockbuster System")
        self.geometry("900x600")
        self.current_frame = None
        configure_treeview_style()
        self.switch_frame(LoginScreen, self)

    def switch_frame(self, frame_class, *args):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame=frame_class(self, *args)
        self.current_frame.pack(fill="both", expand=True)

if __name__=="__main__":
    app = BlockbusterApp()
    app.mainloop()


    