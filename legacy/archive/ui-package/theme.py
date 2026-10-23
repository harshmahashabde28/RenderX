"""Design tokens, color palettes, and typographic styling for the RenderX UI."""
from dataclasses import dataclass
from typing import Tuple, Dict
import pygame

Color = Tuple[int, int, int]


@dataclass(frozen=True)
class Palette:
    name: str
    background: Color
    surface: Color
    surface_hover: Color
    surface_active: Color
    border: Color
    border_focus: Color
    accent: Color
    accent_hover: Color
    text: Color
    text_dim: Color
    grid: Color
    success: Color
    warning: Color
    danger: Color
    selected: Color


# Palettes
PALETTE_DARK = Palette(
    name="Dark",
    background=(18, 20, 26),
    surface=(28, 32, 42),
    surface_hover=(38, 44, 58),
    surface_active=(48, 56, 74),
    border=(45, 52, 68),
    border_focus=(90, 160, 255),
    accent=(76, 175, 80),
    accent_hover=(96, 195, 100),
    text=(235, 240, 248),
    text_dim=(140, 152, 172),
    grid=(30, 35, 46),
    success=(76, 175, 80),
    warning=(255, 179, 0),
    danger=(239, 83, 80),
    selected=(255, 215, 64),
)

PALETTE_LIGHT = Palette(
    name="Light",
    background=(245, 247, 250),
    surface=(255, 255, 255),
    surface_hover=(235, 240, 246),
    surface_active=(220, 228, 238),
    border=(205, 215, 228),
    border_focus=(30, 120, 240),
    accent=(46, 125, 50),
    accent_hover=(56, 142, 60),
    text=(30, 36, 48),
    text_dim=(90, 102, 120),
    grid=(225, 230, 238),
    success=(46, 125, 50),
    warning=(230, 140, 0),
    danger=(211, 47, 47),
    selected=(230, 160, 0),
)

PALETTE_HIGH_CONTRAST = Palette(
    name="High-Contrast",
    background=(0, 0, 0),
    surface=(20, 20, 20),
    surface_hover=(50, 50, 50),
    surface_active=(80, 80, 80),
    border=(255, 255, 255),
    border_focus=(255, 255, 0),
    accent=(0, 255, 255),
    accent_hover=(128, 255, 255),
    text=(255, 255, 255),
    text_dim=(190, 190, 190),
    grid=(60, 60, 60),
    success=(0, 255, 0),
    warning=(255, 255, 0),
    danger=(255, 0, 0),
    selected=(255, 255, 0),
)

PALETTE_COLORBLIND = Palette(
    name="Colorblind-Safe",
    background=(18, 20, 26),
    surface=(28, 32, 42),
    surface_hover=(40, 46, 60),
    surface_active=(52, 60, 78),
    border=(50, 58, 76),
    border_focus=(230, 159, 0),
    accent=(86, 180, 233),       # Sky blue
    accent_hover=(110, 200, 255),
    text=(240, 244, 250),
    text_dim=(150, 160, 178),
    grid=(32, 38, 50),
    success=(0, 158, 115),       # Bluish green
    warning=(240, 228, 66),      # Yellow
    danger=(213, 94, 0),         # Vermilion
    selected=(230, 159, 0),      # Orange
)

THEMES: Dict[str, Palette] = {
    "Dark": PALETTE_DARK,
    "Light": PALETTE_LIGHT,
    "High-Contrast": PALETTE_HIGH_CONTRAST,
    "Colorblind-Safe": PALETTE_COLORBLIND,
}

# Active theme
current_theme = PALETTE_DARK


def set_theme(name: str) -> Palette:
    global current_theme
    if name in THEMES:
        current_theme = THEMES[name]
    return current_theme


# Spacing tokens
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 16
SPACE_LG = 24
SPACE_XL = 32

# Radii tokens
RADIUS_SM = 4
RADIUS_MD = 6
RADIUS_LG = 10

# Font sizes
FONT_SM = 14
FONT_BODY = 18
FONT_SUBTITLE = 22
FONT_TITLE = 28
FONT_HERO = 36

_font_cache: Dict[Tuple[int, bool], pygame.font.Font] = {}


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Retrieve or create a cached Pygame font instance."""
    if not pygame.font.get_init():
        pygame.font.init()
    key = (size, bold)
    if key not in _font_cache:
        # Fallback system font chain
        font_name = pygame.font.match_font("consolas,dejavusansmono,monospace")
        try:
            f = pygame.font.Font(font_name, size)
        except Exception:
            f = pygame.font.Font(None, size)
        if bold:
            f.set_bold(True)
        _font_cache[key] = f
    return _font_cache[key]


def clear_font_cache() -> None:
    _font_cache.clear()
