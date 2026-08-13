"""Bespoke Spotify & Netflix inspired dark theme colors and fonts for the GUI Dashboard."""

from __future__ import annotations


class Theme:
    """Color palette and styling tokens for a premium, high-contrast dark UI."""

    # Backgrounds (Obsidian Black)
    BG_DARK = "#0a0a0a"         # Pitch black main panel
    SIDEBAR_BG = "#000000"      # Pure black sidebar panel
    CARD_BG = "#121212"         # Spotify charcoal-black card backgrounds
    CARD_HOVER = "#1c1c1c"      # Slightly lighter charcoal
    
    # Accents (Spotify Green & Netflix Red)
    PRIMARY = "#1ed760"         # Spotify Neon Green brand accent
    PRIMARY_HOVER = "#1db954"   # Muted Spotify Green
    
    SECONDARY = "#3b82f6"       # Electric Blue secondary brand accent
    SECONDARY_HOVER = "#2563eb" # Deep Blue
    
    # Status Indicators
    SUCCESS = "#1ed760"         # Spotify Green
    SUCCESS_HOVER = "#1db954"   # Muted green
    
    WARNING = "#fbbf24"         # Golden Amber
    WARNING_HOVER = "#d97706"   # Muted Amber
    
    DANGER = "#e50914"          # Netflix Red
    DANGER_HOVER = "#b9090b"    # Muted Netflix Red
    
    # Neutral Text Colors
    TEXT_MAIN = "#ffffff"       # Pure white high contrast text
    TEXT_MUTED = "#a7a7a7"      # Spotify muted gray text
    TEXT_DARK = "#000000"       # Low contrast black
    
    # Borders & Button Containers
    BORDER = "#282828"          # Spotify outline/disabled container gray (distinct against #121212)
    BORDER_LIGHT = "#3e3e3e"    # Lighter active border line
