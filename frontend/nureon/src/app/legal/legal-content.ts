// Everything the legal texts (/privacidad, /terminos, the consent on
// /registro) need that is not decided yet lives here, and only here, as a
// visible marker. tools/check-legal-placeholders.mjs builds production and
// fails while any marker is still in the output: fill these in before the
// release.

// Who is responsible for the database (Ley 25.326, art. 6 inc. b asks for
// the identity and the address of the responsible party): name and address.
export const LEGAL_RESPONSIBLE = '[RESPONSABLE]';

// Where people write to exercise their rights (access, rectification,
// deletion) and ask anything about their data.
export const LEGAL_CONTACT_EMAIL = '[CONTACTO]';

// The version of the texts. The backend stores its own CONSENT_VERSION with
// every new account: when these texts change, both change together.
export const LEGAL_TEXT_VERSION = '2026-10-20';
export const LEGAL_TEXT_DATE = '20 de octubre de 2026';

// The short notice above "Crear cuenta" (art. 6: inform before collecting).
export const CONSENT_SUMMARY =
  'Tus respuestas al test y los datos de tu perfil se usan para calcular tu resultado y para ' +
  'mejorar el instrumento. Se guardan en servidores de Amazon Web Services en Estados Unidos. ' +
  'Podés pedir acceso, corrección o borrado de tus datos, o borrar tu cuenta desde tu perfil.';
