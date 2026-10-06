#!/usr/bin/env python3
"""
Generate Angular Material 2 palette maps from NureonAI brand base colors.

Replaces the hand-estimated tints in src/custom-theme.scss with deterministic,
reproducible output. Run it, paste the result, commit both.

    python tools/generate_palette.py > docs/palette-source.md

The 50-900 ramp uses the algorithm popularised by the mcg palette generator
(mcg.mbitson.com), reimplemented here because that site is HTTP-only and
frequently unreachable:

    baseLight = #ffffff
    baseDark  = base multiplied by itself (per-channel, /255)
    50..400   = baseLight mixed with base at 12/30/50/70/85 %
    500       = base
    600..900  = baseDark mixed with base at 87/70/54/25 %

The A-series is NOT taken from that algorithm, whose tetrad-based accent maths
is unstable. It is derived from an explicit brand accent seed by moving
lightness in HSL while preserving hue, so brand colors stay brand colors.

Contrast values are computed with the WCAG 2.1 relative-luminance formula and
follow Material's convention: rgba(black, .87) on light tints, white on dark.
"""

import colorsys

# (palette name, base hex used as 500, accent seed for the A-series)
PALETTES = [
    ("nureon-primary", "#1a7f5b", "#5bc795"),   # dark spring green, mint accent
    ("nureon-accent",  "#7cb0eb", "#7cb0eb"),   # ruddy blue
]

RAMP_LIGHT = {"50": 12, "100": 30, "200": 50, "300": 70, "400": 85}
RAMP_DARK = {"600": 87, "700": 70, "800": 54, "900": 25}


def to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(c))) for c in rgb))


def mix(c1, c2, amount):
    """tinycolor.mix semantics: amount is the percentage of c2."""
    p = amount / 100.0
    return tuple(a * (1 - p) + b * p for a, b in zip(c1, c2))


def multiply(c1, c2):
    return tuple(a * b / 255.0 for a, b in zip(c1, c2))


def shift_lightness(hex_color, delta_l, delta_s=0.0):
    r, g, b = (c / 255.0 for c in to_rgb(hex_color))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = max(0.0, min(1.0, l + delta_l))
    s = max(0.0, min(1.0, s + delta_s))
    return to_hex(tuple(c * 255 for c in colorsys.hls_to_rgb(h, l, s)))


def luminance(rgb):
    def chan(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(rgb1, rgb2):
    l1, l2 = luminance(rgb1), luminance(rgb2)
    lo, hi = sorted((l1, l2))
    return (hi + 0.05) / (lo + 0.05)


def build(base_hex, accent_seed):
    base = to_rgb(base_hex)
    light = (255.0, 255.0, 255.0)
    dark = multiply(base, base)

    tints = {}
    for key, amount in RAMP_LIGHT.items():
        tints[key] = to_hex(mix(light, base, amount))
    tints["500"] = to_hex(base)
    for key, amount in RAMP_DARK.items():
        tints[key] = to_hex(mix(dark, base, amount))

    # A-series: hue-preserving moves around the brand accent seed.
    tints["A100"] = shift_lightness(accent_seed, +0.18)
    tints["A200"] = accent_seed.lower()          # the brand color itself, untouched
    tints["A400"] = shift_lightness(accent_seed, -0.10, +0.08)
    tints["A700"] = shift_lightness(accent_seed, -0.20, +0.12)

    order = ["50", "100", "200", "300", "400", "500", "600", "700", "800", "900",
             "A100", "A200", "A400", "A700"]
    return [(k, tints[k]) for k in order]


def contrast_for(hex_color):
    rgb = to_rgb(hex_color)
    on_white = contrast_ratio(rgb, (255, 255, 255))
    on_black = contrast_ratio(rgb, (0, 0, 0))
    if on_black >= on_white:
        return "rgba(black, 0.87)", on_black
    return "white", on_white


def main():
    print("# Paletas de marca — salida del generador\n")
    print("Generado por `tools/generate_palette.py`. **No editar a mano.** Si hay que cambiar un")
    print("color, se cambia el hex base o la semilla de acento en el script y se vuelve a correr.\n")
    print("Reemplaza los tints estimados a ojo que tenía `src/custom-theme.scss`. El algoritmo del")
    print("ramp 50-900 es el de mcg (`mcg.mbitson.com`), reimplementado acá porque ese sitio es")
    print("solo HTTP y no siempre responde. La serie A no usa la matemática de tetrad de mcg, que")
    print("es inestable: se deriva de la semilla de acento de marca moviendo luminosidad en HSL,")
    print("con el hue intacto. Por eso `A200` es exactamente el color de marca, sin tocar.\n")
    print("No existe un generador oficial de Google para paletas Material 2 — las originales las")
    print("hizo a mano el equipo de diseño. La mejora sobre lo anterior no es que sean oficiales,")
    print("es que son deterministas, reproducibles y con el contraste calculado por WCAG 2.1 en")
    print("lugar de elegido a ojo.\n")

    for name, base, seed in PALETTES:
        print(f"\n## `${name}-palette`\n")
        print(f"Base (500): `{base}` · semilla de acento (A200): `{seed}`\n")
        rows = build(base, seed)

        print("```scss")
        print(f"${name}-palette: (")
        for key, hex_color in rows:
            print(f"  {key}: {hex_color},")
        print("  contrast: (")
        for key, hex_color in rows:
            fg, _ = contrast_for(hex_color)
            print(f"    {key}: {fg},")
        print("  ),")
        print(");")
        print("```\n")

        print("| Tint | Hex | Texto encima | Ratio | AA texto normal | AA texto grande |")
        print("|---|---|---|---|---|---|")
        for key, hex_color in rows:
            fg, ratio = contrast_for(hex_color)
            aa = "sí" if ratio >= 4.5 else "**no**"
            aa_lg = "sí" if ratio >= 3.0 else "**no**"
            print(f"| {key} | `{hex_color}` | {fg} | {ratio:.2f} | {aa} | {aa_lg} |")

    print("\n## Nota para la Etapa 8\n")
    print("Los ratios de arriba son de texto sobre el tint. Las combinaciones que la Etapa 8 tiene")
    print("que medir aparte son las de marca sobre fondo de página: verde `#1a7f5b`, menta")
    print("`#5bc795`, azul `#7cb0eb`, ámbar `#ffbf1f` y naranja `#ff6d33` sobre blanco.\n")

    print("| Color de marca sobre blanco | Ratio | AA texto normal | AA texto grande |")
    print("|---|---|---|---|")
    for label, hexv in [("verde oscuro `#1a7f5b`", "#1a7f5b"), ("menta `#5bc795`", "#5bc795"),
                        ("azul `#7cb0eb`", "#7cb0eb"), ("ámbar `#ffbf1f`", "#ffbf1f"),
                        ("naranja `#ff6d33`", "#ff6d33")]:
        r = contrast_ratio(to_rgb(hexv), (255, 255, 255))
        print(f"| {label} | {r:.2f} | {'sí' if r >= 4.5 else '**no**'} | {'sí' if r >= 3.0 else '**no**'} |")


if __name__ == "__main__":
    main()
