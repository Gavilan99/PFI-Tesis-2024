// Development runs against the Flask backend on this machine (`python wsgi.py`
// in backend/, loopback port 5000; its CORS_ALLOWED_ORIGINS includes
// http://localhost:4200). To go back to MockApiService, set useMockApi: true.
export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:5000',
  useMockApi: false,
};
