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
