import pygame

class keybinds:
	"""
	Optimized keybinds:
	- pre-rendered label surfaces (normal/pressed)
	- reuse Rect via rect.update(...)
	- minimal allocations in draw
	"""
	def __init__(self, base_width, base_height, font, lift=40):
		self.rows = [["A", "Z", "E"], ["Q", "S", "D"]]
		self.base_width = base_width
		self.base_height = base_height
		self.lift = lift

		self.default_btn_w = 70
		self.default_btn_h = 54
		self.default_gap = 12

		self.font = font or pygame.font.Font(None, 20)

		self.buttons = {}
		for lab in sum(self.rows, []):
			rect = pygame.Rect(0, 0, self.default_btn_w, self.default_btn_h)
			self.buttons[lab] = {
				"rect": rect,
				"pressed": False,
				"label": lab,
				"_surf": None,
				"_surf_pressed": None,
			}
		self._prepare_label_surfaces()

		self.key_to_label = {}
		for lab in sum(self.rows, []):
			try:
				kc = getattr(pygame, f"K_{lab.lower()}")
			except Exception:
				continue
			self.key_to_label[kc] = lab

	def _prepare_label_surfaces(self):

		f = self.font if hasattr(self.font, "render") else pygame.font.Font(None, 20)
		for lab, info in self.buttons.items():
			info["_surf"] = f.render(str(lab), True, (220, 220, 220))
			info["_surf_pressed"] = f.render(str(lab), True, (255, 255, 255))

		self._title_surf = f.render("KEYBINDS", True, (200, 200, 200))

	def set_font(self, font):
		if font is not None and font is not self.font:
			self.font = font
			self._prepare_label_surfaces()

	def handle_event(self, event):

		et = event.type
		if et in (pygame.KEYDOWN, pygame.KEYUP):
			lab = self.key_to_label.get(event.key)
			if lab:
				self.buttons[lab]["pressed"] = (et == pygame.KEYDOWN)
				return

		if et in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP) and getattr(event, "button", None) == 1:
			pos = getattr(event, "pos", None)
			if pos is None:
				return
			for info in self.buttons.values():
				if info["rect"].collidepoint(pos):
					info["pressed"] = (et == pygame.MOUSEBUTTONDOWN)

	def draw_keybinds_panel(self, surface, window_rect):
		win = window_rect or surface.get_rect()
		draw_rect = pygame.draw.rect
		btn_w_default = self.default_btn_w
		btn_h_default = self.default_btn_h
		gap = self.default_gap

		draw_rect(surface, (25,25,25), win, border_radius=8)
		draw_rect(surface, (60,60,60), win, 1, border_radius=8)

		title_surf = getattr(self, "_title_surf", None)
		if title_surf is None:
			self._prepare_label_surfaces()
			title_surf = self._title_surf
		surface.blit(title_surf, (win.x + 12, win.y + 8))

		padding_x = 12
		padding_top = win.y + 8 + title_surf.get_height() + 8
		padding_bottom = 12

		cols = max(len(row) for row in self.rows)
		rows = len(self.rows)

		available_w = max(0, win.w - padding_x * 2)
		available_h = max(0, win.h - (padding_top - win.y) - padding_bottom)

		btn_w = min(btn_w_default, max(40, (available_w - (cols - 1) * gap) // cols))
		btn_h = min(btn_h_default, max(30, (available_h - (rows - 1) * gap) // rows))

		total_w = cols * btn_w + (cols - 1) * gap
		start_x = win.x + (win.w - total_w) // 2

		for r_idx, row in enumerate(self.rows):
			y = padding_top + r_idx * (btn_h + gap)
			for c_idx, lab in enumerate(row):
				x = start_x + c_idx * (btn_w + gap)
				info = self.buttons[lab]
				info["rect"].update(x, y, btn_w, btn_h)

				pressed = info["pressed"]
				if pressed:
					border_color, border_w = (255,255,255), 4
					label_surf = info["_surf_pressed"]
				else:
					border_color, border_w = (110,110,110), 2
					label_surf = info["_surf"]
				draw_rect(surface, border_color, info["rect"], border_w, border_radius=10)

				ls = label_surf
				surface.blit(ls, ls.get_rect(center=info["rect"].center))

	def get_state(self):
		return {lab: info["pressed"] for lab, info in self.buttons.items()}