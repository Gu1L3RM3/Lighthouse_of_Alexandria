import pygame

_ROW_CACHE: dict[tuple, pygame.Surface] = {}
_ROW_CACHE_LIMIT = 256


def get_prompt_style(label: str) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    normalized = label.upper()
    if normalized == "A":
        return (42, 122, 66), (122, 224, 150), (245, 252, 245)
    if normalized == "B":
        return (128, 42, 42), (236, 126, 126), (255, 244, 244)
    if normalized == "X":
        return (42, 76, 128), (132, 178, 245), (244, 249, 255)
    if normalized == "Y":
        return (118, 102, 30), (245, 222, 118), (255, 252, 236)
    if normalized == "START":
        return (62, 56, 40), (232, 208, 132), (250, 244, 220)
    if normalized == "CROSS":
        return (42, 76, 128), (132, 178, 245), (244, 249, 255)
    if normalized == "CIRCLE":
        return (128, 42, 42), (236, 126, 126), (255, 244, 244)
    if normalized == "SQUARE":
        return (166, 92, 30), (255, 202, 118), (255, 248, 236)
    if normalized == "TRIANGLE":
        return (42, 122, 66), (122, 224, 150), (245, 252, 245)
    if normalized == "OPTIONS":
        return (62, 56, 40), (232, 208, 132), (250, 244, 220)
    if normalized in {"LB", "RB", "L1", "R1"}:
        return (68, 64, 54), (220, 205, 150), (250, 244, 220)
    return (24, 28, 36), (235, 221, 160), (245, 230, 170)


def draw_prompt_chip(
    surface: pygame.Surface,
    font: pygame.font.Font,
    label: str,
    rect: pygame.Rect,
):
    bg, border, text_color = get_prompt_style(label)
    pygame.draw.rect(surface, bg, rect, border_radius=8)
    pygame.draw.rect(surface, border, rect, width=2, border_radius=8)
    text_surf = font.render(label, True, text_color)
    surface.blit(text_surf, text_surf.get_rect(center=rect.center))


def draw_prompt_hint_row(
    surface: pygame.Surface,
    chip_font: pygame.font.Font,
    text_font: pygame.font.Font,
    items: list[tuple[str, str]],
    anchor: tuple[int, int],
    align: str = "center",
    gap: int = 14,
):
    normalized_items = tuple((str(button_label), str(description)) for button_label, description in items)
    cache_key = (
        id(chip_font),
        id(text_font),
        normalized_items,
        int(gap),
    )
    row_surface = _ROW_CACHE.get(cache_key)
    if row_surface is None:
        prepared: list[tuple[str, object]] = []
        total_width = 0
        max_height = 0

        for index, (button_label, description) in enumerate(normalized_items):
            chip_w = max(34, chip_font.size(button_label)[0] + 18)
            chip_h = max(24, chip_font.get_height() + 10)
            text_surf = text_font.render(description, True, (176, 165, 136))
            prepared.append(("chip", (button_label, chip_w, chip_h)))
            prepared.append(("text", text_surf))
            total_width += chip_w + 8 + text_surf.get_width()
            max_height = max(max_height, chip_h, text_surf.get_height())
            if index < len(normalized_items) - 1:
                total_width += gap

        row_surface = pygame.Surface((max(1, total_width), max(1, max_height)), pygame.SRCALPHA)
        rx = 0
        for idx, (kind, payload) in enumerate(prepared):
            if kind == "chip":
                button_label, chip_w, chip_h = payload
                rect = pygame.Rect(rx, (max_height - chip_h) // 2, chip_w, chip_h)
                draw_prompt_chip(row_surface, chip_font, button_label, rect)
                rx += chip_w + 8
            else:
                text_surf = payload
                row_surface.blit(text_surf, (rx, (max_height - text_surf.get_height()) // 2))
                rx += text_surf.get_width()
                if idx < len(prepared) - 1:
                    rx += gap

        if len(_ROW_CACHE) >= _ROW_CACHE_LIMIT:
            _ROW_CACHE.clear()
        _ROW_CACHE[cache_key] = row_surface

    total_width = row_surface.get_width()
    max_height = row_surface.get_height()
    if align == "center":
        x = anchor[0] - total_width // 2
    elif align == "right":
        x = anchor[0] - total_width
    else:
        x = anchor[0]
    y = anchor[1] - max_height // 2
    surface.blit(row_surface, (x, y))
