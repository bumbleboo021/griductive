"""Navigation screens and HUD: Home, Stage Select, Gameplay Timer HUD, Pause, and Stage Cleared."""
from dataclasses import dataclass
import math
import random
import pygame
from griductive.ui import config as cfg


@dataclass(frozen=True)
class StageEntry:
    path: object
    title: str
    short_title: str
    size: int
    index: int


@dataclass(frozen=True)
class StageRecord:
    best_time_ms: int


def format_duration(ms):
    total_seconds = max(0, int(ms) // 1000)
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


def short_stage_title(title):
    parts = title.split(" - ", 2)
    return parts[2].strip() if len(parts) == 3 and parts[2].strip() else title


_SHADOW_CACHE = {}


def draw_panel(surface, rect, fill=cfg.PANEL, border=cfg.BORDER_SUBTLE, border_width=1, radius=14, shadow=True):
    if shadow:
        key = (rect.width, rect.height, radius)
        shadow_surf = _SHADOW_CACHE.get(key)
        if shadow_surf is None:
            shadow_surf = pygame.Surface((rect.width + 16, rect.height + 16), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 95), shadow_surf.get_rect(), border_radius=radius + 4)
            _SHADOW_CACHE[key] = shadow_surf
        surface.blit(shadow_surf, (rect.x - 8, rect.y - 2))
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    if border and border_width > 0:
        pygame.draw.rect(surface, border, rect, border_width, border_radius=radius)


def draw_centered_text(surface, font, text, center, color=cfg.TEXT):
    rendered = font.render(str(text), True, color)
    surface.blit(rendered, rendered.get_rect(center=center))


def main_canvas_rect():
    return pygame.Rect(0, 0, cfg.WINDOW_SIZE[0], cfg.WINDOW_SIZE[1])


def spawn_cleared_particles(canvas_rect, count=32):
    rng = random.Random()
    palette = (cfg.HIGHLIGHT, cfg.ACCENT, (255, 232, 162), (146, 238, 220))
    particles = []
    for _ in range(count):
        particles.append({
            "x": rng.uniform(canvas_rect.x + 80, canvas_rect.right - 80),
            "y": rng.uniform(canvas_rect.y + 40, canvas_rect.bottom - 80),
            "vx": rng.uniform(-14, 14),
            "vy": rng.uniform(-32, -12),
            "size": rng.uniform(2.5, 5.0),
            "phase": rng.uniform(0, math.tau),
            "color": rng.choice(palette),
        })
    return particles


def draw_cleared_particles(surface, particles, delta_ms, canvas_rect, tick):
    dt = max(0.0, min(0.05, delta_ms / 1000.0))
    for p in particles:
        p["x"] += p["vx"] * dt + math.sin(tick / 420.0 + p["phase"]) * 8.0 * dt
        p["y"] += p["vy"] * dt
        if p["y"] < canvas_rect.y + 20:
            p["y"] = canvas_rect.bottom - 30
        if p["x"] < canvas_rect.x + 30:
            p["x"] = canvas_rect.right - 30
        elif p["x"] > canvas_rect.right - 30:
            p["x"] = canvas_rect.x + 30
        pulse = 0.65 + 0.35 * math.sin(tick / 260.0 + p["phase"])
        radius = max(2, round(p["size"] * pulse))
        pygame.draw.circle(surface, p["color"], (round(p["x"]), round(p["y"])), radius)


