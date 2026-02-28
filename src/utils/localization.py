"""
localization.py — Lightweight i18n helper (English / Turkish).

Usage:
    from utils.localization import t, set_language, get_language, load_from_settings

    # Retrieve a translated string:
    label_text = t("waiting_for_card")

    # Change the active language at runtime:
    set_language("tr")

    # Load the saved preference from the database on startup:
    load_from_settings()
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# String table
# ---------------------------------------------------------------------------

_STRINGS: dict[str, dict[str, str]] = {
    # ── Attendance tab ────────────────────────────────────────────────────
    "attendance_title":    {"en": "Attendance",                         "tr": "Yoklama"},
    "loading_sections":    {"en": "Loading sections...",                 "tr": "Dersler yükleniyor..."},
    "listening":           {"en": "● LISTENING",                        "tr": "● DİNLİYOR"},
    "idle":                {"en": "◌ IDLE",                             "tr": "◌ BEKLİYOR"},
    "waiting_for_card":    {"en": "Waiting for card tap...",             "tr": "Kart bekleniyor..."},
    "no_taps_today":       {"en": "No taps recorded today.",             "tr": "Bugün kayıt bulunamadı."},
    "col_student":         {"en": "Student",                            "tr": "Öğrenci"},
    "col_section":         {"en": "Section",                            "tr": "Ders"},
    "col_status":          {"en": "Status",                             "tr": "Durum"},
    "col_method":          {"en": "Method",                             "tr": "Yöntem"},
    "col_time":            {"en": "Time",                               "tr": "Saat"},
    "no_sections_today":   {"en": "No sections scheduled for today",    "tr": "Bugün ders bulunmuyor"},
    "today_prefix":        {"en": "Today",                              "tr": "Bugün"},
    # ── Settings tab ─────────────────────────────────────────────────────
    "settings_title":      {"en": "Settings",                           "tr": "Ayarlar"},
    "lang_section":        {"en": "Language",                           "tr": "Dil"},
    "lang_label":          {"en": "Interface language:",                 "tr": "Arayüz dili:"},
    "lang_restart_note":   {
        "en": "Language saved. Restart the app to apply all label changes.",
        "tr": "Dil kaydedildi. Tüm etiket değişikliklerinin uygulanması için uygulamayı yeniden başlatın.",
    },
    # ── Shared status strings ─────────────────────────────────────────────
    "present":             {"en": "Present",                            "tr": "Var"},
    "absent":              {"en": "Absent",                             "tr": "Yok"},
}

# ---------------------------------------------------------------------------
# Active language state
# ---------------------------------------------------------------------------

_current_lang: str = "en"


def set_language(lang: str) -> None:
    """Set the active language code ('en' or 'tr').

    Unknown codes fall back silently to English.
    """
    global _current_lang
    _current_lang = lang if lang in ("en", "tr") else "en"


def get_language() -> str:
    """Return the currently active language code ('en' or 'tr')."""
    return _current_lang


def t(key: str) -> str:
    """Return the translated string for *key* in the active language.

    Falls back to English when the key or language is missing.
    Returns the raw *key* string if no translation exists at all.
    """
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(_current_lang, entry.get("en", key))


def load_from_settings() -> None:
    """Read the 'language' key from the settings DB and activate it.

    Should be called once during application startup, after the database
    has been initialised.
    """
    # Import here to avoid a circular import at module level
    import models.settings_model as settings_model  # noqa: PLC0415
    lang = settings_model.get_setting("language") or "en"
    set_language(lang)
