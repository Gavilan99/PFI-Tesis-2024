// RF01: username, email, password, plus the consent (Ley 25.326, Feature 11)
// — nothing else. The rest of what the `users` table eventually needs is
// collected in the profile (RF07, Stage 7). consentAccepted must be true:
// the backend rejects the registration otherwise (CONSENT_REQUIRED), and
// records the version of the texts in force itself — the client never sends it.
export interface RegisterInput {
  username: string;
  email: string;
  password: string;
  consentAccepted: boolean;
}

export interface LoginInput {
  email: string;
  password: string;
}
