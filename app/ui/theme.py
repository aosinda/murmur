"""Colour palettes for light and dark mode."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    name: str
    bg: str
    sidebar: str
    surface: str
    border: str
    text: str
    subtext: str
    accent: str
    danger: str
    warning: str


LIGHT = Palette(
    name="light",
    bg="#F4F1EB",
    sidebar="#EDEAE3",
    surface="#FFFFFF",
    border="#E0DBD3",
    text="#1C1A18",
    subtext="#6B6660",
    accent="#34C759",
    danger="#E5342A",
    warning="#E07800",
)

DARK = Palette(
    name="dark",
    bg="#1C1A18",
    sidebar="#161412",
    surface="#252320",
    border="#38342F",
    text="#F4F1EB",
    subtext="#8A857E",
    accent="#32D74B",
    danger="#FF453A",
    warning="#FF9F0A",
)


def get(name: str) -> Palette:
    return LIGHT if name == "light" else DARK
