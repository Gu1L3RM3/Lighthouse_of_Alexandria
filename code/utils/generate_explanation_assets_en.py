from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT_DIR = Path(__file__).resolve().parents[2]
ASSETS_DIR = ROOT_DIR / "assets"
OUT_ROOT = ASSETS_DIR / "images" / "explanations"
FONT_REGULAR = str(Path("C:/Windows/Fonts/arial.ttf"))
FONT_BOLD = str(Path("C:/Windows/Fonts/arialbd.ttf"))

W = 1280
H = 720
BG = (233, 238, 247)
HEADER = (30, 51, 88)
HEADER_ALT = (16, 36, 54)
TEXT = (34, 41, 53)
BLUE = (48, 99, 183)
GREEN = (40, 142, 92)
ORANGE = (225, 97, 33)
OUTLINE = (46, 73, 116)
CARD_DARK = (19, 36, 51)
CARD_DARK_2 = (14, 27, 39)
ACCENT = (237, 222, 165)


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size=size)


def new_light_slide(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 92), fill=HEADER)
    draw.text((36, 18), title, fill="white", font=font(46))
    return img, draw


def new_dark_slide(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), (18, 61, 83))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((70, 88, 1210, 592), radius=0, fill=CARD_DARK_2, outline=None)
    draw.text((112, 138), title, fill=ACCENT, font=font(58, bold=True))
    draw.text((905, 638), "Lighthouse of Alexandria - Explanatory", fill=(191, 211, 226), font=font(14))
    return img, draw


def wrap(draw: ImageDraw.ImageDraw, text: str, ft, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if draw.textbbox((0, 0), trial, font=ft)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_paragraph(draw, text: str, xy: tuple[int, int], ft, fill, max_width: int, line_gap: int = 8):
    x, y = xy
    for line in wrap(draw, text, ft, max_width):
        draw.text((x, y), line, fill=fill, font=ft)
        box = draw.textbbox((x, y), line, font=ft)
        y = box[3] + line_gap
    return y


def compute_step_boxes_layout(
    draw,
    steps: list[str],
    body_top: int = 170,
    body_bottom: int = 655,
    box_width: int = 1000,
    font_size: int = 28,
    box_padding_x: int = 22,
    box_padding_y: int = 14,
    gap: int = 18,
):
    ft = font(font_size)
    x1 = (W - box_width) // 2
    x2 = x1 + box_width
    line_box = draw.textbbox((0, 0), "Ag", font=ft)
    line_h = line_box[3] - line_box[1]
    boxes = []
    total_h = 0

    for i, step in enumerate(steps, start=1):
        wrapped = wrap(draw, f"{i}) {step}", ft, box_width - (box_padding_x * 2))
        text_h = max(1, len(wrapped)) * line_h + max(0, len(wrapped) - 1) * 8
        box_h = max(54, text_h + (box_padding_y * 2))
        boxes.append({
            "index": i,
            "wrapped": wrapped,
            "box_h": box_h,
            "line_h": line_h,
        })
        total_h += box_h

    total_h += gap * max(0, len(boxes) - 1)
    start_y = body_top + max(0, (body_bottom - body_top - total_h) // 2)
    y = start_y

    for box in boxes:
        box["y1"] = y
        box["y2"] = y + box["box_h"]
        y += box["box_h"] + gap

    return {
        "x1": x1,
        "x2": x2,
        "box_width": box_width,
        "font": ft,
        "gap": gap,
        "box_padding_x": box_padding_x,
        "box_padding_y": box_padding_y,
        "boxes": boxes,
    }


def draw_step_boxes(
    draw,
    steps: list[str],
    start_y: int | None = None,
    body_top: int = 170,
    body_bottom: int = 655,
    box_width: int = 1000,
    font_size: int = 28,
    box_padding_x: int = 22,
    box_padding_y: int = 14,
    gap: int = 18,
    fill=(247, 249, 253),
    outline=(208, 217, 235),
    text_fill=TEXT,
):
    layout = compute_step_boxes_layout(
        draw,
        steps,
        body_top=start_y if start_y is not None else body_top,
        body_bottom=body_bottom,
        box_width=box_width,
        font_size=font_size,
        box_padding_x=box_padding_x,
        box_padding_y=box_padding_y,
        gap=gap,
    )
    for box in layout["boxes"]:
        draw.rounded_rectangle(
            (layout["x1"], box["y1"], layout["x2"], box["y2"]),
            radius=8,
            outline=outline,
            width=2,
            fill=fill,
        )
        block_h = len(box["wrapped"]) * box["line_h"] + max(0, len(box["wrapped"]) - 1) * 8
        text_y = box["y1"] + (box["box_h"] - block_h) / 2 - 2
        for line in box["wrapped"]:
            draw.text(
                (layout["x1"] + layout["box_padding_x"], text_y),
                line,
                fill=text_fill,
                font=layout["font"],
            )
            text_y += box["line_h"] + 8


def draw_ground(draw, x: int, y: int, scale: float = 1.0, color=(40, 40, 40)):
    draw.line((x, y, x, y - 46 * scale), fill=color, width=max(1, int(3 * scale)))
    draw.line((x - 24 * scale, y, x + 24 * scale, y), fill=color, width=max(1, int(3 * scale)))
    draw.line((x - 16 * scale, y + 10 * scale, x + 16 * scale, y + 10 * scale), fill=color, width=max(1, int(3 * scale)))
    draw.line((x - 8 * scale, y + 20 * scale, x + 8 * scale, y + 20 * scale), fill=color, width=max(1, int(3 * scale)))


def draw_resistor(draw, x1: int, y1: int, x2: int, label: str):
    box = (x1, y1 - 16, x2, y1 + 16)
    draw.rounded_rectangle(box, radius=4, outline=ORANGE, width=3, fill=(245, 247, 250))
    draw.text((x1 + 18, y1 - 11), label, fill=ORANGE, font=font(18))


def draw_resistor_centered(draw, cx: int, cy: int, w: int, h: int, label: str, text_size: int = 22):
    x1 = cx - w // 2
    y1 = cy - h // 2
    x2 = cx + w // 2
    y2 = cy + h // 2
    draw.rounded_rectangle((x1, y1, x2, y2), radius=4, outline=ORANGE, width=3, fill=(245, 247, 250))
    bbox = draw.textbbox((0, 0), label, font=font(text_size))
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw / 2, cy - th / 2 - 2), label, fill=ORANGE, font=font(text_size))


