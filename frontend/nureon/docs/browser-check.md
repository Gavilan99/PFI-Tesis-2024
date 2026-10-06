# Verificación cross-browser (RNF04)

Objetivo de la Etapa 9: confirmar que los cuatro casos de uso principales andan igual en
Chrome, Firefox, Edge y Brave, y dejar anotada cualquier diferencia de render, por menor que sea.

- **CU001** — Registrarse (`registro.component.ts`)
- **CU002** — Iniciar sesión (`ingresar.component.ts`)
- **CU003** — El test (`test.component.ts`)
- **CU004** — Ver resultados (`resultados.component.ts`)

## Contra qué se probó

Todo se probó contra **`ng serve` (`localhost:4200`)**, no contra el build de producción.
Motivo: `environment.ts` (el que usa `ng build`) tiene `useMockApi: false` y apunta a
`https://api.nureon.ai`, que no existe todavía — `HttpApiService.register()`/`login()`/etc. son
stubs que tiran `Error: ... is not implemented yet` a propósito (ver `mvp-status.md`). Contra el
build de producción, CU001 y CU002 fallan siempre, en cualquier navegador — no es un bug de esta
etapa, es el estado esperado hasta que el backend real reemplace al mock.

Con `ng serve`, `environment.development.ts` pone `useMockApi: true` y todo corre contra
`MockApiService`. Ese estado vive en `localStorage` del navegador (no hay servidor de por medio),
así que **una cuenta registrada a mano en un navegador no existe en los otros** — cada navegador
tiene su propio storage. Para no depender de eso, las cuatro pasadas usaron la cuenta demo
seedeada en el propio código (`mock-api.service.ts`), que existe igual en cualquier navegador
sin necesidad de registrarla antes:

```
email: demo@nureon.ai
password: Demo1234
```

## Resultado

| Navegador | CU001 | CU002 | CU003 | CU004 | Diferencias de render |
|---|---|---|---|---|---|
| Chrome  | ✅ | ✅ | ✅ | ✅ | Ninguna — pasada detallada abajo |
| Edge    | ✅ | ✅ | ✅ | ✅ | Ninguna |
| Firefox | ✅ | ✅ | ✅ | ✅ | Ninguna |
| Brave   | ✅ | ✅ | ✅ | ✅ | Ninguna |

Los cuatro navegadores pasan los cuatro casos de uso sin diferencias visuales. Chrome se
recorrió con automatización (`claude-in-chrome`) con el detalle de abajo; Firefox, Edge y Brave
se recorrieron a mano siguiendo el mismo guion.

### Detalle de la pasada en Chrome

- **CU001**: formulario completo con cuenta nueva (usuario/email/contraseña) → "Crear cuenta" →
  pantalla de éxito → "Ir a mi cuenta". Sin errores en consola.
- **CU002**: logout → login con la cuenta recién creada → redirige a `/inicio`. Logout también
  probado con la cuenta demo en un tab nuevo — la sesión persiste vía `localStorage`
  (`nureon_mock_auth_user`) entre navegaciones y tabs nuevos del mismo navegador.
- **CU003**: recorrido de varios ítems (Likert de 5 opciones y de escenario de 3 opciones),
  selección por mouse y por teclado (`aria-keyshortcuts` 1-5), auto-advance sin botón "Siguiente",
  barra de progreso actualizándose, foco visible (`:focus-visible`, verde de marca) al tabular
  entre opciones.
- **CU004**: resultado con diagrama de eneagrama, eneatipo, motivación central, fortalezas,
  tensiones, alas, y el overlay de freemium ("Desbloquear mi perfil completo") sobre la sección
  "En crecimiento y bajo estrés" para una cuenta sin `tier: 'paid_full'`.
- Responsive: mismo recorrido de CU003/CU004 repetido con el device toolbar de Chrome DevTools
  en ~390px de ancho — el menú colapsa a hamburguesa, las tarjetas de opciones se apilan, nada
  se corta ni desborda horizontalmente.

### Notas sobre la herramienta de automatización

- `claude-in-chrome` solo controla instancias de **Chrome** (o Edge/Brave si se les instala la
  misma extensión). No puede automatizar Firefox bajo ninguna configuración — se recorrió a mano.
- `resize_window` no siempre aplica sobre una ventana maximizada/snapeada en Windows; el device
  toolbar de DevTools (`Ctrl+Shift+M`) fue el método confiable para emular ancho mobile.

## Pendiente fuera de alcance de esta etapa

- El contenido de los ítems del test (`questions.sample.json`) es contenido de relleno explícito
  ("Enunciado de ejemplo…"), no el banco real — ver `mvp-status.md`. No afecta la comparación
  entre navegadores (todos renderizan el mismo relleno igual), pero si se recapturan estas
  pantallas más adelante con el banco real, conviene repetir esta verificación.

## Etapa 10 — recorrido de punta a punta contra `build:demo`

Objetivo distinto al de arriba: no cross-browser, sino confirmar que el build **desplegable**
(`npm run build:demo`, servido como estático + SSR, sin `ng serve`) completa el recorrido entero
sin tocar ninguna pantalla en construcción — ver `docs/mvp-status.md` para el detalle de qué
cerró esta etapa (`/inicio` real, `/eneagrama`, `/nosotros`, `/contacto`).

Verificado en Chrome contra `localhost:4400` sirviendo `dist/nureon` compilado con
`--configuration demo`:

- **Cuenta demo preseedeada**: `demo@nureon.ai` / `Demo1234` entra directo a `/inicio` con un
  resultado ya completo ("Ya tenés un resultado esperándote") — no hace falta responder 40
  preguntas para ver `/resultados`.
- **Cuenta nueva de punta a punta**: `/` → "Empezar gratis" → registro → confirmación
  ("Empezar el test", ya no "Ir a mi cuenta") → test completo (40 ítems, teclado) →
  "¡Listo! Terminaste el test" → resultado. Sin pasar por ningún placeholder en ningún punto.
- **Los tres links del header** (`/eneagrama`, `/nosotros`, `/contacto`) llevan a contenido real,
  no al placeholder de Etapa 2.
- **Freemium**: "Desbloquear mi perfil completo" abre el panel de niveles (`Escape`, click en
  backdrop y botón "Cerrar" lo cierran; el foco vuelve al botón que lo abrió). No desbloquea nada
  ni simula un pago — dice explícitamente que el flujo de pago está en desarrollo.
- **Contacto**: formulario completo contra `MockApiService.submitContactMessage` → confirmación
  en pantalla.
- **`npm run build`** (producción normal) sigue compilando sin warnings de budget después de los
  cambios de esta etapa.

### Pendiente de esta etapa

- Las capturas mobile `05-test-item-mobile.jpg` y `07-resultados-mobile.jpg` en
  `docs/screenshots/` **son las de Etapa 9** — el device toolbar de Chrome DevTools no volvió a
  responder de forma confiable en esta sesión (varios intentos, incluso en tabs nuevos) para
  recapturarlas con el footer oculto y el layout de resultados nuevo. Las versiones desktop
  (`04`, `06`) sí están actualizadas. Quedan desactualizadas hasta la próxima sesión con la
  herramienta funcionando, o hasta que alguien las saque a mano.
- No se repitió la pasada de Firefox/Edge/Brave para esta etapa — el objetivo acá era el build
  demo de punta a punta, no cross-browser otra vez. Si hace falta, se puede repetir el mismo
  guion (cuenta demo → `/inicio` → resto del recorrido) en los otros tres navegadores.
