import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import time

class GraphManager:
    def __init__(self, root, update_interval=1, max_speed=255, max_depth=50, pressure_value=1.0):
        self.root = root
        self.update_interval = update_interval
        self.max_speed = max_speed
        self.max_depth = max_depth
        self.pressure_value = pressure_value
        
        self.times = []
        self.speeds = []
        self.depths = []
        self.pressures = []

        self.start_time = time.time()

        # Création des sous-graphes Matplotlib
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, figsize=(10, 6))
        plt.subplots_adjust(hspace=1, top=0.95)
        self._setup_axes()
        
        # Intégration Matplotlib dans Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _setup_axes(self):
        self.fig.patch.set_facecolor('#2D2D2D')
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.set_facecolor('#404040')
            ax.tick_params(axis='both', colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')

        self.ax1.set_ylim(0, self.max_speed)
        self.ax1.set_xlabel('Temps écoulé (s)')
        self.ax1.set_ylabel('Vitesse moteur')
        self.ax1.set_title('Vitesse moteur en temps réel')
        
        self.ax2.set_ylim(0, self.max_depth)
        self.ax2.set_xlabel('Temps écoulé (s)')
        self.ax2.set_ylabel('Profondeur (m)')
        self.ax2.set_title('Profondeur en temps réel')
        
        self.ax3.set_ylim(0, 2)
        self.ax3.set_xlabel('Temps écoulé (s)')
        self.ax3.set_ylabel('Pression (bar)')
        self.ax3.set_title('Pression en temps réel')

        self.line1, = self.ax1.plot([], [], label="Vitesse")
        self.line2, = self.ax2.plot([], [], color='green', label="Profondeur")
        self.line3, = self.ax3.plot([], [], color='red', label="Pression")

    def update_graph(self, new_speed, new_depth, new_pressure):
        elapsed_time = time.time() - self.start_time
        
        self.times.append(elapsed_time)
        self.speeds.append(new_speed)
        self.depths.append(new_depth)
        self.pressures.append(new_pressure)
        
        # Mise à jour des axes X pour afficher toutes les données
        self.ax1.set_xlim(0, elapsed_time)
        self.ax2.set_xlim(0, elapsed_time)
        self.ax3.set_xlim(0, elapsed_time)
        
        self.line1.set_data(self.times, self.speeds)
        self.line2.set_data(self.times, self.depths)
        self.line3.set_data(self.times, self.pressures)

        self.canvas.draw()

    def draw(self):
        new_speed = np.random.randint(0, self.max_speed + 1)
        depth_variation = np.random.uniform(-0.1, 0.1) 
        new_depth = 7 + depth_variation
        new_pressure = self.pressure_value + np.random.uniform(-0.1, 0.1)
         
        self.update_graph(new_speed, new_depth, new_pressure)
        
    def run(self):
        self.root.after(self.update_interval * 1000, self.run)
        self.draw()