def draw_arrow(draw, start: tuple[int, int], end: tuple[int, int], color=BLUE, width: int = 3):
    draw.line((*start, *end), fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    head = 10
    left = (end[0] - head * math.cos(angle - 0.4), end[1] - head * math.sin(angle - 0.4))
    right = (end[0] - head * math.cos(angle + 0.4), end[1] - head * math.sin(angle + 0.4))
    draw.polygon([end, left, right], fill=color)


def ensure_dir(path: str):
    (OUT_ROOT / path).mkdir(parents=True, exist_ok=True)


def save(img: Image.Image, rel: str):
    target = OUT_ROOT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    img.save(target)


def gen_ohm_law():
    folder = "ohm_law_en"
    ensure_dir(folder)

    img, draw = new_light_slide("Ohm's Law: Core Idea")
    draw_paragraph(draw, "Voltage (V) pushes charges. Current (I) is the flow of charges. Resistance (R) opposes that flow.", (44, 135), font(38), TEXT, 760, 10)
    cx, cy, r = 1000, 400, 178
    draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=HEADER, width=6)
    draw.line((cx-r, cy, cx+r, cy), fill=HEADER, width=6)
    draw.line((cx, cy-r, cx, cy+r), fill=HEADER, width=6)
    draw.text((cx-54, cy-95), "V", fill=ORANGE, font=font(60))
    draw.text((cx-94, cy+30), "R", fill=GREEN, font=font(60))
    draw.text((cx+64, cy+30), "I", fill=BLUE, font=font(60))
    save(img, f"{folder}/01_visao_geral.png")

    img, draw = new_light_slide("Ohm's Law Equations")
    draw.rounded_rectangle((372, 132, 1160, 440), radius=14, outline=OUTLINE, width=3, fill=(247, 249, 252))
    eqs = [("V = R x I", ORANGE, 48), ("I = V / R", TEXT, 42), ("R = V / I", GREEN, 42)]
    ys = [200, 272, 342]
    for (text, color, size), y in zip(eqs, ys):
        bbox = draw.textbbox((0, 0), text, font=font(size))
        tw = bbox[2] - bbox[0]
        draw.text((766 - tw / 2, y), text, fill=color, font=font(size))
    save(img, f"{folder}/02_equacoes_ohm.png")

    img, draw = new_light_slide("Basic Circuit for V = R x I")
    y = 310
    left_x = 80
    right_x = 1040
    bottom_y = 460
    draw.line((left_x, y, 272, y), fill=(20, 20, 24), width=6)
    draw.line((left_x, y, left_x, bottom_y), fill=(20, 20, 24), width=6)
    draw.line((left_x, bottom_y, right_x, bottom_y), fill=(20, 20, 24), width=6)
    draw.line((right_x, y, right_x, bottom_y), fill=(20, 20, 24), width=6)
    draw.line((272, y, 320, y), fill=(20, 20, 24), width=6)
    draw.line((332, y - 18, 332, y + 18), fill=(20, 20, 24), width=5)
    draw.line((350, y - 10, 350, y + 10), fill=(20, 20, 24), width=3)
    draw.text((290, 252), "Voltage source", fill=(91, 108, 134), font=font(16))
    draw.line((350, y, 560, y), fill=(20, 20, 24), width=6)
    draw_resistor(draw, 560, y, 690, "R")
    draw.line((690, y, 720, y), fill=(20, 20, 24), width=6)
    draw_arrow(draw, (720, y), (900, y), color=BLUE, width=5)
    draw.line((900, y, right_x, y), fill=(20, 20, 24), width=6)
    draw.text((876, y - 36), "I", fill=BLUE, font=font(20, bold=True))
    draw.text((120, 580), "With fixed R, increasing V increases I. With fixed V, increasing R reduces I.", fill=(77, 86, 101), font=font(24))
    save(img, f"{folder}/03_circuito_basico.png")

    img, draw = new_light_slide("Two Resistors in Series")
    y = 250
    left_x = 120
    right_x = 1080
    bottom_y = 420
    draw.text((208, 190), "Voltage source", fill=(91, 108, 134), font=font(16))
    draw.line((left_x, y, 220, y), fill=(20, 20, 24), width=6)
    draw.line((220, y-20, 220, y+20), fill=(20, 20, 24), width=5)
    draw.line((248, y-28, 248, y+28), fill=(20, 20, 24), width=7)
    draw.line((248, y, 360, y), fill=(20, 20, 24), width=6)
    draw_resistor_centered(draw, 440, y, 160, 52, "R1", 26)
    draw.line((520, y, 600, y), fill=(20, 20, 24), width=6)
    draw_resistor_centered(draw, 680, y, 160, 52, "R2", 26)
    draw.line((760, y, 840, y), fill=(20, 20, 24), width=6)
    draw_arrow(draw, (840, y), (940, y), color=BLUE, width=5)
    draw.text((912, 210), "I", fill=BLUE, font=font(24, bold=True))
    draw.line((940, y, right_x, y), fill=(20, 20, 24), width=6)
    draw.line((left_x, y, left_x, bottom_y), fill=(20, 20, 24), width=6)
    draw.line((right_x, y, right_x, bottom_y), fill=(20, 20, 24), width=6)
    draw.line((left_x, bottom_y, right_x, bottom_y), fill=(20, 20, 24), width=6)
    bbox = draw.textbbox((0, 0), "Req = R1 + R2  (same current through both)", font=font(28))
    tw = bbox[2] - bbox[0]
    draw.text((640 - tw / 2, 520), "Req = R1 + R2  (same current through both)", fill=(70, 83, 115), font=font(28))
    bbox2 = draw.textbbox((0, 0), "Then use V = Req x I to find the total current.", font=font(20))
    tw2 = bbox2[2] - bbox2[0]
    draw.text((640 - tw2 / 2, 560), "Then use V = Req x I to find the total current.", fill=(103, 112, 127), font=font(20))
    save(img, f"{folder}/06_serie_equivalente.png")

    img, draw = new_light_slide("How to Solve Stage 3 Panels")
    draw_step_boxes(draw, [
        "Read the target: voltage, current, or resistance.",
        "Identify the known values in the circuit.",
        "Choose the correct form: V=RI, I=V/R, or R=V/I.",
        "Calculate and compare with the panel value.",
        "Adjust the resistors and validate again.",
    ], 198, 655)
    save(img, f"{folder}/08_passos_paineis.png")

    img, draw = new_light_slide("GND: Circuit Reference")
    draw.rounded_rectangle((130, 125, 1070, 255), radius=14, outline=OUTLINE, width=3, fill=(242, 245, 250))
    draw_paragraph(draw, "GND means Ground, the 0 V reference point. In the circuit, GND defines where the simulator measures voltage. Without GND, the circuit may not solve correctly.", (168, 150), font(28), (63, 74, 100), 850, 6)
    draw.line((200, 480, 290, 480), fill=(42, 42, 42), width=4)
    draw.line((290, 420, 290, 540), fill=(42, 42, 42), width=4)
    draw.line((312, 430, 312, 530), fill=(42, 42, 42), width=3)
    draw.text((240, 420), "Voltage source", fill=(91, 108, 134), font=font(16))
    draw.line((312, 480, 410, 480), fill=(42, 42, 42), width=4)
    draw_resistor(draw, 410, 480, 540, "R")
    draw.line((540, 480, 640, 480), fill=(42, 42, 42), width=4)
    draw_ground(draw, 640, 500, 1.0)
    draw.text((598, 578), "0 V reference", fill=(91, 108, 134), font=font(16))
    draw_ground(draw, 1020, 470, 1.15)
    draw.text((930, 520), "Ground symbol", fill=ORANGE, font=font(28))
    save(img, f"{folder}/09_gnd_referencia.png")