def draw_game_hud(view):
    """Draw compact gameplay HUD pill (timer, moves, hints) and Menu button."""
    pill = pygame.Rect(348, 22, 324, 38)
    pygame.draw.rect(view.screen, cfg.PANEL, pill, border_radius=10)
    pygame.draw.rect(view.screen, cfg.BORDER_SUBTLE, pill, 1, border_radius=10)

    section_w = pill.width // 3
    # Section 1: TIME
    time_cx = pill.x + section_w // 2
    draw_centered_text(view.screen, view.tiny, "TIME", (time_cx, pill.y + 11), cfg.MUTED)
    draw_centered_text(view.screen, view.small, format_duration(view.stage_elapsed_ms), (time_cx, pill.y + 26), cfg.TEXT)

    div1_x = pill.x + section_w
    pygame.draw.line(view.screen, cfg.BORDER_SUBTLE, (div1_x, pill.y + 8), (div1_x, pill.bottom - 8), 1)

    # Section 2: MOVES
    moves_cx = div1_x + section_w // 2
    draw_centered_text(view.screen, view.tiny, "MOVES", (moves_cx, pill.y + 11), cfg.MUTED)
    draw_centered_text(view.screen, view.small, str(view.moves), (moves_cx, pill.y + 26), cfg.ACCENT)

    div2_x = div1_x + section_w
    pygame.draw.line(view.screen, cfg.BORDER_SUBTLE, (div2_x, pill.y + 8), (div2_x, pill.bottom - 8), 1)

    # Section 3: HINTS
    hints_cx = div2_x + (pill.right - div2_x) // 2
    draw_centered_text(view.screen, view.tiny, "HINTS", (hints_cx, pill.y + 11), cfg.MUTED)
    draw_centered_text(view.screen, view.small, str(view.hints_used), (hints_cx, pill.y + 26), cfg.HIGHLIGHT if view.hints_used else cfg.TEXT)

    # Menu / Pause button right beside Agent button
    view.button("pause", "Menu", pygame.Rect(684, 22, 94, 38), enabled=True, style="default")

    # If solved and the player chose "View Board", allow reopening Stage Cleared panel
    if view.engine.solved and view.cleared_dismissed:
        view.button("reopen_cleared", "Stage Cleared", pygame.Rect(468, 64, 142, 28), enabled=True, style="gold")


