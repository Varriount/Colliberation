from Tkinter import *
import ttk


class TKCollabApp(Frame):

    def say_hi(self):
        print "hi there, everyone!"

    def createWidgets(self):
        self.tabs = ttk.Notebook(self)
        frame = Frame(self.tabs)
        tab_1 = ttk.Frame(self.tabs)
        tab_2 = ttk.Frame(self.tabs)
        tab_3 = ttk.Frame(self.tabs)
        tab_4 = ttk.Frame(self.tabs)

        self.tabs.add(frame, text=" main ")
        self.tabs.add(tab_1, text=" 1 ")
        self.tabs.add(tab_2, text=" 2 ")
        self.tabs.add(tab_3, text=" 3 ")
        self.tabs.add(tab_4, text=" 4 ")
        self.tabs.pack()

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

root = Tk()
app = TKCollabApp(master=root)
app.mainloop()
root.destroy()