def gen_electric_power():
    folder = "electric_power_en"
    ensure_dir(folder)
    img, draw = new_light_slide("Electric Power in the Resistor")
    draw.rounded_rectangle((82, 144, 1198, 650), radius=24, outline=OUTLINE, width=4, fill=(246, 248, 252))
    draw.text((122, 200), "Concept: energy transferred per second.", fill=(43, 54, 71), font=font(30))
    draw.text((122, 266), "Base equation:  P = V x I", fill=ORANGE, font=font(64, bold=True))
    draw.text((122, 350), "Unit: watt (W).", fill=BLUE, font=font(36))
    draw.text((122, 410), "Use this form when V and I are known.", fill=TEXT, font=font(32))
    save(img, f"{folder}/01_potencia_base.png")

    img, draw = new_light_slide("Power Equations with Resistance")
    draw.rounded_rectangle((82, 144, 1198, 650), radius=24, outline=OUTLINE, width=4, fill=(246, 248, 252))
    draw.text((122, 200), "Starting from V = R x I:", fill=(43, 54, 71), font=font(28))
    draw.text((122, 264), "P = I^2 x R", fill=GREEN, font=font(44, bold=True))
    draw.text((122, 324), "P = V^2 / R", fill=BLUE, font=font(44, bold=True))
    draw.text((122, 402), "These formulas use R directly.", fill=TEXT, font=font(28))
    save(img, f"{folder}/02_potencia_com_resistencia.png")

    img, draw = new_light_slide("Quick Resistor Example")
    draw.rounded_rectangle((82, 144, 1198, 650), radius=24, outline=OUTLINE, width=4, fill=(246, 248, 252))
    draw.text((122, 200), "Given: R = 6 ohms, V = 12 V", fill=(43, 54, 71), font=font(26))
    draw.text((122, 254), "I = V/R = 12/6 = 2 A", fill=BLUE, font=font(34, bold=True))
    draw.text((122, 312), "P = I^2 x R = 2^2 x 6 = 24 W", fill=GREEN, font=font(34, bold=True))
    draw.text((122, 370), "Check: P = V^2/R = 12^2/6 = 24 W", fill=ORANGE, font=font(32, bold=True))
    save(img, f"{folder}/03_exemplo_potencia_resistor.png")


