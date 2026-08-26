# Paletas de marca — salida del generador

Generado por `tools/generate_palette.py`. **No editar a mano.** Si hay que cambiar un
color, se cambia el hex base o la semilla de acento en el script y se vuelve a correr.

Reemplaza los tints estimados a ojo que tenía `src/custom-theme.scss`. El algoritmo del
ramp 50-900 es el de mcg (`mcg.mbitson.com`), reimplementado acá porque ese sitio es
solo HTTP y no siempre responde. La serie A no usa la matemática de tetrad de mcg, que
es inestable: se deriva de la semilla de acento de marca moviendo luminosidad en HSL,
con el hue intacto. Por eso `A200` es exactamente el color de marca, sin tocar.

No existe un generador oficial de Google para paletas Material 2 — las originales las
hizo a mano el equipo de diseño. La mejora sobre lo anterior no es que sean oficiales,
es que son deterministas, reproducibles y con el contraste calculado por WCAG 2.1 en
lugar de elegido a ojo.


## `$nureon-primary-palette`

Base (500): `#1a7f5b` · semilla de acento (A200): `#5bc795`

```scss
$nureon-primary-palette: (
  50: #e4f0eb,
  100: #bad9ce,
  200: #8cbfad,
  300: #5fa58c,
  400: #3c9274,
  500: #1a7f5b,
  600: #177753,
  700: #136c49,
  800: #0f6240,
  900: #084f2f,
  A100: #9fdec1,
  A200: #5bc795,
  A400: #33bc7d,
  A700: #259762,
  contrast: (
    50: rgba(black, 0.87),
    100: rgba(black, 0.87),
    200: rgba(black, 0.87),
    300: rgba(black, 0.87),
    400: rgba(black, 0.87),
    500: white,
    600: white,
    700: white,
    800: white,
    900: white,
    A100: rgba(black, 0.87),
    A200: rgba(black, 0.87),
    A400: rgba(black, 0.87),
    A700: rgba(black, 0.87),
  ),
);
```

| Tint | Hex | Texto encima | Ratio | AA texto normal | AA texto grande |
|---|---|---|---|---|---|
| 50 | `#e4f0eb` | rgba(black, 0.87) | 17.96 | sí | sí |
| 100 | `#bad9ce` | rgba(black, 0.87) | 13.90 | sí | sí |
| 200 | `#8cbfad` | rgba(black, 0.87) | 10.17 | sí | sí |
| 300 | `#5fa58c` | rgba(black, 0.87) | 7.25 | sí | sí |
| 400 | `#3c9274` | rgba(black, 0.87) | 5.56 | sí | sí |
| 500 | `#1a7f5b` | white | 4.96 | sí | sí |
| 600 | `#177753` | white | 5.53 | sí | sí |
| 700 | `#136c49` | white | 6.42 | sí | sí |
| 800 | `#0f6240` | white | 7.39 | sí | sí |
| 900 | `#084f2f` | white | 9.68 | sí | sí |
| A100 | `#9fdec1` | rgba(black, 0.87) | 13.69 | sí | sí |
| A200 | `#5bc795` | rgba(black, 0.87) | 10.05 | sí | sí |
| A400 | `#33bc7d` | rgba(black, 0.87) | 8.63 | sí | sí |
| A700 | `#259762` | rgba(black, 0.87) | 5.68 | sí | sí |

## `$nureon-accent-palette`

Base (500): `#7cb0eb` · semilla de acento (A200): `#7cb0eb`

```scss
$nureon-accent-palette: (
  50: #eff6fd,
  100: #d8e7f9,
  200: #bed8f5,
  300: #a3c8f1,
  400: #90bcee,
  500: #7cb0eb,
  600: #74a9e9,
  700: #69a0e5,
  800: #5f97e3,
  900: #4c87dd,
  A100: #cce0f7,
  A200: #7cb0eb,
  A400: #4895ec,
  A700: #147aed,
  contrast: (
    50: rgba(black, 0.87),
    100: rgba(black, 0.87),
    200: rgba(black, 0.87),
    300: rgba(black, 0.87),
    400: rgba(black, 0.87),
    500: rgba(black, 0.87),
    600: rgba(black, 0.87),
    700: rgba(black, 0.87),
    800: rgba(black, 0.87),
    900: rgba(black, 0.87),
    A100: rgba(black, 0.87),
    A200: rgba(black, 0.87),
    A400: rgba(black, 0.87),
    A700: rgba(black, 0.87),
  ),
);
```

| Tint | Hex | Texto encima | Ratio | AA texto normal | AA texto grande |
|---|---|---|---|---|---|
| 50 | `#eff6fd` | rgba(black, 0.87) | 19.27 | sí | sí |
| 100 | `#d8e7f9` | rgba(black, 0.87) | 16.72 | sí | sí |
| 200 | `#bed8f5` | rgba(black, 0.87) | 14.33 | sí | sí |
| 300 | `#a3c8f1` | rgba(black, 0.87) | 12.09 | sí | sí |
| 400 | `#90bcee` | rgba(black, 0.87) | 10.61 | sí | sí |
| 500 | `#7cb0eb` | rgba(black, 0.87) | 9.27 | sí | sí |
| 600 | `#74a9e9` | rgba(black, 0.87) | 8.59 | sí | sí |
| 700 | `#69a0e5` | rgba(black, 0.87) | 7.76 | sí | sí |
| 800 | `#5f97e3` | rgba(black, 0.87) | 7.02 | sí | sí |
| 900 | `#4c87dd` | rgba(black, 0.87) | 5.82 | sí | sí |
| A100 | `#cce0f7` | rgba(black, 0.87) | 15.57 | sí | sí |
| A200 | `#7cb0eb` | rgba(black, 0.87) | 9.27 | sí | sí |
| A400 | `#4895ec` | rgba(black, 0.87) | 6.79 | sí | sí |
| A700 | `#147aed` | rgba(black, 0.87) | 5.04 | sí | sí |

## Nota para la Etapa 8

Los ratios de arriba son de texto sobre el tint. Las combinaciones que la Etapa 8 tiene
que medir aparte son las de marca sobre fondo de página: verde `#1a7f5b`, menta
`#5bc795`, azul `#7cb0eb`, ámbar `#ffbf1f` y naranja `#ff6d33` sobre blanco.

| Color de marca sobre blanco | Ratio | AA texto normal | AA texto grande |
|---|---|---|---|
| verde oscuro `#1a7f5b` | 4.96 | sí | sí |
| menta `#5bc795` | 2.09 | **no** | **no** |
| azul `#7cb0eb` | 2.27 | **no** | **no** |
| ámbar `#ffbf1f` | 1.65 | **no** | **no** |
| naranja `#ff6d33` | 2.80 | **no** | **no** |
