// Everything the legal texts (/privacidad, /terminos, the consent on
// /registro) need that is not decided yet lives here, and only here, as a
// visible marker. tools/check-legal-placeholders.mjs builds production and
// fails while any marker is still in the output: fill these in before the
// release.

// Who is responsible for the database (Ley 25.326, art. 6 inc. b asks for
// the identity and the address of the responsible party): name and address.
export const LEGAL_RESPONSIBLE = 'Juan Manuel Gavilan y Tobías Nahuel Vodopivec';

// Where people write to exercise their rights (access, rectification,
// deletion) and ask anything about their data.
export const LEGAL_CONTACT_EMAIL = 'eneagramnureon@gmail.com';

// The version of the texts. The backend stores its own CONSENT_VERSION with
// every new account: when these texts change, both change together.
export const LEGAL_TEXT_VERSION = '2026-11-03';
export const LEGAL_TEXT_DATE = '3 de noviembre de 2026';

// The short notice above "Crear cuenta" (art. 6: inform before collecting).
// Feature 22: mentions that the account type chosen below changes what the service does (salud/
// rrhh administer the test to other people) and, for those two, the per-test consent declaration.
export const CONSENT_SUMMARY =
  'Tus respuestas al test y los datos de tu perfil se usan para calcular tu resultado, para ' +
  'personalizar la descripción del resultado en el plan pago y para mejorar el instrumento. Si ' +
  'elegís una cuenta de salud o de recursos humanos, podés administrar el test en forma presencial ' +
  'a otras personas, declarando antes de cada test que contás con su consentimiento. Se guardan en ' +
  'servidores de Amazon Web Services en Estados Unidos. Podés pedir acceso, corrección o borrado de ' +
  'tus datos, o borrar tu cuenta desde tu perfil.';
