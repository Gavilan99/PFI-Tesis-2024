import { AccountType } from './user.model';

// RF01: username, email, password, plus the consent (Ley 25.326, Feature 11)
// — nothing else but accountType. The rest of what the `users` table
// eventually needs is collected in the profile (RF07, Stage 7).
// consentAccepted must be true: the backend rejects the registration
// otherwise (CONSENT_REQUIRED), and records the version of the texts in
// force itself — the client never sends it. accountType is required by the
// backend (Feature 20) but the registration form still doesn't ask for it —
// RegistroComponent always sends 'individual'; salud/rrhh is chosen later,
// in the profile, same as before.
export interface RegisterInput {
  username: string;
  email: string;
  password: string;
  accountType: AccountType;
  consentAccepted: boolean;
}

export interface LoginInput {
  email: string;
  password: string;
}