def draw_home(view):
    """Home Screen with hero logo, character preview, and main navigation menu."""
    view.hover_scope = "home"
    canvas = main_canvas_rect()

    view.draw_backdrop((10, 16, 24, 130))

    # Top utility strip
    badge = pygame.Rect(34, 24, 290, 36)
    pygame.draw.rect(view.screen, cfg.PANEL, badge, border_radius=18)
    pygame.draw.rect(view.screen, cfg.BORDER_SUBTLE, badge, 1, border_radius=18)
    draw_centered_text(view.screen, view.tiny, "DEDUCTION PUZZLE  |  SAT / DPLL", badge.center, cfg.ACCENT)

    music_label = "Music: On" if view.music.enabled else "Music"
    view.button("home_music", music_label, pygame.Rect(canvas.right - 306, 24, 130, 38), style="default")
    view.button("home_help", "How to Play", pygame.Rect(canvas.right - 164, 24, 130, 38), style="default")

    # Hero Title
    title_center = (canvas.centerx, 126)
    draw_centered_text(view.screen, view.title_font, "GRIDUCTIVE", (title_center[0] + 2, title_center[1] + 3), (8, 12, 18))
    draw_centered_text(view.screen, view.title_font, "GRIDUCTIVE", title_center, cfg.ACCENT)

    bar_rect = pygame.Rect(canvas.centerx - 120, 166, 240, 3)
    pygame.draw.rect(view.screen, cfg.HIGHLIGHT, bar_rect, border_radius=2)
    draw_centered_text(
        view.screen,
        view.font,
        "Every clue is true. Prove every verdict by pure logic.",
        (canvas.centerx, 192),
        cfg.TEXT,
    )

    # Center Hero Preview Panel
    showcase = pygame.Rect(canvas.centerx - 350, 224, 700, 214)
    draw_panel(view.screen, showcase, fill=(22, 32, 44), border=cfg.BORDER_SUBTLE, border_width=1, radius=16)

    preview_specs = (
        ("INNOCENT", cfg.INNOCENT_CARD, cfg.ACCENT, "Proved Innocent"),
        ("CRIMINAL", cfg.CRIMINAL_CARD, cfg.DANGER, "Proved Criminal"),
        ("UNKNOWN", cfg.PANEL_ELEVATED, cfg.HIGHLIGHT, "Deduce Verdict?"),
    )
    portraits = view.home_preview_characters()
    card_w, card_h, gap = 196, 150, 24
    start_x = showcase.centerx - (card_w * 3 + gap * 2) // 2
    base_y = showcase.y + 20

    for idx, ((status_tag, card_bg, tag_color, caption), record) in enumerate(zip(preview_specs, portraits)):
        card = pygame.Rect(start_x + idx * (card_w + gap), base_y, card_w, card_h)
        draw_panel(view.screen, card, fill=card_bg, border=tag_color, border_width=2 if idx == 2 else 1, radius=12, shadow=False)

        portrait_size = 76
        portrait_rect = pygame.Rect(card.centerx - portrait_size // 2, card.y + 12, portrait_size, portrait_size)
        portrait = view.artwork.portrait(record.name, (portrait_size, portrait_size)) if record else None
        if portrait:
            view.screen.blit(portrait, portrait_rect)
        else:
            pygame.draw.rect(view.screen, cfg.BG, portrait_rect, border_radius=8)
            draw_centered_text(view.screen, view.heading, "?", portrait_rect.center, tag_color)

        char_name = record.name if record else f"Suspect {idx + 1}"
        draw_centered_text(view.screen, view.small, char_name, (card.centerx, card.y + 102), cfg.TEXT)

        tag_rect = pygame.Rect(card.x + 22, card.bottom - 30, card.width - 44, 22)
        pygame.draw.rect(view.screen, cfg.BG, tag_rect, border_radius=11)
        pygame.draw.rect(view.screen, tag_color, tag_rect, 1, border_radius=11)
        draw_centered_text(view.screen, view.tiny, caption, tag_rect.center, tag_color)

    stages = view.discover_stages()
    total_stages = len(stages)
    solved_count = sum(1 for entry in stages if entry.path in view.stage_records)
    progress_text = f"Stages Solved: {solved_count} / {total_stages}   |   3x3 / 4x4 / 5x5 Grids"
    draw_centered_text(view.screen, view.small, progress_text, (showcase.centerx, showcase.bottom - 18), cfg.MUTED)

    # Primary CTA buttons
    has_progress = view.has_active_session and not view.engine.solved
    play_label = "CONTINUE GAME" if has_progress else "PLAY"
    view.button("home_play", play_label, pygame.Rect(canvas.centerx - 185, 466, 370, 58), style="primary")

    current_caption = f"Current Case: {view.engine.title}"
    draw_centered_text(view.screen, view.small, current_caption, (canvas.centerx, 539), cfg.MUTED)

    view.button("home_stages", "SELECT STAGE", pygame.Rect(canvas.centerx - 185, 560, 370, 48), style="default")
    view.button("home_help_cta", "HOW TO PLAY", pygame.Rect(canvas.centerx - 185, 622, 178, 46), style="default")
    view.button("home_quit", "QUIT", pygame.Rect(canvas.centerx + 7, 622, 178, 46), style="danger")

    # Footer
    footer_y = canvas.bottom - 42
    pygame.draw.line(view.screen, cfg.BORDER_SUBTLE, (40, footer_y - 18), (canvas.right - 40, footer_y - 18), 1)
    view.label(f"Analyzer: {view.analyzer_name}", (42, footer_y), cfg.MUTED, view.small)
    hint_text = "Enter: Play   |   Esc: Quit"
    hint_w = view.small.size(hint_text)[0]
    view.label(hint_text, (canvas.right - 42 - hint_w, footer_y), cfg.MUTED, view.small)


def draw_stage_select(view):
    """Categorized Stage Select grid with 3x3 / 4x4 / 5x5 tabs and best-time status."""
    view.hover_scope = "stage_select"
    canvas = main_canvas_rect()

    view.draw_backdrop((10, 16, 24, 155))

    # Header
    view.button("stage_back", "Back", pygame.Rect(36, 26, 114, 40), style="default")
    draw_centered_text(view.screen, view.heading, "SELECT STAGE", (canvas.centerx, 46), cfg.ACCENT)

    all_stages = view.discover_stages()
    solved_count = sum(1 for entry in all_stages if entry.path in view.stage_records)
    summary_pill = pygame.Rect(canvas.right - 224, 28, 188, 36)
    pygame.draw.rect(view.screen, cfg.PANEL, summary_pill, border_radius=18)
    pygame.draw.rect(view.screen, cfg.BORDER_SUBTLE, summary_pill, 1, border_radius=18)
    draw_centered_text(
        view.screen,
        view.small,
        f"Solved {solved_count} / {len(all_stages)}",
        summary_pill.center,
        cfg.ACCENT,
    )

    # Filter Tabs: All / 3x3 / 4x4 / 5x5
    tabs = (
        ("all", f"All ({len(all_stages)})"),
        (3, f"3x3 ({sum(1 for s in all_stages if s.size == 3)})"),
        (4, f"4x4 ({sum(1 for s in all_stages if s.size == 4)})"),
        (5, f"5x5 ({sum(1 for s in all_stages if s.size == 5)})"),
    )
    tab_w, tab_h, tab_gap = 132, 36, 14
    tabs_start_x = canvas.centerx - (len(tabs) * tab_w + (len(tabs) - 1) * tab_gap) // 2
    for i, (filter_key, label) in enumerate(tabs):
        tab_rect = pygame.Rect(tabs_start_x + i * (tab_w + tab_gap), 94, tab_w, tab_h)
        active = view.stage_filter == filter_key
        view.button(
            f"stage_filter_{filter_key}",
            label,
            tab_rect,
            focused=active,
            style="primary" if active else "default",
        )

    filtered = [s for s in all_stages if view.stage_filter == "all" or s.size == view.stage_filter]

    viewport = pygame.Rect(58, 150, canvas.width - 116, 616)
    cols = 3
    card_gap_x, card_gap_y = 20, 18
    card_w = (viewport.width - card_gap_x * (cols - 1)) // cols
    card_h = 132
    rows = max(1, (len(filtered) + cols - 1) // cols)
    total_h = rows * card_h + max(0, rows - 1) * card_gap_y
    view.stage_select_max_scroll = max(0, total_h - viewport.height)
    view.stage_select_scroll = max(0, min(view.stage_select_max_scroll, view.stage_select_scroll))
    view.stage_select_hits = []

    old_clip = view.screen.get_clip()
    view.screen.set_clip(viewport)
    size_colors = {3: cfg.ACCENT, 4: cfg.HIGHLIGHT, 5: cfg.DANGER}

    for idx, entry in enumerate(filtered):
        row, col = divmod(idx, cols)
        rect = pygame.Rect(
            viewport.x + col * (card_w + card_gap_x),
            viewport.y + row * (card_h + card_gap_y) - view.stage_select_scroll,
            card_w,
            card_h,
        )
        if not rect.colliderect(viewport):
            continue
        is_current = view.current_path == entry.path
        record = view.stage_records.get(entry.path)
        amount = view.hover(f"stage-card-{entry.path}", rect, enabled=True, focused=is_current)
        drawn = rect.move(0, -round(cfg.HOVER_LIFT * amount))

        fill = cfg.INNOCENT_CARD if record else cfg.PANEL
        fill = tuple(round(a + (b - a) * amount * 0.18) for a, b in zip(fill, cfg.ACCENT))
        border = cfg.ACCENT if (amount > 0.1 or is_current) else (cfg.ACCENT if record else cfg.BORDER_SUBTLE)
        draw_panel(view.screen, drawn, fill=fill, border=border, border_width=2 if (is_current or amount > 0.1) else 1, radius=12, shadow=False)

        badge_color = size_colors.get(entry.size, cfg.ACCENT)
        stage_pill = pygame.Rect(drawn.x + 14, drawn.y + 12, 82, 22)
        pygame.draw.rect(view.screen, cfg.BG, stage_pill, border_radius=11)
        draw_centered_text(view.screen, view.tiny, f"STAGE {entry.index:02d}", stage_pill.center, cfg.TEXT)

        size_pill = pygame.Rect(stage_pill.right + 8, drawn.y + 12, 44, 22)
        pygame.draw.rect(view.screen, cfg.BG, size_pill, border_radius=11)
        pygame.draw.rect(view.screen, badge_color, size_pill, 1, border_radius=11)
        draw_centered_text(view.screen, view.tiny, f"{entry.size}x{entry.size}", size_pill.center, badge_color)

        if record:
            status_pill = pygame.Rect(drawn.right - 78, drawn.y + 12, 64, 22)
            pygame.draw.rect(view.screen, cfg.BG, status_pill, border_radius=11)
            pygame.draw.rect(view.screen, cfg.ACCENT, status_pill, 1, border_radius=11)
            draw_centered_text(view.screen, view.tiny, "SOLVED", status_pill.center, cfg.ACCENT)
        elif is_current:
            status_pill = pygame.Rect(drawn.right - 84, drawn.y + 12, 70, 22)
            pygame.draw.rect(view.screen, cfg.BG, status_pill, border_radius=11)
            pygame.draw.rect(view.screen, cfg.HIGHLIGHT, status_pill, 1, border_radius=11)
            draw_centered_text(view.screen, view.tiny, "CURRENT", status_pill.center, cfg.HIGHLIGHT)

        title_rect = pygame.Rect(drawn.x + 14, drawn.y + 44, drawn.width - 28, 46)
        view.wrapped(entry.short_title, title_rect, cfg.TEXT, view.font)

        if record:
            meta = f"Best Time: {format_duration(record.best_time_ms)}"
            meta_color = cfg.ACCENT
        elif is_current:
            meta = "Current stage  |  Click to play"
            meta_color = cfg.HIGHLIGHT
        else:
            meta = "Click to start investigation"
            meta_color = cfg.MUTED
        view.label(meta, (drawn.x + 14, drawn.bottom - 26), meta_color, view.tiny)
        view.stage_select_hits.append((rect.clip(viewport), entry.path))

    if not filtered:
        draw_centered_text(view.screen, view.font, "No stages found for this filter.", viewport.center, cfg.MUTED)

    view.screen.set_clip(old_clip)

    if view.stage_select_max_scroll > 0:
        track = pygame.Rect(viewport.right + 10, viewport.y, 6, viewport.height)
        pygame.draw.rect(view.screen, cfg.BG, track, border_radius=3)
        thumb_h = max(36, round(viewport.height * viewport.height / total_h))
        thumb_y = track.y + round((track.height - thumb_h) * view.stage_select_scroll / view.stage_select_max_scroll)
        pygame.draw.rect(view.screen, cfg.ACCENT, (track.x, thumb_y, track.width, thumb_h), border_radius=3)

    draw_centered_text(
        view.screen,
        view.small,
        "Click a stage card to play   |   Scroll to browse   |   Esc to go back",
        (canvas.centerx, canvas.bottom - 36),
        cfg.MUTED,
    )


def draw_pause_overlay(view):
    """Pause menu overlay on top of active gameplay."""
    view.hover_scope = "pause"
    view.draw_veil((8, 12, 18, 190))

    canvas = view.screen.get_rect()
    rect = pygame.Rect(0, 0, 446, 478)
    rect.center = canvas.center
    draw_panel(view.screen, rect, fill=cfg.PANEL, border=cfg.ACCENT, border_width=2, radius=16)

    draw_centered_text(view.screen, view.heading, "PAUSED", (rect.centerx, rect.y + 42), cfg.ACCENT)
    draw_centered_text(view.screen, view.small, view.engine.title, (rect.centerx, rect.y + 76), cfg.TEXT)

    state = view.engine.public_state()
    meta = f"Proved {len(state.verdicts)}/{len(state.characters)}   |   Time {format_duration(view.stage_elapsed_ms)}"
    draw_centered_text(view.screen, view.tiny, meta, (rect.centerx, rect.y + 102), cfg.MUTED)

    pygame.draw.line(view.screen, cfg.BORDER_SUBTLE, (rect.x + 36, rect.y + 122), (rect.right - 36, rect.y + 122), 1)

    bx, bw = rect.x + 53, rect.width - 106
    view.button("pause_resume", "Resume", pygame.Rect(bx, rect.y + 140, bw, 48), style="primary")
    view.button("pause_restart", "Restart Stage", pygame.Rect(bx, rect.y + 200, bw, 44), style="default")
    view.button("pause_stages", "Select Stage", pygame.Rect(bx, rect.y + 256, bw, 44), style="default")

    half_w = (bw - 12) // 2
    music_label = "Music: On" if view.music.enabled else "Music"
    view.button("pause_music", music_label, pygame.Rect(bx, rect.y + 312, half_w, 42), style="default")
    view.button("pause_help", "How to Play", pygame.Rect(bx + half_w + 12, rect.y + 312, half_w, 42), style="default")

    view.button("pause_home", "Main Menu", pygame.Rect(bx, rect.y + 366, half_w, 42), style="default")
    view.button("pause_quit", "Quit", pygame.Rect(bx + half_w + 12, rect.y + 366, half_w, 42), style="danger")

    draw_centered_text(view.screen, view.tiny, "Press Esc to resume", (rect.centerx, rect.bottom - 22), cfg.MUTED)


def draw_cleared_overlay(view):
    """Stage Cleared overlay (star-free, focused on deduction stats and Next Stage navigation)."""
    view.hover_scope = "cleared"
    tick = pygame.time.get_ticks()
    canvas = view.screen.get_rect()

    view.draw_veil((8, 16, 22, 192))

    draw_cleared_particles(view.screen, view.cleared_particles, view.hover_delta, canvas, tick)

    rect = pygame.Rect(0, 0, 610, 466)
    rect.center = canvas.center
    draw_panel(view.screen, rect, fill=cfg.PANEL, border=cfg.ACCENT, border_width=2, radius=18)

    # Crisp checkmark emblem
    emblem_center = (rect.centerx, rect.y + 54)
    pygame.draw.circle(view.screen, cfg.INNOCENT_CARD, emblem_center, 30)
    pygame.draw.circle(view.screen, cfg.ACCENT, emblem_center, 30, 3)
    check_pts = (
        (emblem_center[0] - 12, emblem_center[1] + 1),
        (emblem_center[0] - 3, emblem_center[1] + 10),
        (emblem_center[0] + 14, emblem_center[1] - 9),
    )
    pygame.draw.lines(view.screen, cfg.ACCENT, False, check_pts, 4)

    next_path = view.next_stage_path()
    stages = view.discover_stages()
    all_solved = bool(stages) and all(entry.path in view.stage_records for entry in stages)
    banner_title = "ALL STAGES CLEARED" if (all_solved and next_path is None) else "STAGE CLEARED"
    draw_centered_text(view.screen, view.heading, banner_title, (rect.centerx, rect.y + 110), cfg.ACCENT)
    draw_centered_text(view.screen, view.small, view.engine.title, (rect.centerx, rect.y + 144), cfg.TEXT)

    # 3-metric stats row: TIME | MOVES | HINTS
    hint_val = f"{view.hints_used}" if not view.auto_used else f"{view.hints_used} (Auto)"
    stats = (
        ("TIME", format_duration(view.stage_elapsed_ms), cfg.TEXT),
        ("MOVES", str(view.moves), cfg.ACCENT),
        ("HINTS", hint_val, cfg.HIGHLIGHT if (view.hints_used or view.auto_used) else cfg.TEXT),
    )
    box_gap = 14
    box_w = (rect.width - 64 - box_gap * 2) // 3
    box_h = 76
    box_y = rect.y + 174
    for i, (label, val, val_color) in enumerate(stats):
        box = pygame.Rect(rect.x + 32 + i * (box_w + box_gap), box_y, box_w, box_h)
        draw_panel(view.screen, box, fill=cfg.PANEL_ELEVATED, border=cfg.BORDER_SUBTLE, border_width=1, radius=10, shadow=False)
        draw_centered_text(view.screen, view.tiny, label, (box.centerx, box.y + 22), cfg.MUTED)
        draw_centered_text(view.screen, view.font, val, (box.centerx, box.y + 50), val_color)

    # Progress & best time summary
    solved_count = sum(1 for entry in stages if entry.path in view.stage_records)
    record = view.stage_records.get(view.current_path)
    best_str = f"Best Time: {format_duration(record.best_time_ms)}" if record else ""
    summary = f"Stages Solved: {solved_count} / {len(stages)}" + (f"   |   {best_str}" if best_str else "")
    draw_centered_text(view.screen, view.small, summary, (rect.centerx, rect.y + 276), cfg.MUTED)

    pygame.draw.line(view.screen, cfg.BORDER_SUBTLE, (rect.x + 32, rect.y + 300), (rect.right - 32, rect.y + 300), 1)

    # Primary action row: Replay | Next Stage | View Board
    row1_y = rect.y + 320
    view.button("cleared_replay", "Replay", pygame.Rect(rect.x + 32, row1_y, 148, 48), style="default")
    next_label = "Next Stage" if next_path is not None else "All Stages"
    view.button("cleared_next", next_label, pygame.Rect(rect.x + 194, row1_y, 222, 48), style="primary")
    view.button("cleared_board", "View Board", pygame.Rect(rect.x + 430, row1_y, 148, 48), style="default")

    # Secondary navigation row
    row2_y = rect.y + 382
    view.button("cleared_stages", "Stage Select", pygame.Rect(rect.x + 32, row2_y, 266, 40), style="default")
    view.button("cleared_home", "Main Menu", pygame.Rect(rect.x + 312, row2_y, 266, 40), style="default")

    draw_centered_text(view.screen, view.tiny, "Enter: Next Stage   |   Esc: View Board", (rect.centerx, rect.bottom - 18), cfg.MUTED)
