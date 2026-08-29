// Mirrors the `users` table (PDR — NureonAI Data Model). account_type,
// age_range, gender, country and profession_context are the profile fields
// RF01's registration form deferred — RF07 (Stage 7) is where they're
// actually collected/edited, so they're nullable until the user fills them in.
export type AccountType = 'individual' | 'rrhh' | 'salud';

export interface User {
  id: string;
  displayName: string;
  email: string;
  accountType: AccountType | null;
  ageRange: string | null;
  gender: string | null;
  country: string | null;
  professionContext: string | null;
}

// What RegistroComponent's flow populates — everything else starts null.
export type NewUserDefaults = Pick<User, 'id' | 'displayName' | 'email'>;

export function withEmptyProfile(defaults: NewUserDefaults): User {
  return {
    ...defaults,
    accountType: null,
    ageRange: null,
    gender: null,
    country: null,
    professionContext: null,
  };
}

// What the profile screen (RF07) can actually change.
export type UpdateProfileInput = Partial<
  Pick<User, 'displayName' | 'accountType' | 'ageRange' | 'gender' | 'country' | 'professionContext'>
>;
