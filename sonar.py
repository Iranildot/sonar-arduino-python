import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from customtkinter import *

# SETS THE SCALING OF THE WIDGETS
set_widget_scaling(1.3)

class SonarGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sonar GUI")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)

        # FRAME FOR THE SONAR PLOT
        self.plot_frame = CTkFrame(root)
        self.plot_frame.rowconfigure(0, weight=1)
        self.plot_frame.columnconfigure(0, weight=1)
        self.plot_frame.grid(row=0, column=1, sticky=tk.NSEW)

        # FRAME FOR THE CONTROLS
        self.control_frame = CTkFrame(root, fg_color="#111111", corner_radius=0)
        self.control_frame.grid(row=0, column=0, sticky=tk.NS)
        
        # INITIAL VARIABLES
        self.angle_scale = 10
        self.distance_scale = 0.4
        self.polar_angle = 0
        self.add = 1
        self.object_angle = 0
        self.object_distance = 2
        self.sonar_range = 4
        self.detected_objects = [None for _ in range(181)]

        # CREATES THE CONTROLS
        self.create_controls()
        # CREATES THE SONAR PLOT
        self.create_sonar_plot()
        
        self.root.protocol("WM_DELETE_WINDOW", self.close_plot)

        # INITIALIZE THE SWEEP ANGLE
        self.sweep_angle = 0
        
        # INITIAL SWEEP LINE
        self.sweep_line, = self.ax.plot([0, 0], [0, self.sonar_range], color='red')
        self.sweep()

    def create_controls(self):
        # LABEL AND ENTRY FOR ANGLE
        entries_frame = CTkFrame(self.control_frame, fg_color="#111111", corner_radius=0)
        entries_frame.grid(padx=20, pady=20)
        CTkLabel(entries_frame, text="Angle scale", text_color="#FFFFFF", width=5).grid(row=0, column=0)
        self.angle_scale_combobox = CTkComboBox(entries_frame, values=["10°", "20°", "30°", "60°", "90°", "180°"], state="readonly")
        self.angle_scale_combobox.grid(row=0, column=1, padx=10)
        self.angle_scale_combobox.set(self.angle_scale_combobox._values[0])
        
        CTkLabel(entries_frame, text="Sonar Range (m)", text_color="#FFFFFF", width=5).grid(row=1, column=0, pady=(10, 0))
        self.sonar_range_entry = CTkEntry(entries_frame)
        self.sonar_range_entry.grid(row=1, column=1, padx=10, pady=(10, 0))
        self.sonar_range_entry.insert(0, self.sonar_range)
        
        CTkLabel(entries_frame, text="Distance scale (m)", text_color="#FFFFFF", width=5).grid(row=2, column=0, pady=(10, 0))
        self.distance_scale_entry = CTkEntry(entries_frame)
        self.distance_scale_entry.grid(row=2, column=1, padx=10, pady=(10, 0))
        self.distance_scale_entry.insert(0, self.distance_scale)

        # BUTTON TO UPDATE THE SONAR PLOT
        self.update_button = CTkButton(self.control_frame, text="Update Sonar", command=self.update_sonar_plot)
        self.update_button.grid(pady=20)

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
        self.update_distance_axis_variables()
        self.update_angle_axis_variables()
        
        plt.yticks(self.distances, self.distances_labels)
        plt.xticks(self.angles[:-1], self.angle_labels)
        
        # ADJUST TO SHOW ONLY A HALF-CIRCLE
        self.ax.set_thetamin(0)
        self.ax.set_thetamax(180)
        
        # UPDATE THE LIMITS OF THE SONAR PLOT
        self.ax.set_ylim(0, self.sonar_range)
    
    def update_angle_axis_variables(self):
        # SAMPLE DATA FOR THE RADAR PLOT
        self.angle_labels = np.array(["0°"] + [f"{angle}°" for angle in range(self.angle_scale, 180, self.angle_scale)] + ["180°"])
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
            
            counter += self.distance_scale
            
            if counter > self.sonar_range:
                self.sonar_range = self.distances[-1]
                break
        
        self.distances_labels[0] = f"{self.distances[0]}"
        length = len(self.distances) // 2
        self.distances_labels[length] = f"{self.distances[length]}"
        self.distances_labels[-1] = f"{self.distances[-1]} m"
        
    def update_sonar_plot(self):
        try:
            self.angle_scale = int(self.angle_scale_combobox.get().replace("°", ""))
            self.sonar_range = float(self.sonar_range_entry.get().strip())
            self.distance_scale = float(self.distance_scale_entry.get().strip())
            self.plot_radar()
            self.canvas.draw()
            self.root.update()
            
        except ValueError:
            print("Invalid input. Please enter a valid number for the radius.")
            
    def sweep(self):
        # UPDATE THE ANGLE FOR THE SWEEP LINE
        self.sweep_angle += self.add  # ADJUST THE STEP FOR SMOOTHER OR FASTER SWEEP
        if self.sweep_angle >= 180:
            self.add = -1
        if self.sweep_angle <= 0:
            self.add = 1

        # UPDATE THE SWEEP LINE DATA
        self.object_angle = (np.pi * self.sweep_angle) / 180
        self.sweep_line.set_data([0.0, self.object_angle], [0.0, self.sonar_range])
        
        self.identify_object()

        # REDRAW THE CANVAS
        self.canvas.draw()

        # CALL THIS METHOD AGAIN AFTER A SHORT DELAY
        self.root.after(10, self.sweep)  # ADJUST THE DELAY FOR FASTER OR SLOWER SWEEP
    
    def identify_object(self):
        # REMOVE PREVIOUSLY DETECTED OBJECT IF ANY
        if self.detected_objects[self.sweep_angle - 1] is not None:
            self.detected_objects[self.sweep_angle - 1].remove()
            self.detected_objects[self.sweep_angle - 1] = None
        
        # ADD NEW DETECTED OBJECT IF WITHIN DETECTION RANGE
        if self.object_distance > 0:
            self.detected_objects[self.sweep_angle - 1], = plt.plot(self.object_angle, self.object_distance, "go", markeredgecolor="black", markeredgewidth=1)
            plt.plot(self.object_angle, self.sonar_range, "go", markeredgecolor="black", markeredgewidth=1)[0].remove()
            
    def close_plot(self):
        plt.close()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = SonarGUI(root)
    root.mainloop()
