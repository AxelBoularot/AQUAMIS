import pygame
import random
import time

try:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure

    _HAS_MPL = True
except Exception:
    _HAS_MPL = False

class Graphs_Main:
    def __init__(self, surface, width, height, max_value_pressure, max_value_depth, color_pressure, color_depth, label_pressure, label_depth, target_pressure, target_depth, x_offset=1127, y_offset=201, max_time=10, grid_spacing=20):
        self.surface = surface
        self.width = width
        self.height = height
        self.max_value_pressure = max_value_pressure
        self.max_value_depth = max_value_depth
        self.color_pressure = color_pressure
        self.color_depth = color_depth
        self.label_pressure = label_pressure
        self.label_depth = label_depth
        self.target_pressure = target_pressure  
        self.target_depth = target_depth  
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.max_time = max_time
        self.grid_spacing = grid_spacing  
        self.depth_progress = 0
        self.data_pressure = []
        self.data_depth = []
        self.time_stamps = []

        self.enabled_series: set[str] = {"pressure", "depth"}

        self._mpl_size: tuple[int, int] | None = None
        self._fig = None
        self._canvas = None
        self._ax = None
        self._ax_depth = None
        self._line_pressure = None
        self._line_depth = None

        if _HAS_MPL:
            self._ensure_mpl()

    def is_series_enabled(self, name: str) -> bool:
        n = str(name).strip().lower()
        return n in self.enabled_series

    def toggle_series(self, name: str) -> None:
        n = str(name).strip().lower()
        if n not in ("pressure", "depth"):
            return
        if n in self.enabled_series:
            self.enabled_series.remove(n)
        else:
            self.enabled_series.add(n)
        if not self.enabled_series:
            self.enabled_series = {"pressure", "depth"}

    def _ensure_mpl(self) -> None:
        if not _HAS_MPL:
            return
        w = max(10, int(self.width))
        h = max(10, int(self.height))
        if self._mpl_size == (w, h) and self._fig is not None:
            return

        self._mpl_size = (w, h)

        dpi = 100
        fig = Figure(figsize=(w / dpi, h / dpi), dpi=dpi)
        fig.patch.set_facecolor((0.10, 0.10, 0.10))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.set_facecolor((0.10, 0.10, 0.10))

        axis_c = (0.85, 0.85, 0.85)
        tick_c = (0.80, 0.80, 0.80)
        grid_c = (0.35, 0.35, 0.35)

        ax.set_xlim(0, float(self.max_time))
        ax.set_ylim(0, float(self.max_value_pressure) if self.max_value_pressure else 1.0)
        ax.grid(True, color=grid_c, alpha=0.35, linewidth=0.8)
        ax.tick_params(axis="both", colors=tick_c, labelsize=7, length=3, width=1)
        ax.spines["left"].set_color(axis_c)
        ax.spines["bottom"].set_color(axis_c)
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.set_xlabel("t (s)", color=tick_c, fontsize=7, labelpad=2)
        ax.set_ylabel("pressure", color=tick_c, fontsize=7, labelpad=2)

        ax_depth = ax.twinx()
        ax_depth.set_facecolor((0.10, 0.10, 0.10))
        ax_depth.set_ylim(0, float(self.max_value_depth) if self.max_value_depth else 1.0)
        ax_depth.tick_params(axis="y", colors=tick_c, labelsize=7, length=3, width=1)
        ax_depth.spines["right"].set_color(axis_c)
        ax_depth.spines["top"].set_visible(False)
        ax_depth.spines["left"].set_visible(False)
        ax_depth.set_ylabel("depth", color=tick_c, fontsize=7, labelpad=2)

        fig.subplots_adjust(left=0.12, right=0.88, bottom=0.18, top=0.94)

        (line_pressure,) = ax.plot([], [], color=(1.0, 0.0, 0.0), linewidth=2)
        (line_depth,) = ax_depth.plot([], [], color=(0.0, 0.0, 1.0), linewidth=2)

        self._fig = fig
        self._canvas = canvas
        self._ax = ax
        self._ax_depth = ax_depth
        self._line_pressure = line_pressure
        self._line_depth = line_depth
        
    def add_data(self, value_pressure, value_depth):
        current_time = time.time()
        
        self.data_pressure.append(value_pressure)
        self.data_depth.append(value_depth)
        self.time_stamps.append(current_time)
        
        while self.time_stamps[0] < current_time - self.max_time:
            self.data_pressure.pop(0)
            self.data_depth.pop(0)
            self.time_stamps.pop(0)
    
    def draw_grid(self):
        return
    
    def draw(self):
        self.draw_grid()  
        
        font = pygame.font.SysFont('Arial', 20)
        text_pressure = font.render(self.label_pressure, True, (255, 255, 255))
        self.surface.blit(text_pressure, (self.x_offset + 5, self.y_offset - 20))
        
        text_depth = font.render(self.label_depth, True, (255, 255, 255))
        self.surface.blit(text_depth, (self.x_offset + 5, self.y_offset - 40))
        
        legend_font = pygame.font.SysFont('CenturySchoolBook', 15)

        if len(self.data_pressure) > 0 and len(self.data_depth) > 0:
            current_pressure_value = self.data_pressure[-1]
            current_depth_value = self.data_depth[-1]

            inactive = (140, 155, 170)
            pressure_c = (255, 0, 0) if "pressure" in self.enabled_series else inactive
            depth_c = (0, 0, 255) if "depth" in self.enabled_series else inactive

            pressure_value_text = legend_font.render(f"Pressure: {int(current_pressure_value)}", True, pressure_c)
            depth_value_text = legend_font.render(f"Depth: {int(current_depth_value)} m", True, depth_c)
            
            self.surface.blit(pressure_value_text, (self.x_offset + self.width + 20, self.y_offset + 100))
            self.surface.blit(depth_value_text, (self.x_offset + self.width + 20, self.y_offset + 70))

        if len(self.data_pressure) > 1 and len(self.data_depth) > 1:
            if not _HAS_MPL:
                start_time = self.time_stamps[0]

                for i in range(1, len(self.data_pressure)):
                    elapsed_time = self.time_stamps[i] - start_time

                    start_x_pressure = self.x_offset + (elapsed_time) * (self.width / (self.time_stamps[-1] - start_time))
                    start_y_pressure = self.y_offset + self.height - (self.data_pressure[i - 1] / self.max_value_pressure) * self.height
                    end_x_pressure = self.x_offset + ((elapsed_time + (self.time_stamps[i] - self.time_stamps[i - 1])) * (self.width / (self.time_stamps[-1] - start_time)))
                    end_y_pressure = self.y_offset + self.height - (self.data_pressure[i] / self.max_value_pressure) * self.height

                    if "pressure" in self.enabled_series:
                        pygame.draw.line(self.surface, self.color_pressure, (start_x_pressure, start_y_pressure), (end_x_pressure, end_y_pressure), 2)

                    start_x_depth = self.x_offset + (elapsed_time) * (self.width / (self.time_stamps[-1] - start_time))
                    start_y_depth = self.y_offset + self.height - (self.data_depth[i - 1] / self.max_value_depth) * self.height
                    end_x_depth = self.x_offset + ((elapsed_time + (self.time_stamps[i] - self.time_stamps[i - 1])) * (self.width / (self.time_stamps[-1] - start_time)))
                    end_y_depth = self.y_offset + self.height - (self.data_depth[i] / self.max_value_depth) * self.height

                    if "depth" in self.enabled_series:
                        pygame.draw.line(self.surface, self.color_depth, (start_x_depth, start_y_depth), (end_x_depth, end_y_depth), 2)

                pygame.draw.line(self.surface, (255, 255, 255), (self.x_offset+1, self.y_offset), (self.x_offset+1, self.y_offset + self.height), 2)
                pygame.draw.line(self.surface, (255, 255, 255), (self.x_offset, self.y_offset + self.height), (self.x_offset + self.width, self.y_offset + self.height), 2)
                return

            self._ensure_mpl()
            if not self.time_stamps:
                return

            start_time = self.time_stamps[0]
            xs = [max(0.0, min(float(self.max_time), float(t - start_time))) for t in self.time_stamps]

            self._ax.set_xlim(0, float(self.max_time))
            self._ax.set_ylim(0.0, float(self.max_value_pressure) if self.max_value_pressure else 1.0)
            if self._ax_depth is not None:
                self._ax_depth.set_ylim(0.0, float(self.max_value_depth) if self.max_value_depth else 1.0)

            self._line_pressure.set_data(xs, self.data_pressure)
            self._line_depth.set_data(xs, self.data_depth)

            self._line_pressure.set_visible("pressure" in self.enabled_series)
            self._line_depth.set_visible("depth" in self.enabled_series)

            self._canvas.draw()
            buf = self._canvas.buffer_rgba()
            w, h = self._mpl_size
            img = pygame.image.frombuffer(buf.tobytes(), (w, h), "RGBA")
            self.surface.blit(img, (int(self.x_offset), int(self.y_offset)))


    def update_graph_main(self):
        fluctuation_pressure = random.uniform(-0.2, 0.2)
        new_pressure_value = self.target_pressure + fluctuation_pressure
        new_pressure_value = max(11.8, min(12.2, new_pressure_value))

        if self.depth_progress < 10:
            self.depth_progress += 0.01 
        else:
            self.depth_progress = 10

        new_depth_value = self.target_depth + self.depth_progress
        new_depth_value = max(0, min(self.max_value_depth, new_depth_value))
        
        self.add_data(new_pressure_value, new_depth_value)
        self.draw()
