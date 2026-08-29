// RF01: username, email, password — nothing else. The rest of what the
// `users` table eventually needs is collected in the profile (RF07, Stage 7).
export interface RegisterInput {
  username: string;
  email: string;
  password: string;
}

export interface LoginInput {
  email: string;
  password: string;
}
