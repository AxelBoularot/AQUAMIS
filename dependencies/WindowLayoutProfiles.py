from __future__ import annotations

import json
import os
import re
from typing import Any, Callable

import pygame

from dependencies.Variable import WHITE, CARD_BG


_STORE_PATH = os.path.join("data", "window_layout_profiles.json")


def _ensure_store_shape(store: Any) -> dict[str, Any]:
    if not isinstance(store, dict):
        store = {}
    profiles = store.get("profiles")
    if not isinstance(profiles, dict):
        profiles = {}
    last_profile = store.get("last_profile")
    if not isinstance(last_profile, str):
        last_profile = ""
    return {"profiles": profiles, "last_profile": last_profile}


def load_store() -> dict[str, Any]:
    try:
        with open(_STORE_PATH, "r", encoding="utf-8") as f:
            return _ensure_store_shape(json.load(f))
    except FileNotFoundError:
        return _ensure_store_shape({})
    except json.JSONDecodeError:
        return _ensure_store_shape({})


def save_store(store: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(_STORE_PATH), exist_ok=True)
    with open(_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(_ensure_store_shape(store), f, ensure_ascii=False, indent=2)


def list_profiles() -> list[str]:
    store = load_store()
    names = [n for n in store["profiles"].keys() if isinstance(n, str) and n.strip()]
    names.sort(key=lambda s: s.lower())
    return names


def get_last_profile_name() -> str:
    store = load_store()
    name = store.get("last_profile")
    return name if isinstance(name, str) else ""


def set_last_profile_name(name: str) -> None:
    store = load_store()
    store["last_profile"] = str(name)
    save_store(store)


def save_profile(name: str, snapshot: dict[str, Any]) -> None:
    store = load_store()
    store["profiles"][name] = snapshot
    store["last_profile"] = name
    save_store(store)


def load_profile(name: str) -> dict[str, Any] | None:
    store = load_store()
    prof = store["profiles"].get(name)
    return prof if isinstance(prof, dict) else None


_NAME_RE = re.compile(r"^[\w\- ]{1,32}$", re.UNICODE)


def normalize_profile_name(raw: str) -> str:
    name = (raw or "").strip()
    if not name:
        return ""
    if not _NAME_RE.match(name):
        return ""
    return name


def open_profile_name_modal(*, on_submit: Callable[[str], None], title: str = "Nom du profil :") -> None:
    surf = pygame.display.get_surface()
    if surf is None:
        return

    globals()["LAYOUT_PROFILE_MODAL"] = {
        "input_text": "",
        "cursor_visible": True,
        "last_blink": pygame.time.get_ticks(),
        "modal_w": 560,
        "modal_h": 170,
        "title": title,
        "message": None,
        "message_time": 0,
        "close_after": None,
        "on_submit": on_submit,
    }


def profile_modal_handle_event(event) -> bool:
    state = globals().get("LAYOUT_PROFILE_MODAL")
    if not state:
        return False

    if event.type == pygame.QUIT:
        return True

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            del globals()["LAYOUT_PROFILE_MODAL"]
            return True
        if event.key == pygame.K_RETURN:
            name = normalize_profile_name(state["input_text"])
            if not name:
                state["message"] = "Nom invalide (1-32: lettres/chiffres/espace/_/-)"
                state["message_time"] = pygame.time.get_ticks()
                return True
            try:
                cb = state.get("on_submit")
                if callable(cb):
                    cb(name)
                state["message"] = "Profil enregistré"
                state["message_time"] = pygame.time.get_ticks()
                state["close_after"] = pygame.time.get_ticks() + 700
            except Exception:
                state["message"] = "Erreur lors de l'enregistrement"
                state["message_time"] = pygame.time.get_ticks()
            return True
        if event.key == pygame.K_BACKSPACE:
            state["input_text"] = state["input_text"][:-1]
            return True
        if event.unicode and ord(event.unicode) >= 32:
            if len(state["input_text"]) < 32:
                state["input_text"] += event.unicode
            return True

    if event.type == pygame.MOUSEBUTTONDOWN:
        mx, my = event.pos
        surf = pygame.display.get_surface()
        sx = (surf.get_width() - state["modal_w"]) // 2
        sy = (surf.get_height() - state["modal_h"]) // 2
        local_x, local_y = mx - sx, my - sy

        save_btn = pygame.Rect(state["modal_w"] - 140, state["modal_h"] - 50, 110, 38)
        cancel_btn = pygame.Rect(state["modal_w"] - 280, state["modal_h"] - 50, 110, 38)

        if save_btn.collidepoint((local_x, local_y)):
            name = normalize_profile_name(state["input_text"])
            if not name:
                state["message"] = "Nom invalide (1-32: lettres/chiffres/espace/_/-)"
                state["message_time"] = pygame.time.get_ticks()
                return True
            try:
                cb = state.get("on_submit")
                if callable(cb):
                    cb(name)
                state["message"] = "Profil enregistré"
                state["message_time"] = pygame.time.get_ticks()
                state["close_after"] = pygame.time.get_ticks() + 700
            except Exception:
                state["message"] = "Erreur lors de l'enregistrement"
                state["message_time"] = pygame.time.get_ticks()
            return True

        if cancel_btn.collidepoint((local_x, local_y)):
            del globals()["LAYOUT_PROFILE_MODAL"]
            return True

    return False


def profile_modal_draw(surface) -> None:
    state = globals().get("LAYOUT_PROFILE_MODAL")
    if not state:
        return

    now = pygame.time.get_ticks()
    if now - state["last_blink"] > 500:
        state["cursor_visible"] = not state["cursor_visible"]
        state["last_blink"] = now

    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    mw, mh = state["modal_w"], state["modal_h"]
    modal = pygame.Surface((mw, mh))
    modal.fill(CARD_BG)
    pygame.draw.rect(modal, WHITE, modal.get_rect(), 2)

    font = pygame.font.SysFont("Arial", 20)
    title = font.render(state.get("title") or "Nom du profil :", True, WHITE)
    modal.blit(title, (18, 12))

    hint = pygame.font.SysFont("Arial", 16).render("(1-32: lettres/chiffres/espace/_/-)", True, (200, 200, 200))
    modal.blit(hint, (18, 34))

    input_rect = pygame.Rect(18, 58, mw - 36, 36)
    pygame.draw.rect(modal, (20, 20, 20), input_rect)
    pygame.draw.rect(modal, WHITE, input_rect, 1)

    txt = state["input_text"]
    txt_surf = font.render(txt, True, WHITE)
    modal.blit(txt_surf, (input_rect.x + 8, input_rect.y + 6))
    if state["cursor_visible"]:
        cursor_x = input_rect.x + 8 + txt_surf.get_width()
        pygame.draw.rect(modal, WHITE, (cursor_x, input_rect.y + 8, 2, input_rect.height - 16))

    save_btn = pygame.Rect(mw - 140, mh - 50, 110, 38)
    cancel_btn = pygame.Rect(mw - 280, mh - 50, 110, 38)
    pygame.draw.rect(modal, (0, 120, 200), save_btn, border_radius=8)
    pygame.draw.rect(modal, (120, 120, 120), cancel_btn, border_radius=8)
    save_label = font.render("Sauvegarder", True, WHITE)
    cancel_label = font.render("Annuler", True, WHITE)
    modal.blit(
        save_label,
        (
            save_btn.x + (save_btn.width - save_label.get_width()) // 2,
            save_btn.y + (save_btn.height - save_label.get_height()) // 2,
        ),
    )
    modal.blit(
        cancel_label,
        (
            cancel_btn.x + (cancel_btn.width - cancel_label.get_width()) // 2,
            cancel_btn.y + (cancel_btn.height - cancel_label.get_height()) // 2,
        ),
    )

    if state.get("message"):
        msg = state["message"]
        ok = "enregistr" in msg.lower() or "profil" in msg.lower()
        color = (80, 220, 80) if ok else (220, 80, 80)
        msg_surf = font.render(msg, True, color)
        modal.blit(msg_surf, (18, mh - 44))

    sx, sy = (surface.get_width() - mw) // 2, (surface.get_height() - mh) // 2
    surface.blit(modal, (sx, sy))

    if state.get("close_after") and now >= state["close_after"]:
        del globals()["LAYOUT_PROFILE_MODAL"]
