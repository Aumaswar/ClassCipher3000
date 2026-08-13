"""Bespoke Midnight Steel & Cyber Mint theme colors and fonts for the GUI Dashboard."""

from __future__ import annotations


class Theme:
    """Color palette and styling tokens for a custom developer-centric dark theme."""

    # Backgrounds (Midnight Steel)
    BG_DARK = "#0b0f19"         # Deep obsidian blue-black
    SIDEBAR_BG = "#111827"      # Dark slate-steel for sidebar
    CARD_BG = "#1f2937"         # Slate-800 card container background
    CARD_HOVER = "#374151"      # Slate-700 container hover state
    
    # Accents (Cyber Mint & Indigo)
    PRIMARY = "#00f5d4"         # Bespoke neon cyan/mint brand highlight
    PRIMARY_HOVER = "#00d7bb"   # Muted cyan/mint
    
    SECONDARY = "#6366f1"       # Vibrant indigo secondary accent
    SECONDARY_HOVER = "#4f46e5" # Deep indigo
    
    # Status Indicators
    SUCCESS = "#10b981"         # Emerald green
    SUCCESS_HOVER = "#059669"   # Dark emerald green
    
    WARNING = "#fbbf24"         # Warm golden amber
    WARNING_HOVER = "#d97706"   # Muted amber
    
    DANGER = "#f43f5e"          # Vibrant rose red
    DANGER_HOVER = "#e11d48"    # Deep rose red
    
    # Neutral Text Colors
    TEXT_MAIN = "#f9fafb"       # Off-white slate-50 high contrast text
    TEXT_MUTED = "#9ca3af"      # Slate-400 medium contrast text
    TEXT_DARK = "#0b0f19"       # Low contrast black
    
    # Borders
    BORDER = "#1f2937"          # Slate-800 border line
    BORDER_LIGHT = "#4b5563"    # Slate-600 active border line
