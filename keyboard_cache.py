"""
Keyboard caching system to optimize performance
"""
from typing import Dict, Optional
from aiogram.types import InlineKeyboardMarkup
from keyboards import (
    main_kb, nickname_kb, rad_kb, gofra_kb, cable_kb, top_kb,
    back_kb, atm_status_kb, gofra_info_kb, cable_info_kb, profile_extended_kb
)

class KeyboardCache:
    def __init__(self):
        self._cache: Dict[str, InlineKeyboardMarkup] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> InlineKeyboardMarkup:
        """Get cached keyboard or create new one"""
        if key in self._cache:
            self._hits += 1
            return self._cache[key]

        self._misses += 1

        # Create keyboard based on key
        if key == "main":
            keyboard = main_kb()
        elif key == "nickname":
            keyboard = nickname_kb()
        elif key == "rad":
            keyboard = rad_kb()
        elif key == "gofra":
            keyboard = gofra_kb()
        elif key == "cable":
            keyboard = cable_kb()
        elif key == "top":
            keyboard = top_kb()
        elif key == "back_main":
            keyboard = back_kb("back_main")
        elif key == "back_profile":
            keyboard = back_kb("profile")
        elif key == "back_rademka":
            keyboard = back_kb("rademka")
        elif key == "atm_status":
            keyboard = atm_status_kb()
        elif key == "gofra_info":
            keyboard = gofra_info_kb()
        elif key == "cable_info":
            keyboard = cable_info_kb()
        elif key == "profile_extended":
            keyboard = profile_extended_kb()
        else:
            # Default to main keyboard if unknown
            keyboard = main_kb()

        # Cache the keyboard
        self._cache[key] = keyboard
        return keyboard

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        hit_rate = self._hits / max(1, self._hits + self._misses)
        return {
            "cached_keyboards": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate
        }

    def clear(self):
        """Clear all cached keyboards"""
        self._cache = {}
        self._hits = 0
        self._misses = 0

# Global keyboard cache instance
keyboard_cache = KeyboardCache()

# Convenience functions
def get_main_kb() -> InlineKeyboardMarkup:
    return keyboard_cache.get("main")

def get_nickname_kb() -> InlineKeyboardMarkup:
    return keyboard_cache.get("nickname")

def get_rad_kb() -> InlineKeyboardMarkup:
    return keyboard_cache.get("rad")

def get_gofra_kb() -> InlineKeyboardMarkup:
    return keyboard_cache.get("gofra")

def get_cable_kb() -> InlineKeyboardMarkup:
    return keyboard_cache.get("cable")

def get_top_kb() -> InlineKeyboardMarkup:
    return keyboard_cache.get("top")

def get_back_main_kb() -> InlineKeyboardMarkup:
    return keyboard_cache.get("back_main")

def get_back_profile_kb() -> InlineKeyboardMarkup:
    return keyboard_cache.get("back_profile")

def get_back_rademka_kb() -> InlineKeyboardMarkup:
    return keyboard_cache.get("back_rademka")

def get_atm_status_kb() -> InlineKeyboardMarkup:
    return keyboard_cache.get("atm_status")

def get_gofra_info_kb() -> InlineKeyboardMarkup:
    return keyboard_cache.get("gofra_info")

def get_cable_info_kb() -> InlineKeyboardMarkup:
    return keyboard_cache.get("cable_info")

def get_profile_extended_kb() -> InlineKeyboardMarkup:
    return keyboard_cache.get("profile_extended")