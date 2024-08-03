import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from customtkinter import *
from PIL import Image
from serial_connection import *
import time

# SETS THE SCALING OF THE WIDGETS
set_widget_scaling(1.3)

class SonarGUI:
    def __init__(self, root):
        
        self.root = root
        self.root.title("Sonar GUI")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        
        # DEFINING ARDUINO'S VARIABLES
        self.serial_connection = SerialConnection()
        self.ports = self.serial_connection.check_available_ports()["ports"]
        self.arduino = None

        # FRAME FOR THE SONAR PLOT
        self.plot_frame = CTkFrame(root)
        self.plot_frame.rowconfigure(0, weight=1)
        self.plot_frame.columnconfigure(0, weight=1)
        self.plot_frame.grid(row=0, column=1, sticky=tk.NSEW)

        # FRAME FOR THE CONTROLS
        self.control_frame = CTkScrollableFrame(root, fg_color="#111111", corner_radius=0, width=280)
        self.control_frame.grid(row=0, column=0, sticky=tk.NSEW)
        
        # INITIAL VARIABLES
        self.sonar_settings = {
                                "mode": "BOUNCE",
                                "angle_scale": 30,
                                "distance_scale": 0.1,
                                "range": 1.0,
                                "step": 1,
                              }
        
        self.sonar_settings_pre_saved = self.sonar_settings.copy()
        
        self.scan_started = False
        self.scan_step = 1

        self.detected_object = {
                                 "degree": 0,
                                 "radian": 0.0,
                                 "distance": 0.0,
                                 "on_plot": [None for _ in range(181)]
                               }

        # CREATES THE CONTROLS
        self.create_controls()
        # CREATES THE SONAR PLOT
        self.create_sonar_plot()
        
        # INITIAL SCAN LINE
        self.scan_line, = self.ax.plot([0, 0], [0, self.sonar_settings["range"]], color='red')
        self.checking_divices()
        self.scan()
        
        self.root.bind_all("<Key>", self.key_press)
        self.root.bind_all("<1>", self.button_press)
        
        self.root.protocol("WM_DELETE_WINDOW", self.cancel)

    def create_controls(self):
        
        # ARDUINO CONTROLS
        arduino_settings_frame = CTkFrame(self.control_frame, fg_color="#333333")
        arduino_settings_frame.grid(padx=20, pady=(20, 0), sticky=tk.EW)
        
        self.connected_arduino_label = CTkLabel(arduino_settings_frame, 
                                                text="ARDUINO COTROLS", 
                                                font=("helvetica", 14, "bold"), 
                                                text_color="#FFFFFF",
                                                compound="right",
                                                image=CTkImage(light_image=Image.open("./icons/usb_off.png")))
        self.connected_arduino_label.grid(row=0, column=0, padx=(10, 0), pady=10, columnspan=2, sticky=tk.W)
        
        # FOR ANGLE SCALE
        CTkLabel(arduino_settings_frame, 
                 text="ARDUINO BOARD", 
                 text_color="#FFFFFF").grid(row=1, column=0, padx=10, pady=(0, 20), sticky=tk.W)
        self.arduino_board_combobox = CTkComboBox(arduino_settings_frame, 
                                                  values=[""],
                                                  width=100,
                                                  state="readonly",
                                                  command=self.connect_arduino)
        self.arduino_board_combobox.grid(row=1, column=1, padx=(0, 10), pady=(0, 20))
        self.arduino_board_combobox.set(self.arduino_board_combobox._values[0])
        
        # SONAR INFO
        sonar_info_frame = CTkFrame(self.control_frame,
                                    fg_color="#333333")
        sonar_info_frame.grid(padx=20, pady=(20, 0), sticky=tk.EW)
        
        CTkLabel(sonar_info_frame,
                 text="SONAR INFO",
                 font=("helvetica", 14, "bold"),
                 text_color="#FFFFFF",
                 compound="right",
                 image=CTkImage(light_image=Image.open("./icons/info.png"))).grid(row=0, column=0, padx=(10, 0), pady=10, columnspan=2, sticky=tk.W)
        
        # FOR CURRENT ANGLE
        CTkLabel(sonar_info_frame,
                 text="CURRENT ANGLE",
                 text_color="#FFFFFF").grid(row=2, column=0, padx=10, pady=(10, 0), sticky=tk.W)
        self.current_angle_label = CTkLabel(sonar_info_frame,
                                            text="",
                                            fg_color="#F0F0F0",
                                            width=100,
                                            corner_radius=5)
        self.current_angle_label.grid(row=2, column=1, padx=10, pady=(10, 0))
        
        # FOR OBJECT DISTANCE
        CTkLabel(sonar_info_frame,
                 text="OBJECT DISTANCE",
                 text_color="#FFFFFF").grid(row=3, column=0, padx=10, pady=(10, 20), sticky=tk.W)
        self.object_distance_label = CTkLabel(sonar_info_frame,
                                              text="",
                                              fg_color="#F0F0F0",
                                              width=100,
                                              corner_radius=5)
        self.object_distance_label.grid(row=3, column=1, padx=10, pady=(10, 20))

        # BUTTON TO START SCANNING
        self.start_stop_button = CTkButton(self.control_frame,
                                           text="START SCANNING",
                                           fg_color="#008833",
                                           hover_color="#006611",
                                           image=CTkImage(light_image=Image.open("./icons/flip.png")),
                                           command=self.start_scan)
        self.start_stop_button.grid(pady=10)        
        
        
        # SONAR CONTROLS
        sonar_settings_frame = CTkFrame(self.control_frame,
                                        fg_color="#333333")
        sonar_settings_frame.grid(padx=20, sticky=tk.EW)
        
        CTkLabel(sonar_settings_frame,
                 text="SONAR COTROLS",
                 font=("helvetica", 14, "bold"),
                 text_color="#FFFFFF",
                 compound="right",
                 image=CTkImage(light_image=Image.open("./icons/radar.png"))).grid(row=0, column=0, padx=(10, 0), pady=10, columnspan=2, sticky=tk.W)
        
        self.sonar_mode_segmented_button = CTkSegmentedButton(sonar_settings_frame, 
                                             values=["BOUNCE", "0°", "180°"], 
                                             selected_color="#006611", 
                                             selected_hover_color="#006611",
                                             unselected_hover_color="#006611",
                                             unselected_color="#008833",
                                             fg_color="#008833",
                                             text_color="#FFFFFF",)
        self.sonar_mode_segmented_button.grid(columnspan=2, padx=10, pady=(0, 20), sticky=tk.EW)
        self.sonar_mode_segmented_button.set(self.sonar_settings["mode"])
        
        
        # FOR ANGLE SCALE
        CTkLabel(sonar_settings_frame,
                 text="ANGLE SCALE",
                 text_color="#FFFFFF").grid(row=2, column=0, padx=10, sticky=tk.W)
        self.angle_scale_combobox = CTkComboBox(sonar_settings_frame,
                                                values=["10°", "20°", "30°", "60°", "90°", "180°"],
                                                width=80,
                                                state="readonly",
                                                command=self.pre_save_sonar_settings)
        self.angle_scale_combobox.grid(row=2, column=1, padx=10)
        self.angle_scale_combobox.set(str(self.sonar_settings["angle_scale"]) + "°")
        
        # FOR DISTANCE SCALE
        CTkLabel(sonar_settings_frame,
                 text="DISTANCE SCALE (m)",
                 text_color="#FFFFFF").grid(row=3, column=0, padx=10, pady=(10, 0), sticky=tk.W)
        self.distance_scale_entry = CTkEntry(sonar_settings_frame, width=80)
        self.distance_scale_entry.grid(row=3, column=1, padx=10, pady=(10, 0))
        self.distance_scale_entry.insert(0, self.sonar_settings["distance_scale"])
        
        # FOR SONAR RANGE
        CTkLabel(sonar_settings_frame,
                 text="SONAR RANGE (m)",
                 text_color="#FFFFFF").grid(row=4, column=0, padx=10, pady=(10, 0), sticky=tk.W)
        self.sonar_range_entry = CTkEntry(sonar_settings_frame, width=80)
        self.sonar_range_entry.grid(row=4, column=1, padx=10, pady=(10, 0))
        self.sonar_range_entry.insert(0, self.sonar_settings["range"])
        
        # FOR SONAR STEP
        CTkLabel(sonar_settings_frame,
                 text="SONAR STEP",
                 text_color="#FFFFFF").grid(row=5, column=0, padx=10, pady=(10, 20), sticky=tk.W)
        self.sonar_step_combobox = CTkComboBox(sonar_settings_frame,
                                               values=["1°", "2°", "3°", "4°", "5°", "6°", "7°", "8°", "9°", "10°"],
                                               width=80,
                                               state="readonly",
                                               command=self.pre_save_sonar_settings)
        self.sonar_step_combobox.grid(row=5, column=1, padx=10, pady=(10, 20))
        self.sonar_step_combobox.set(str(self.sonar_settings["step"]) + "°")

        # BUTTON TO UPDATE THE SONAR PLOT
        self.update_button = CTkButton(self.control_frame,
                                       text="UPDATE SONAR",
                                       fg_color="#008833",
                                       hover_color="#006611",
                                       image=CTkImage(light_image=Image.open("./icons/upgrade.png")),
                                       command=self.update_sonar_plot)
        self.update_button.grid(pady=10)

    def create_sonar_plot(self):
        # CREATE THE PLOT
        self.fig, self.ax = plt.subplots(figsize=(6, 3), subplot_kw=dict(polar=True))
        #self.ax.set_ylim(0, 2)  # SET THE Y-AXIS LIMIT FOR BETTER VISUALIZATION
        self.plot_radar()

        # EMBED THE PLOT IN THE TKINTER GUI
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(sticky=tk.NSEW)

    def plot_radar(self):
        # DISTANCE AXIS
        self.update_distance_axis_variables()
        
        # ANGLE AXIS
        self.update_angle_axis_variables()
        
        # PLOT DISTANCES
        plt.yticks(self.distances, self.distances_labels)
        
        # PLOT ANGLES
        plt.xticks(self.angles[:-1], self.angle_labels)
        
        # ADJUST TO SHOW ONLY A HALF-CIRCLE
        self.ax.set_thetamin(0)
        self.ax.set_thetamax(180)
        
        # UPDATE THE LIMITS OF THE SONAR PLOT
        self.ax.set_ylim(0, self.sonar_settings["range"])
    
    def update_angle_axis_variables(self):
        # SAMPLE DATA FOR THE RADAR PLOT
        self.angle_labels = np.array(["0°"] + [f"{angle}°" for angle in range(self.sonar_settings["angle_scale"], 180, self.sonar_settings["angle_scale"])] + ["180°"])
        self.num_vars = len(self.angle_labels)

        # COMPUTE ANGLE FOR EACH AXIS
        self.angles = np.linspace(0, np.pi, self.num_vars).tolist()
        
        # COMPLETE THE LOOP
        self.angles += self.angles[:1]
    
    def update_distance_axis_variables(self):
        counter = 0
        self.distances = []
        self.distances_labels = []
        while True:
            self.distances.append(round(counter, 1))
            self.distances_labels.append("")
            
            counter += self.sonar_settings["distance_scale"]
            
            if counter > self.sonar_settings["range"]:
                self.sonar_settings["range"] = self.distances[-1]
                break
        
        self.distances_labels[0] = f"{self.distances[0]}"
        length = len(self.distances) // 2
        self.distances_labels[length] = f"{self.distances[length]}"
        self.distances_labels[-1] = f"{self.distances[-1]} m"
        
    def update_sonar_plot(self):
        if self.arduino != None:
            if self.arduino.is_open:
                try:
                    if self.sonar_settings["step"] != self.sonar_settings_pre_saved["step"]:
                        self.clear_dots()
                    
                    self.sonar_settings = self.sonar_settings_pre_saved.copy()
                    
                    self.update_button.configure(fg_color="#008833", hover_color="#006611")
                    
                    self.arduino.write(f"UPDATE:{str(self.sonar_settings["mode"]).replace("°", "")}:{str(self.sonar_settings["step"]).replace("°", "")}:{self.sonar_settings["range"]*100}:".encode())
                    
                    # UPDATE PLOT
                    self.plot_radar()
                    self.canvas.draw()
                    self.root.update()
                    
                except ValueError:
                    ...
        else:
            self.alert_window("CONNECT AN ARDUINO DEVICE!")
    
    def pre_save_sonar_settings(self, event):
        try:
            self.sonar_settings_pre_saved["mode"] = self.sonar_mode_segmented_button.get()
            self.sonar_settings_pre_saved["angle_scale"] = int(self.angle_scale_combobox.get().replace("°", "")) # ANGLE SCALE
            self.sonar_settings_pre_saved["range"] = float(self.sonar_range_entry.get().strip()) # SOANR RANGE
            self.sonar_settings_pre_saved["distance_scale"] = float(self.distance_scale_entry.get().strip()) # DISTANCE SCALE
            self.sonar_settings_pre_saved["step"] = int(self.sonar_step_combobox.get().replace("°", ""))
            
            if self.sonar_settings_pre_saved != self.sonar_settings:
                self.update_button.configure(fg_color="#DD3300", hover_color="#CC1100")
            else:
                self.update_button.configure(fg_color="#008833", hover_color="#006611")
        except ValueError:
            ...
    
    def start_scan(self):
        if self.arduino != None:
            if self.arduino.is_open:
                self.scan_started = not self.scan_started
                
                if self.scan_started:
                    self.start_stop_button.configure(text="STOP SCANNING", fg_color="#DD3300", hover_color="#CC1100")
                    self.arduino.write(f"ON:{str(self.sonar_settings["mode"]).replace("°", "")}:{str(self.sonar_settings["step"]).replace("°", "")}:{self.sonar_settings["range"]*100}:".encode())
                else:
                    self.start_stop_button.configure(text="START SCANNING", fg_color="#008833", hover_color="#006611")
                    self.arduino.write(f"OFF:".encode())
        else:
            self.alert_window("CONNECT AN ARDUINO DEVICE!")
                
    def scan(self):
        
        if self.scan_started:
            try:
                if self.arduino.inWaiting():
                    try:
                        arduino_output = self.arduino.readline().decode().split(":")
                        self.detected_object["distance"] = float(arduino_output[0])
                        self.detected_object["degree"] = int(arduino_output[1])
                        self.arduino.write(f"NEXT:".encode())
                    except:
                        self.arduino.write(f"NEXT:".encode())
            except:
                ...
                
            # UPDATE THE SCAN LINE DATA
            self.detected_object["radian"] = (np.pi * self.detected_object["degree"]) / 180
            self.scan_line.set_data([0.0, self.detected_object["radian"]], [0.0, self.sonar_settings["range"]])
            
            self.identify_object()
            self.update_sonar_info()

            # REDRAW THE CANVAS
            self.canvas.draw_idle()
        
        self.root.after(10, self.scan)
    
    def identify_object(self):
        # REMOVE PREVIOUSLY DETECTED OBJECT IF ANY
        if self.detected_object["on_plot"][self.detected_object["degree"]] is not None:
            self.detected_object["on_plot"][self.detected_object["degree"]].remove()
            self.detected_object["on_plot"][self.detected_object["degree"]] = None
        
        # ADD NEW DETECTED OBJECT IF WITHIN DETECTION RANGE
        if self.detected_object["distance"] > 0:
            self.detected_object["on_plot"][self.detected_object["degree"]], = plt.plot(self.detected_object["radian"], self.detected_object["distance"], "ro", markeredgecolor="black", markeredgewidth=1)
        
    def key_press(self, event):
        self.pre_save_sonar_settings(event)
        self.hide_drawer(event)
        
    def button_press(self, event):
        if type(event.widget) != str:
            if "entry" not in event.widget.winfo_name():
                self.root.focus()
            self.pre_save_sonar_settings(event)
        
    def hide_drawer(self, event):
        if event.keysym.upper() == "H" and "entry" not in event.widget.winfo_name():
            if self.control_frame.winfo_ismapped():
                self.control_frame.grid_forget()
            else:
                self.control_frame.grid(row=0, column=0, sticky=tk.NSEW)
    
    def update_sonar_info(self):
        self.current_angle_label.configure(text=str(self.detected_object["degree"]) + "°")
        self.object_distance_label.configure(text=str(self.detected_object["distance"]) + " m")
        
        self.root.update()
    
    # TO STABILISH SERIAL CONNECTION
    def connect_arduino(self, event) -> None:
        if self.arduino != None:
            if self.arduino.is_open:
                self.serial_connection.end(self.arduino)
        
        self.arduino = self.serial_connection.start(self.arduino_board_combobox.get())
        
        time.sleep(1)
        
        if self.arduino != None:
            self.connected_arduino_label.configure(image=CTkImage(light_image=Image.open("./icons/usb.png")))
        else:
            self.arduino_board_combobox.set(value=[])
            self.connected_arduino_label.configure(image=CTkImage(light_image=Image.open("./icons/usb_off.png")))
            self.alert_window("ARDUINO CONNECTION FAILED")

        
    # TO CHECK IF THERE ARE ARDUINOS CONNECTED TO THE USB PORTS ON USER'S COMPUTER
    def checking_divices(self) -> None:               
        
        # GETTING THE PORT
        self.ports = self.serial_connection.check_available_ports()["ports"]
        # PUT THE PORTS INTO COMBOBOX VALUES
        self.arduino_board_combobox.configure(values=self.ports)
        
        if self.arduino_board_combobox.get() not in self.ports:
            self.arduino_board_combobox.set(value=[])
            self.connected_arduino_label.configure(image=CTkImage(light_image=Image.open("./icons/usb_off.png")))
            self.scan_started = False
            self.arduino = None
            self.start_stop_button.configure(text="START SCANNING", fg_color="#008833", hover_color="#006611")
            self.object_distance_label.configure(text="")
            self.current_angle_label.configure(text="")
            self.clear_dots()
        
        # CHECKS THE USB PORTS EACH 2 SECONDS
        self.root.after(1000, self.checking_divices)
    
    # TO STOP THE SONG LOOP WHEN THE APP WINDOW CLOSE
    def cancel(self) -> None:
        plt.close()
        if self.arduino != None:
            if self.arduino.is_open:
                self.scan_started = False
                self.serial_connection.end(self.arduino)

        self.root.quit()
        
    def clear_dots(self):
        for i in range(len(self.detected_object["on_plot"])):
            if self.detected_object["on_plot"][i]:
                self.detected_object["on_plot"][i].remove()
                self.detected_object["on_plot"][i] = None
                
        self.detected_object["degree"] = 0
        self.detected_object["distance"] = 0
        self.scan_line.set_data([0.0, 0.0], [0.0, self.sonar_settings["range"]])
        self.canvas.draw_idle()
        
    def alert_window(self, message:str) -> None:
        self.window = CTkToplevel(self.root)
        self.window.attributes('-topmost', True)
        self.window.geometry("+200+200")
        self.window.resizable(False, False)
        self.window.title("Alert")
        
        self.window_frame = CTkFrame(self.window,
                                     fg_color="#111111",
                                     corner_radius=0)
        self.window_frame.grid()
        
        CTkLabel(self.window_frame,
                 text=message,
                 text_color="#FFFFFF").grid(padx=30, pady=(20, 5))
        
        CTkButton(self.window_frame,
                  text="OK",
                  fg_color="#008833",
                  hover_color="#006611",
                  command=lambda: self.window.destroy()).grid(padx=30, pady=(5, 20), columnspan=2, sticky=tk.EW)
        

if __name__ == "__main__":
    root = CTk()
    app = SonarGUI(root)
    root.mainloop()
