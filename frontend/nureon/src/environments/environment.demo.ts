// Stage 10 — deployable to S3 without a real backend: `production: true` so
// dev tools and the /styleguide route stay excluded (this is meant to be
// shown to people, not poked at), `useMockApi: true` so every screen works
// against MockApiService's seeded state instead of throwing against
// apiBaseUrl, which doesn't need to resolve to anything real here.
export const environment = {
  production: true,
  apiBaseUrl: '',
  useMockApi: true,
};
