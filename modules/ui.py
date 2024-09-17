import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo

import sys
import psutil

import modules.process_info as proc_info

class ProcessSelectGUI(tk.Tk):
    def __init__(self, log_loop_func):
        super().__init__()
        self.log_loop_func = log_loop_func
        self.proc_var = tk.StringVar(value="")
    
        #Construimos la UI
        self.title("Window Title Logger")

        #Menu bar
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)

        self.about_menu = tk.Menu(self.menubar)
        self.about_menu.add_command(
            label='About',
            command=self.about,
        )

        self.menubar.add_cascade(
            label="About",
            menu=self.about_menu
        )

        #Frame
        self.select_frame = ttk.Labelframe(self, text="Process Selection")
        self.select_frame.pack(expand=True, fill="both", padx=10, pady=5, ipadx=5, ipady=5)
        self.columnconfigure(0, weight=1)
        self.select_frame.columnconfigure(0, weight=1)
        self.select_frame.columnconfigure(1, weight=3)
        #Label
        self.select_label = ttk.Label(self.select_frame, text="Process to log: ")
        self.select_label.grid(column=0, row=0, sticky=tk.E)
        #Selector de procesos
        self.select_combobox = ttk.Combobox(self.select_frame, textvariable=self.proc_var, values=(1,2,3), state="readonly")
        self.select_combobox.grid(column=1, row=0, sticky=tk.EW)
        self.bind("<1>", lambda e: self.update_processes_options())

        #Boton de logear
        self.log_button = ttk.Button(self.select_frame, text="Start logging", command=self.log)
        self.log_button.grid(column=0, row=1, columnspan=2, sticky=tk.NSEW)

        self.update_processes_options()

    def log(self):
        if self.proc_var.get() != "":
            self.log_loop_func(self.proc_var.get())
    
    def update_processes_options(self):
        procs = []
        for i in psutil.process_iter():
            if proc_info.is_visible_by_id(i.pid):
                procs.append(i.name())

        self.select_combobox["values"] = procs
    
    def about(self):
        showinfo("About", 
'''Window Title Logger v0.1
Github: https://github.com/UlisesZag/Window-Title-Logger
Licence: MIT
'''
)