def gen_resistor_assoc():
    folder = "resistor_assoc_en"
    ensure_dir(folder)
    img, draw = new_light_slide("Resistor Networks: Overview")
    draw_paragraph(draw, "In the next stage you will combine resistors in series, parallel, and mixed arrangements.", (60, 145), font(34), TEXT, 1100, 8)
    draw.text((60, 256), "Goal: find the equivalent resistance and then apply Ohm's Law.", fill=HEADER, font=font(34))
    draw.rounded_rectangle((80, 342, 1188, 648), radius=18, outline=(190, 202, 228), width=3, fill=(248, 249, 252))
    draw.text((128, 396), "Series: same current through all resistors", fill=TEXT, font=font(28))
    draw.text((128, 472), "Parallel: same voltage across all branches", fill=TEXT, font=font(28))
    draw.text((128, 548), "Mixed: solve by blocks (series/parallel)", fill=TEXT, font=font(28))
    save(img, f"{folder}/01_visao_geral.png")

    img, draw = new_light_slide("Resistors in Series")
    y = 314
    draw.line((140, y, 240, y), fill=(42, 42, 42), width=4)
    draw.line((240, y-36, 240, y+36), fill=(42, 42, 42), width=4)
    draw.line((260, y-28, 260, y+28), fill=(42, 42, 42), width=3)
    draw.text((148, 210), "V", fill=(90, 110, 138), font=font(22))
    draw.line((260, y, 400, y), fill=(42, 42, 42), width=4)
    draw_resistor(draw, 400, y, 520, "R1")
    draw.line((520, y, 580, y), fill=(42, 42, 42), width=4)
    draw_resistor(draw, 580, y, 700, "R2")
    draw.line((700, y, 760, y), fill=(42, 42, 42), width=4)
    draw_resistor(draw, 760, y, 880, "R3")
    draw.line((880, y, 1000, y), fill=(42, 42, 42), width=4)
    draw.text((382, 470), "Formula: Req = R1 + R2 + R3", fill=GREEN, font=font(32))
    save(img, f"{folder}/02_serie_formula.png")

    img, draw = new_light_slide("Series Example")
    draw.rounded_rectangle((82, 144, 1198, 650), radius=24, outline=OUTLINE, width=4, fill=(246, 248, 252))
    draw.text((122, 206), "Let R1=10 ohms, R2=20 ohms, and R3=30 ohms:", fill=TEXT, font=font(28))
    draw.text((122, 302), "Req = 10 + 20 + 30 = 60 ohms", fill=ORANGE, font=font(40, bold=True))
    draw.text((122, 418), "With V=12V => I_total = V/Req = 12/60 = 0.2 A", fill=(70, 83, 115), font=font(28))
    save(img, f"{folder}/03_serie_exemplo.png")

    img, draw = new_light_slide("Resistors in Parallel")
    left_rail = 140
    right_rail = 1080
    branch_left = 340
    branch_right = 640
    for by, label in ((260, "R1"), (390, "R2"), (520, "R3")):
        draw.line((left_rail, by, branch_left, by), fill=(20, 20, 24), width=6)
        draw_resistor_centered(draw, (branch_left + branch_right) // 2, by, branch_right - branch_left, 76, label, 28)
        draw.line((branch_right, by, right_rail, by), fill=(20, 20, 24), width=6)
    draw.line((left_rail, 210, left_rail, 570), fill=(20, 20, 24), width=6)
    draw.line((right_rail, 210, right_rail, 570), fill=(20, 20, 24), width=6)
    bbox = draw.textbbox((0, 0), "Formula: 1/Req = 1/R1 + 1/R2 + 1/R3", font=font(28))
    tw = bbox[2] - bbox[0]
    draw.text((640 - tw / 2, 635), "Formula: 1/Req = 1/R1 + 1/R2 + 1/R3", fill=GREEN, font=font(28))
    save(img, f"{folder}/04_paralelo_formula.png")

    img, draw = new_light_slide("Parallel Example")
    draw.rounded_rectangle((82, 144, 1198, 650), radius=24, outline=OUTLINE, width=4, fill=(246, 248, 252))
    draw.text((122, 206), "Let R1=6 ohms and R2=3 ohms:", fill=TEXT, font=font(28))
    draw.text((122, 300), "1/Req = 1/6 + 1/3 = 1/6 + 2/6 = 3/6 = 1/2", fill=TEXT, font=font(28))
    draw.text((122, 380), "Req = 2 ohms", fill=ORANGE, font=font(40, bold=True))
    draw.text((122, 470), "In parallel, Req is smaller than the smallest resistor.", fill=(70, 83, 115), font=font(26))
    save(img, f"{folder}/05_paralelo_exemplo.png")

    img, draw = new_light_slide("Mixed Circuit (Series + Parallel)")
    y = 360
    draw.line((120, y, 360, y), fill=(20, 20, 24), width=6)
    draw_resistor_centered(draw, 440, y, 160, 52, "R1", 26)
    draw.line((520, y, 620, y), fill=(20, 20, 24), width=6)
    left_box = 620
    right_box = 980
    top = 250
    bottom = 470
    draw.line((left_box, top, right_box, top), fill=(20, 20, 24), width=6)
    draw.line((left_box, bottom, right_box, bottom), fill=(20, 20, 24), width=6)
    draw.line((left_box, top, left_box, bottom), fill=(20, 20, 24), width=6)
    draw.line((right_box, top, right_box, bottom), fill=(20, 20, 24), width=6)
    draw_resistor_centered(draw, 800, top, 160, 52, "R2", 26)
    draw_resistor_centered(draw, 800, bottom, 160, 52, "R3", 26)
    draw.line((980, y, 1120, y), fill=(20, 20, 24), width=6)
    bbox = draw.textbbox((0, 0), "Step 1: reduce the R2||R3 parallel block. Step 2: add it in series with R1.", font=font(24))
    tw = bbox[2] - bbox[0]
    draw.text((640 - tw / 2, 560), "Step 1: reduce the R2||R3 parallel block. Step 2: add it in series with R1.", fill=(70, 83, 115), font=font(24))
    save(img, f"{folder}/06_misto_blocos.png")

    img, draw = new_light_slide("Voltage Divider (Series)")
    rail_x = 240
    draw.line((rail_x, 220, rail_x, 540), fill=(20, 20, 24), width=6)
    draw_resistor_centered(draw, rail_x + 90, 290, 170, 54, "R1", 24)
    draw_resistor_centered(draw, rail_x + 90, 420, 170, 54, "R2", 24)
    mid_y = 355
    draw.line((rail_x + 175, mid_y, 620, mid_y), fill=BLUE, width=5)
    draw.text((640, 330), "Vout", fill=BLUE, font=font(26))
    bbox = draw.textbbox((0, 0), "Formula: Vout = Vin x (R2 / (R1 + R2))", font=font(28))
    tw = bbox[2] - bbox[0]
    draw.text((820 - tw / 2, 470), "Formula: Vout = Vin x (R2 / (R1 + R2))", fill=GREEN, font=font(28))
    save(img, f"{folder}/07_divisor_tensao.png")

    img, draw = new_light_slide("Do Not Forget GND")
    draw_paragraph(draw, "GND means Ground, the 0 V reference that keeps voltage measurements consistent. Without GND, the circuit may fail to solve or produce incorrect readings.", (90, 170), font(28), TEXT, 720, 6)
    draw_ground(draw, 1010, 470, 1.2)
    draw.text((930, 520), "Ground symbol", fill=ORANGE, font=font(28))
    save(img, f"{folder}/08_gnd_referencia.png")

    img, draw = new_light_slide("How to Tackle Stage 4 Panels")
    draw_step_boxes(draw, [
        "Identify whether the resistors are in series, parallel, or mixed.",
        "Reduce the blocks until you reach the equivalent resistance.",
        "Apply Ohm's Law with the values requested by the panel.",
        "Check units (ohm, V, A) before validating.",
        "Ensure the circuit has a GND connection.",
    ], 198, 655)
    save(img, f"{folder}/09_passos_paineis.png")


def gen_nodal_kirchhoff():
    folder = "nodal_kirchhoff_en"
    ensure_dir(folder)
    img, draw = new_light_slide("Node Method and Kirchhoff's Laws")
    draw_paragraph(draw, "In this stage you will use KCL, KVL, and the node method to calculate voltages and currents.", (36, 140), font(30), TEXT, 800, 8)
    draw_paragraph(draw, "Core idea: choose a reference node (GND), write the equations, and solve the system.", (36, 245), font(30), (70, 83, 115), 800, 8)
    save(img, f"{folder}/01_visao_geral.png")

    img, draw = new_light_slide("KCL: Kirchhoff's Current Law")
    cx, cy, r = 820, 280, 100
    draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=BLUE, width=4)
    draw.text((cx-25, cy-18), "NODE", fill=TEXT, font=font(28))
    draw.line((cx, cy-r-60, cx, cy-r), fill=BLUE, width=4)
    draw.line((cx-r-90, cy, cx-r, cy), fill=BLUE, width=4)
    draw.line((cx+r, cy, cx+r+90, cy), fill=BLUE, width=4)
    draw.text((cx+14, cy-r-84), "I1 in", fill=BLUE, font=font(16))
    draw.text((cx-r-138, cy-18), "I2 out", fill=BLUE, font=font(16))
    draw.text((cx+r+12, cy-18), "I3 out", fill=BLUE, font=font(16))
    draw.text((430, 520), "KCL: the sum of currents entering equals the sum of currents leaving.", fill=GREEN, font=font(28))
    save(img, f"{folder}/02_kcl_conceito.png")

    img, draw = new_light_slide("Node Equation (Example)")
    draw.text((140, 230), "For node Vx with branches to 10V, 0V, and 5V:", fill=TEXT, font=font(30))
    draw.text((140, 320), "(Vx - 10)/R1 + (Vx - 0)/R2 + (Vx - 5)/R3 = 0", fill=ORANGE, font=font(34))
    draw.text((140, 450), "Then solve for Vx.", fill=(70, 83, 115), font=font(30))
    save(img, f"{folder}/03_kcl_equacao_no.png")

    img, draw = new_light_slide("KVL: Kirchhoff's Voltage Law")
    draw.rectangle((250, 180, 980, 500), outline=(42, 42, 42), width=4)
    draw.arc((370, 210, 850, 460), start=200, end=350, fill=BLUE, width=4)
    draw.text((540, 314), "Loop", fill=(70, 83, 115), font=font(30))
    draw.text((324, 236), "+Vsource", fill=GREEN, font=font(18))
    draw.text((804, 236), "-V_R1", fill=BLUE, font=font(18))
    draw.text((790, 395), "-V_R2", fill=ORANGE, font=font(18))
    draw.text((330, 550), "+Vsource - V_R1 - V_R2 = 0", fill=GREEN, font=font(28))
    draw.text((330, 590), "The algebraic sum of voltages in a closed loop is zero.", fill=(70, 83, 115), font=font(22))
    save(img, f"{folder}/04_kvl_malha.png")

    img, draw = new_light_slide("Step by Step: Node Method")
    draw_step_boxes(draw, [
        "Choose GND (0 V reference).",
        "Name the remaining nodes: V1, V2, ...",
        "Write KCL at each unknown node.",
        "Substitute currents by (Vnode - Vneighbor) / R.",
        "Solve the linear system.",
    ], 205)
    save(img, f"{folder}/05_passos_metodo_nos.png")

    img, draw = new_light_slide("Numerical Node Example")
    draw.text((420, 205), "Given: R1=2 ohms to 10V, R2=4 ohms to GND, R3=8 ohms to 4V.", fill=TEXT, font=font(24))
    draw.text((380, 318), "(Vx-10)/2 + (Vx-0)/4 + (Vx-4)/8 = 0", fill=ORANGE, font=font(34))
    draw.text((520, 470), "Result: Vx = 6 V", fill=GREEN, font=font(34))
    save(img, f"{folder}/06_exemplo_numerico.png")

    img, draw = new_light_slide("Always Connect GND")
    draw_paragraph(draw, "GND = Ground: the 0 V reference for the circuit and the measurements. Without GND, the circuit may not converge and the results can become inconsistent.", (50, 170), font(28), TEXT, 720, 6)
    draw_ground(draw, 930, 470, 1.2)
    save(img, f"{folder}/07_gnd_referencia.png")

    img, draw = new_light_slide("How to Solve the Panels in This Stage")
    draw_step_boxes(draw, [
        "Find the reference node and the unknown nodes.",
        "Write KCL at each node.",
        "Use KVL only when you need loop relations.",
        "Solve and verify the requested unit: V or A.",
        "Validate on the panel and adjust the circuit if needed.",
    ], 198, 655)
    save(img, f"{folder}/08_passos_paineis.png")


