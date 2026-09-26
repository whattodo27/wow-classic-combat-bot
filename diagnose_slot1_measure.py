"""Measure slot 1 exactly, plus the combat indicator by the portrait."""

from __future__ import annotations

from PIL import Image

from combat_bot.capture import WindowCapture

BAR_TOP = 0.895
SLOT_LEFT = 0.005
SLOT_SPAN = 0.065


def _rgb(image: Image.Image):
    rgb = image.convert("RGB")
    return rgb, list(rgb.getdata())


def analyse(image: Image.Image) -> None:
    width, height = image.size
    print(f"window={width}x{height}")

    # Row profile inside the slot-1 area only: find top/bottom of the icon.
    x0 = int(width * SLOT_LEFT)
    x1 = x0 + int(width * SLOT_SPAN)
    top = int(height * BAR_TOP)
    crop = image.crop((x0, top, x1, height))
    rgb, data = _rgb(crop)
    cw, ch = rgb.size

    print("\n--- rows in slot-1 column band (lit pixels) ---")
    rows = []
    for y in range(ch):
        lit = sum(
            1
            for x in range(cw)
            if sum(data[y * cw + x]) > 120
        )
        rows.append(lit)
    for index, value in enumerate(rows):
        print(f"  y {index:>3} (abs {top + index:>4}) : {value:>4}")

    print("\n--- red pixels inside slot 1 ---")
    reds = 0
    for y in range(ch):
        for x in range(cw):
            r, g, b = data[y * cw + x]
            if r > 90 and r - g > 50 and r - b > 50:
                reds += 1
    print(f"  red_pixels={reds}  of {cw * ch}")

    crop.resize((cw * 3, ch * 3), Image.NEAREST).save("diag_slot1.jpg", quality=95)

    # Combat indicator: crossed swords vs level number, left of the bars.
    ind_x0 = int(width * 0.055)
    ind_x1 = int(width * 0.098)
    ind_y0 = int(height * 0.035)
    ind_y1 = int(height * 0.095)
    ind = image.crop((ind_x0, ind_y0, ind_x1, ind_y1))
    irgb, idata = _rgb(ind)
    iw, ih = irgb.size
    lit = sum(1 for p in idata if sum(p) > 120)
    print(f"\n--- combat indicator box {ind.size} ---")
    print(f"  lit_pixels={lit}")
    ind.resize((iw * 4, ih * 4), Image.NEAREST).save("diag_combat.jpg", quality=95)


def main() -> int:
    capture = WindowCapture("World of Warcraft")
    image = capture.capture_image()
    if image is None:
        print("window not found")
        return 1
    image.save("current_window.jpg", quality=92)
    analyse(image)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
