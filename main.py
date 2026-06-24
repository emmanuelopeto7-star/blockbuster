import tkinter as tk

from gui_pages import LoginScreen

class BlockbusterApp(tk.Tk):
    def __init__(self):
        super(). __init__()
        self.title("Modern Blockbuster System")
        self.geometry("900x600")
        self.current_frame = None
        self.switch_frame(LoginScreen, self)

    def switch_frame(self, frame_class, *args):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame=frame_class(self, *args)
        self.current_frame.pack(fill="both", expand=True)

if __name__=="__main__":
    app = BlockbusterApp()
    app.mainloop()


    