// The four states a user can be in, per Stage 2 of the redesign plan:
// no account -> account with no attempts -> attempt in progress ->
// attempt completed with a result. Routes declare which states they're
// valid in; guards read this to decide whether to redirect.
export type UserJourneyState =
  | 'no-account'
  | 'account-no-attempts'
  | 'attempt-in-progress'
  | 'attempt-completed';
