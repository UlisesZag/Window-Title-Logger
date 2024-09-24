import time
import datetime
import atexit
import sys
import os
import webbrowser

from PIL import Image
import pystray

from tkinter.messagebox import showinfo, showerror

import modules.process_info as procinfo
import modules.ui as ui
import modules.configfile as configfile

script_dir = os.path.dirname(os.path.realpath(__file__))


def file_append_line(path, string):
    with open(path, "a", encoding="utf-8") as file:
        file.write(string)

def log_message(path, string):
    try:
        print(string)
        file_append_line(path, string+"\n")
    except PermissionError:
        print(f"ERROR: Permission denied for file {path}. Make sure the program has the correct permissions. Try running as admin.")
        showerror("Error", f"Permission denied for file {path}. Make sure the program has the correct permissions. Try running as admin.")
        sys.exit(1)

class App:
    def main(self):
        self.stop_flag = False
        self.log_started = False
        self.proc_name = ""

        if len(sys.argv) == 1:
            #self.proc_name = input("Process name to log: ")
            self.ui = ui.ProcessSelectGUI(
                log_loop_func=self.log_loop_from_ui, 
                logs_folder_func=self.open_logs_dir,
                script_dir=script_dir
                )
            self.ui.mainloop()
        else:
            self.proc_name = sys.argv[1]
            print("Process to log: ",self.proc_name)
            self.log_loop(self.proc_name)

    def log_loop_from_ui(self, proc_name):
        self.ui.destroy()
        self.proc_name = proc_name
        self.log_loop(proc_name)

    #Bucle de logeo
    def log_loop(self, proc_name):
        #Carga la configuracion
        config = configfile.load_config(script_dir+"/config.json")

        ui.send_toast(
            f"Started logging {proc_name}",
            f"Window Title Logger started logging the process {proc_name} into the file {proc_name}.log. You can access the logger from the system tray.",
            script_dir+'/strayico.ico'
            )

        if not os.path.isdir(script_dir + "/logs/"):
            os.mkdir(script_dir + "/logs/")

        log_file_path = script_dir + "/logs/" + proc_name+".log"
        last_title = ""

        #Crea el icono
        self.sticon = SystemTrayIcon(
            cancel_func = self.cancel_logging,
            open_log_func = self.open_log,
            process_logging = self.proc_name
        )
        self.sticon.setup_system_tray()

        atexit.register(self.exit_handler)


        #Espera a que el programa arranque
        print("Waiting for the process to start...")
        seconds = 30
        while seconds > 0:
            proc_handle = procinfo.get_proc_handle(proc_name)
            t = procinfo.get_window_title_by_handle(proc_handle)
            if proc_handle != None and t != None:
                break
        
            #Si lo cancelan deja de esperar al proceso
            if self.stop_flag:
                seconds = -1
                break
            
            time.sleep(config["wait_time_interval"])
            seconds -= config["wait_time_interval"]
        
        #Si seconds es 0 quiere decir timeout, no encontro el programa y sale sin esperar.
        if seconds <= 0:
            print("Timeout. Exiting...")
            return
        
        self.log_started = True
        log_message(log_file_path, f"--- Log started for process {proc_name}, at {datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")} ---")

        #Bucle principal donde registra los titulos
        while True:
            # Flag para cancelar el logger desde el systray
            if self.stop_flag:
                break

            proc_handle = procinfo.get_proc_handle(proc_name)
            
            #Si es none quiere decir que el proceso logueado se termino de ejecutar. Entonces cierra el bucle
            if proc_handle == None:
                break

            proc_title = procinfo.get_window_title_by_handle(proc_handle)
            if last_title != proc_title:
                log_message(log_file_path, f"[{datetime.datetime.now().strftime("%d/%m/%Y %I:%M%p")}] "+proc_title)
                last_title = proc_title
            
            #TODO: Crear un menu de configuracion donde se ajuste el tiempo de espera a nuevo escaneo.
            time.sleep(config["log_time_interval"]) 
        
        #Fin del programa.
        log_message(log_file_path,f"--- Process {proc_name} finished, at {datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")} ---")

        #Para el icono del system tray
        self.sticon.stop_system_tray()

        ui.send_toast(
            f"Stopped logging {proc_name}",
            f"Window Title Logger finished logging the process {proc_name}.",
            script_dir+'/strayico.ico'
            )

    #Manejador de cerrar el programa
    def exit_handler(self):
        #Fin del programa.
        if self.log_started:
            log_message(script_dir + "/logs/" + self.proc_name+".log", f"--- Logger terminated, at {datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")} ---")
        
        self.sticon.stop_system_tray()
    
    #Cancela el loggeo poniendo el flag de parar como True;
    #Este se chequea en cada iteracion del bucle principal; Si es True se interrumpe.
    def cancel_logging(self):
        self.stop_flag = True
    
    #Abre el archivo de log
    def open_log(self):
        log_path = script_dir+"/logs/"+self.proc_name+".log"

        print(f"Opening file: {log_path}")

        if os.path.exists(log_path):
            webbrowser.open(log_path)
    
    def open_logs_dir(self):
        webbrowser.open(script_dir+"/logs/")


class SystemTrayIcon():
    def __init__(self, cancel_func = None, open_log_func = None, process_logging = "PROCESS LOGGING"):
        self.icon = None
        self.cancel_func = cancel_func
        self.open_log_func = open_log_func
        self.process_logging = process_logging

    def setup_system_tray(self):
        image = Image.open(script_dir+"/strayico.ico")
        menu = (pystray.MenuItem(f' - Process logging: {self.process_logging} - ',  None),
                pystray.MenuItem('Open log file', self.open_log_func),
                pystray.MenuItem('End logging',self.cancel_logging))
        self.icon = pystray.Icon("Window Title Logger", image, "Window Title Logger", menu)

        self.icon.run_detached(setup=self.icon_loop)
    
    def stop_system_tray(self):
        self.icon.stop()
    
    def cancel_logging(self):
        self.icon.stop()
        self.cancel_func()
    
    def icon_loop(self, icon):
        icon.visible = True

if __name__ == '__main__':
    app = App()
    app.main()
    