def gen_thevenin_norton():
    folder = "thevenin_norton_en"
    ensure_dir(folder)
    img, draw = new_light_slide("Thevenin and Norton: Overview")
    draw_paragraph(draw, "These theorems simplify linear networks seen from terminals A-B.", (46, 145), font(28), TEXT, 640, 8)
    draw_paragraph(draw, "Goal: replace a complex network with a simple equivalent that is faster to analyze.", (46, 240), font(28), (70, 83, 115), 700, 8)
    save(img, f"{folder}/01_visao_geral.png")

    img, draw = new_light_slide("Thevenin Equivalent")
    draw.rounded_rectangle((140, 190, 470, 470), radius=10, outline=(42, 42, 42), width=3, fill=(251, 251, 252))
    draw.rounded_rectangle((690, 190, 1140, 470), radius=10, outline=(42, 42, 42), width=3, fill=(251, 251, 252))
    draw.text((245, 315), "Original\nnetwork", fill=(70, 83, 115), font=font(28), align="center")
    draw.text((790, 270), "Voltage source Vth", fill=GREEN, font=font(24))
    draw.text((790, 335), "in series with Rth", fill=ORANGE, font=font(24))
    draw.text((550, 315), "=>", fill=ORANGE, font=font(36, bold=True))
    draw.text((360, 520), "Thevenin = voltage source Vth + resistor Rth in series.", fill=GREEN, font=font(24))
    save(img, f"{folder}/02_thevenin_conceito.png")

    img, draw = new_light_slide("Norton Equivalent")
    draw.rounded_rectangle((140, 190, 470, 470), radius=10, outline=(42, 42, 42), width=3, fill=(251, 251, 252))
    draw.rounded_rectangle((690, 190, 1140, 470), radius=10, outline=(42, 42, 42), width=3, fill=(251, 251, 252))
    draw.text((245, 315), "Original\nnetwork", fill=(70, 83, 115), font=font(28), align="center")
    draw.text((790, 270), "Current source In", fill=GREEN, font=font(24))
    draw.text((790, 335), "in parallel with Rn", fill=ORANGE, font=font(24))
    draw.text((550, 315), "=>", fill=ORANGE, font=font(36, bold=True))
    draw.text((300, 520), "Norton = current source In + resistor Rn in parallel.", fill=GREEN, font=font(24))
    save(img, f"{folder}/03_norton_conceito.png")

    img, draw = new_light_slide("Relationship Between Thevenin and Norton")
    draw.text((420, 220), "Rth = Rn", fill=ORANGE, font=font(42))
    draw.text((420, 300), "Vth = In x Rth", fill=ORANGE, font=font(42))
    draw.text((420, 380), "In = Vth / Rth", fill=ORANGE, font=font(42))
    draw.text((420, 500), "You can convert from one pair to the other whenever it is more convenient.", fill=TEXT, font=font(24))
    save(img, f"{folder}/04_relacoes.png")

    img, draw = new_light_slide("How to Find Vth and Rth")
    draw_step_boxes(draw, [
        "Remove the load from terminals A-B.",
        "Calculate the open-circuit voltage: Vth.",
        "Disable independent sources to find Rth.",
        "Compute the equivalent resistance seen from A-B.",
    ], 220)
    save(img, f"{folder}/05_passos_vth_rth.png")

    img, draw = new_light_slide("How to Find In (Norton Current)")
    draw.text((260, 230), "In is the short-circuit current between terminals A-B.", fill=TEXT, font=font(30))
    draw.text((260, 325), "Step: short A-B, calculate Isc, and use In = Isc.", fill=ORANGE, font=font(32))
    draw.text((260, 440), "Then use Rn = Rth.", fill=GREEN, font=font(32))
    save(img, f"{folder}/06_passos_inorton.png")

    img, draw = new_light_slide("GND Is Essential Here Too")
    draw_paragraph(draw, "Use GND as the 0 V reference to measure Vth and the remaining voltages. Without GND, results may become undefined or wrong.", (70, 180), font(28), TEXT, 760, 8)
    draw_ground(draw, 930, 470, 1.2)
    save(img, f"{folder}/08_gnd_referencia.png")

    img, draw = new_light_slide("Step by Step for the Panels")
    draw_step_boxes(draw, [
        "Identify the load terminals.",
        "Calculate Vth and Rth (or In and Rn).",
        "Assemble the requested equivalent.",
        "Check the unit and the sign of each quantity.",
        "Ensure the circuit has GND before validating.",
    ], 205, 655)
    save(img, f"{folder}/09_passos_paineis.png")


