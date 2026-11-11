"""Portrait card rendering and time-based reveal animation."""
import pygame
from griductive.ui import config as cfg


def reveal_progress(started, now):
    if started is None or cfg.REVEAL_DURATION_MS <= 0:
        return 1.0
    return max(0.0, min(1.0, (now-started)/cfg.REVEAL_DURATION_MS))


def draw_character(view, char, rect, status, clue, progress, size):
    """Draw public clue only after the portrait has begun moving into its header."""
    old_clip = view.screen.get_clip()
    view.screen.set_clip(old_clip.clip(rect.inflate(-8, -6)))
    padding = cfg.CARD_PADDING
    compact = size == 5
    name_font = view.tiny if compact else view.small
    role_font = view.tiny
    record = view.artwork.catalog.get(char.name.casefold())
    origin = record.origin if record else char.origin
    large = min(cfg.PORTRAIT_SIZE[size], rect.height-cfg.PORTRAIT_TOP-8,
                rect.width-2*padding)
    small = cfg.SOLVED_PORTRAIT_SIZE[size]
    eased = progress*progress*(3-2*progress) if status else 0.0
    side = round(large+(small-large)*eased)
    # Unresolved portrait is below the name; solved portrait moves to top-left.
    start_top = rect.y+cfg.PORTRAIT_TOP+(rect.height-cfg.PORTRAIT_TOP-large)//2
    top = round(start_top+(rect.y+7-start_top)*eased)
    start_left = rect.centerx-large/2
    left = round(start_left+(rect.x+padding-start_left)*eased)
    image_rect = pygame.Rect(left, top, side, side)
    portrait = view.artwork.portrait(char.name, (side, side))
    if portrait:
        view.screen.blit(portrait, image_rect)
    else:
        pygame.draw.rect(view.screen, cfg.BG, image_rect, border_radius=5)
        view.label(char.name[0], (image_rect.x+4, image_rect.y+3), cfg.ACCENT, name_font)
    name_x = round(rect.x+padding+(small+6)*eased)
    name_width = rect.right-name_x-padding
    title = f'{char.cell} {char.name}'
    if name_font.size(title)[0] > name_width:
        from griductive.ui.assets import ui_font
        name_font = ui_font(max(9, round(name_font.get_height()*name_width/name_font.size(title)[0]) - 2))
    view.wrapped(title, pygame.Rect(name_x, rect.y+5, name_width, 19), font=name_font)
    view.wrapped(origin, pygame.Rect(name_x, rect.y+21, name_width, 16), cfg.MUTED, role_font)
    if status and clue and progress > .65:
        opacity = min(1.0, (progress-.65)/.35)
        base = cfg.CRIMINAL_CARD if status.value == 'CRIMINAL' else cfg.INNOCENT_CARD
        color = tuple(round(a+(b-a)*opacity) for a,b in zip(base,cfg.TEXT))
        top_clue = rect.y+max(39, small+12)
        body = pygame.Rect(rect.x+padding, top_clue, rect.width-2*padding,
                           rect.bottom-cfg.STATUS_HEIGHT-top_clue-2)
        font = view.tiny if size >= 4 else view.small
        lines = view.lines(view.clue_text(clue), body.width, font)
        capacity = max(1, body.height//font.get_linesize())
        visible = lines[:capacity]
        if len(lines) > capacity:
            text = visible[-1]
            while text and font.size(text+'...')[0] > body.width:
                text = text[:-1]
            visible[-1] = text+'...'
        for i, line in enumerate(visible):
            view.wrapped(line, pygame.Rect(body.x, body.y+i*font.get_linesize(), body.width, font.get_linesize()), color, font)
    if status:
        view.label(status.value, (rect.x+padding, rect.bottom-cfg.STATUS_HEIGHT), cfg.ACCENT, view.tiny)
    view.screen.set_clip(old_clip)
