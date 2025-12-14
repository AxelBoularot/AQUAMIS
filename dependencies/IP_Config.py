import pygame
import json
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from dependencies.Variable import WHITE, CARD_BG

def save_ip(ip_address):
    data = {"ip": ip_address}
    with open("data/data.json", "w") as f:
        json.dump(data, f)
    globals()['LAST_SAVED_IP'] = ip_address

def load_ip():
    with open("data/data.json", "r",encoding="utf-8") as f:
        return json.load(f)

def open_tk_window():
    surf = pygame.display.get_surface()
    if surf is None:
        return

    globals()['IP_MODAL'] = {
        'input_text': '',
        'cursor_visible': True,
        'last_blink': pygame.time.get_ticks(),
        'modal_w': 560,
        'modal_h': 160,
        'message': None,
        'message_time': 0,
        'close_after': None,
    }


def validate_ip(ip_str: str) -> bool:
    import re
    pattern = r'^\s*(?:25[0-5]|2[0-4]\d|1?\d{1,2})(?:\.(?:25[0-5]|2[0-4]\d|1?\d{1,2})){3}\s*$'
    return re.match(pattern, ip_str) is not None


def ip_modal_handle_event(event):
    state = globals().get('IP_MODAL')
    if not state:
        return False

    if event.type == pygame.QUIT:
        return True

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            del globals()['IP_MODAL']
            return True
        if event.key == pygame.K_RETURN:
            ip = state['input_text'].strip()
            if validate_ip(ip):
                save_ip(ip)
                state['message'] = 'IP enregistrée'
                state['message_time'] = pygame.time.get_ticks()
                state['close_after'] = pygame.time.get_ticks() + 900
            else:
                state['message'] = 'IP invalide'
                state['message_time'] = pygame.time.get_ticks()
            return True
        if event.key == pygame.K_BACKSPACE:
            state['input_text'] = state['input_text'][:-1]
            return True
        if event.unicode and ord(event.unicode) >= 32:
            state['input_text'] += event.unicode
            return True

    if event.type == pygame.MOUSEBUTTONDOWN:
        mx, my = event.pos
        surf = pygame.display.get_surface()
        sx = (surf.get_width() - state['modal_w']) // 2
        sy = (surf.get_height() - state['modal_h']) // 2
        local_x, local_y = mx - sx, my - sy
        save_btn = pygame.Rect(state['modal_w'] - 140, state['modal_h'] - 50, 110, 38)
        cancel_btn = pygame.Rect(state['modal_w'] - 280, state['modal_h'] - 50, 110, 38)
        if save_btn.collidepoint((local_x, local_y)):
            ip = state['input_text'].strip()
            if validate_ip(ip):
                save_ip(ip)
                state['message'] = 'IP enregistrée'
                state['message_time'] = pygame.time.get_ticks()
                state['close_after'] = pygame.time.get_ticks() + 900
            else:
                state['message'] = 'IP invalide'
                state['message_time'] = pygame.time.get_ticks()
            return True
        if cancel_btn.collidepoint((local_x, local_y)):
            del globals()['IP_MODAL']
            return True

    return False

def ip_modal_draw(surface):
    """Draw the IP modal over `surface` and auto-close on success."""
    state = globals().get('IP_MODAL')
    if not state:
        return

    now = pygame.time.get_ticks()
    if now - state['last_blink'] > 500:
        state['cursor_visible'] = not state['cursor_visible']
        state['last_blink'] = now

    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    mw, mh = state['modal_w'], state['modal_h']
    modal = pygame.Surface((mw, mh))
    modal.fill(CARD_BG)
    pygame.draw.rect(modal, WHITE, modal.get_rect(), 2)

    font = pygame.font.SysFont('Arial', 20)
    title = font.render("Entrer l'adresse IP :", True, WHITE)
    modal.blit(title, (18, 12))

    input_rect = pygame.Rect(18, 48, mw - 36, 36)
    pygame.draw.rect(modal, (20, 20, 20), input_rect)
    pygame.draw.rect(modal, WHITE, input_rect, 1)

    txt = state['input_text']
    txt_surf = font.render(txt, True, WHITE)
    modal.blit(txt_surf, (input_rect.x + 8, input_rect.y + 6))
    if state['cursor_visible']:
        cursor_x = input_rect.x + 8 + txt_surf.get_width()
        pygame.draw.rect(modal, WHITE, (cursor_x, input_rect.y + 8, 2, input_rect.height - 16))

    save_btn = pygame.Rect(mw - 140, mh - 50, 110, 38)
    cancel_btn = pygame.Rect(mw - 280, mh - 50, 110, 38)
    pygame.draw.rect(modal, (0, 120, 200), save_btn, border_radius=8)
    pygame.draw.rect(modal, (120, 120, 120), cancel_btn, border_radius=8)
    save_label = font.render('Sauvegarder', True, WHITE)
    cancel_label = font.render('Annuler', True, WHITE)
    modal.blit(save_label, (save_btn.x + (save_btn.width - save_label.get_width()) // 2, save_btn.y + (save_btn.height - save_label.get_height()) // 2))
    modal.blit(cancel_label, (cancel_btn.x + (cancel_btn.width - cancel_label.get_width()) // 2, cancel_btn.y + (cancel_btn.height - cancel_label.get_height()) // 2))

    if state.get('message'):
        msg = state['message']
        color = (80, 220, 80) if 'enregistr' in msg else (220, 80, 80)
        msg_surf = font.render(msg, True, color)
        modal.blit(msg_surf, (18, mh - 44))

    sx, sy = (surface.get_width() - mw) // 2, (surface.get_height() - mh) // 2
    surface.blit(modal, (sx, sy))

    if state.get('close_after') and now >= state['close_after']:
        del globals()['IP_MODAL']

def open_excel_table_console(matrix):
    """
    Demande via la console :
    - Le nombre de lignes et de colonnes du tableau Excel.
    - Les valeurs de chaque ligne (les valeurs doivent être séparées par un espace).
    
    Puis utilise Tkinter pour ouvrir une boîte de dialogue permettant de choisir
    l'emplacement et le nom du fichier Excel. Le tableau est ensuite sauvegardé
    grâce à pandas.
    """
    
    # Utiliser Tkinter pour choisir le chemin d'enregistrement du fichier Excel
    root = tk.Tk()
    root.withdraw()  # Masquer la fenêtre principale Tkinter
    file_path = filedialog.asksaveasfilename(
        title="Enregistrer le tableau Excel",
        defaultextension=".xlsx",
        filetypes=[("Fichiers Excel", "*.xlsx"), ("Tous les fichiers", "*.*")]
    )
    if file_path:
        df = pd.DataFrame(matrix)
        df.to_excel(file_path, index=False, header=False)
        print("Tableau Excel sauvegardé dans", file_path)
    else:
        print("Aucun chemin sélectionné, opération annulée.")
    root.destroy()