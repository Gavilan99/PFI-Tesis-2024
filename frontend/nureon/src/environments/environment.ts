// Production build. apiBaseUrl is a placeholder: there is no domain and no
// deployed backend yet (deployment is backend Feature 8), so this build can
// prerender and serve the public pages but not complete a flow.
export const environment = {
  production: true,
  apiBaseUrl: 'https://api.nureon.ai',
  useMockApi: false,
};
