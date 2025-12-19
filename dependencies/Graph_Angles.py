import pygame
import time

try:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure

    _HAS_MPL = True
except Exception:
    _HAS_MPL = False

class Graphs_Angles:
    def __init__(self, surface, width, height, max_value, x_offset=1127, y_offset=19, max_time=10, grid_spacing=20):
        self.surface = surface
        self.width = width
        self.height = height
        self.max_value = max_value
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.max_time = max_time
        self.grid_spacing = grid_spacing
        
        self.data_roll = []
        self.data_pitch = []
        self.data_yaw = []
        self.time_stamps = []

        # Which curves are enabled (toggled by clicking labels)
        self.enabled_series: set[str] = {"roll", "pitch", "yaw"}

        self._mpl_size: tuple[int, int] | None = None
        self._fig = None
        self._canvas = None
        self._ax = None
        self._line_roll = None
        self._line_pitch = None
        self._line_yaw = None

        if _HAS_MPL:
            self._ensure_mpl()

    def is_series_enabled(self, name: str) -> bool:
        n = str(name).strip().lower()
        return n in self.enabled_series

    def toggle_series(self, name: str) -> None:
        n = str(name).strip().lower()
        if n not in ("roll", "pitch", "yaw"):
            return
        if n in self.enabled_series:
            self.enabled_series.remove(n)
        else:
            self.enabled_series.add(n)

        # Never allow all three to be off (keeps the graph meaningful)
        if not self.enabled_series:
            self.enabled_series = {"roll", "pitch", "yaw"}

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
        ax.set_xlim(0, float(self.max_time))
        ax.set_ylim(-float(self.max_value), float(self.max_value))

        axis_c = (0.85, 0.85, 0.85)
        tick_c = (0.80, 0.80, 0.80)
        grid_c = (0.35, 0.35, 0.35)

        # Show axes + ticks (requested)
        ax.spines["left"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        ax.spines["left"].set_color(axis_c)
        ax.spines["bottom"].set_color(axis_c)
        ax.spines["left"].set_linewidth(1.0)
        ax.spines["bottom"].set_linewidth(1.0)
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)

        ax.tick_params(axis="both", colors=tick_c, labelsize=7, length=3, width=1)
        ax.grid(True, color=grid_c, alpha=0.35, linewidth=0.8)
        ax.axhline(0.0, color=axis_c, linewidth=1.0, alpha=0.9)

        (line_roll,) = ax.plot([], [], color=(1.0, 0.0, 0.0), linewidth=2)
        (line_pitch,) = ax.plot([], [], color=(0.0, 1.0, 0.0), linewidth=2)
        (line_yaw,) = ax.plot([], [], color=(0.0, 0.0, 1.0), linewidth=2)

        self._fig = fig
        self._canvas = canvas
        self._ax = ax
        self._line_roll = line_roll
        self._line_pitch = line_pitch
        self._line_yaw = line_yaw
    
    def add_data(self, roll, pitch, yaw):
        current_time = time.time()
        
        self.data_roll.append(roll)
        self.data_pitch.append(pitch)
        self.data_yaw.append(yaw)
        self.time_stamps.append(current_time)
        
        while self.time_stamps[0] < current_time - self.max_time:
            self.data_roll.pop(0)
            self.data_pitch.pop(0)
            self.data_yaw.pop(0)
            self.time_stamps.pop(0)
    
    def draw_grid(self):
        return
    
    def draw(self):
        self.draw_grid()

        if not _HAS_MPL:
            # Fallback to the previous manual rendering
            colors = {'roll': (255, 0, 0), 'pitch': (0, 255, 0), 'yaw': (0, 0, 255)}

            series_order = ["roll", "pitch", "yaw"]
            series_data = {
                "roll": self.data_roll,
                "pitch": self.data_pitch,
                "yaw": self.data_yaw,
            }

            if len(self.data_roll) > 1:
                start_time = self.time_stamps[0]

                for i in range(1, len(self.data_roll)):
                    elapsed_time = self.time_stamps[i] - start_time

                    for key in series_order:
                        if key not in self.enabled_series:
                            continue
                        data = series_data[key]
                        color = colors[key]
                        start_x = self.x_offset + elapsed_time * (self.width / self.max_time)
                        start_y = self.y_offset + self.height - (data[i-1] / self.max_value) * self.height
                        end_x = self.x_offset + (elapsed_time + (self.time_stamps[i] - self.time_stamps[i-1])) * (self.width / self.max_time)
                        end_y = self.y_offset + self.height - (data[i] / self.max_value) * self.height

                        pygame.draw.line(self.surface, color, (start_x, start_y), (end_x, end_y), 2)

                    pygame.draw.line(self.surface, (255, 255, 255), (self.x_offset, self.y_offset), (self.x_offset, self.y_offset + self.height), 2)
                    pygame.draw.line(self.surface, (255, 255, 255), (self.x_offset, self.y_offset + self.height), (self.x_offset + self.width, self.y_offset + self.height), 2)
            return

        self._ensure_mpl()
        if not self.time_stamps:
            return

        start_time = self.time_stamps[0]
        xs = [max(0.0, min(float(self.max_time), float(t - start_time))) for t in self.time_stamps]
        self._ax.set_xlim(0, float(self.max_time))
        self._ax.set_ylim(-float(self.max_value), float(self.max_value))

        self._line_roll.set_data(xs, self.data_roll)
        self._line_pitch.set_data(xs, self.data_pitch)
        self._line_yaw.set_data(xs, self.data_yaw)

        self._line_roll.set_visible("roll" in self.enabled_series)
        self._line_pitch.set_visible("pitch" in self.enabled_series)
        self._line_yaw.set_visible("yaw" in self.enabled_series)

        self._canvas.draw()
        buf = self._canvas.buffer_rgba()
        w, h = self._mpl_size
        img = pygame.image.frombuffer(buf.tobytes(), (w, h), "RGBA")
        self.surface.blit(img, (int(self.x_offset), int(self.y_offset)))

    
    def update_graph_angles(self, roll, pitch, yaw):
        self.add_data(roll, pitch, yaw)
        self.draw()