def gen_max_power_transfer():
    folder = "max_power_transfer_en"
    ensure_dir(folder)
    slides = [
        ("Maximum Power Transfer", "Goal: find the load RL that receives the highest power from a linear network."),
        ("Step 1: Thevenin Equivalent", "From the load perspective: a Thevenin source in series with resistance Rth."),
        ("Maximum Condition", "Power on RL is maximized when RL = Rth."),
        ("Power Expression", "P(RL) = (Vth^2 * RL) / (Rth + RL)^2. The peak occurs when RL equals Rth."),
        ("How to Find Vth and Rth", "1) Open the load and measure Vth. 2) Disable independent sources and calculate Rth."),
        ("Quick Example", "If Vth=12V and Rth=6 ohms, choose RL=6 ohms for maximum load power."),
        ("Efficiency at the Maximum Point", "In the ideal Thevenin case, half of the power goes to RL and half to Rth."),
        ("Ground Reference (GND)", "Define GND to obtain consistent voltages and avoid ambiguous results."),
        ("Apply It to the Panels", "Read the target, estimate Rth, adjust RL, and verify whether the power is close to the expected value."),
    ]
    names = [
        "01_visao_geral.png",
        "02_equivalente_thevenin.png",
        "03_condicao_maxima.png",
        "04_forma_potencia.png",
        "05_passos_vth_rth.png",
        "06_exemplo_numerico.png",
        "07_eficiencia.png",
        "08_gnd_referencia.png",
        "09_passos_paineis.png",
    ]
    for (title, body), name in zip(slides, names):
        img, draw = new_dark_slide(title)
        if name == "09_passos_paineis.png":
            draw_step_boxes(
                draw,
                [
                    "Read the target power shown by the panel.",
                    "Estimate or calculate the Thevenin resistance Rth.",
                    "Adjust RL so it gets close to Rth.",
                    "Compare the resulting power with the requested value.",
                    "Validate and fine-tune the circuit if needed.",
                ],
                body_top=210,
                body_bottom=585,
                box_width=980,
                font_size=28,
                fill=(27, 44, 60),
                outline=(70, 103, 133),
                text_fill=(236, 240, 245),
            )
        else:
            draw_paragraph(draw, body, (116, 272), font(34), (230, 234, 238), 980, 10)
        save(img, f"{folder}/{name}")


def main():
    gen_ohm_law()
    gen_electric_power()
    gen_resistor_assoc()
    gen_nodal_kirchhoff()
    gen_thevenin_norton()
    gen_max_power_transfer()
    print("English explanation assets generated.")


if __name__ == "__main__":
    main()
