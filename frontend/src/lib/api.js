import axios from 'axios';

export function getApiBaseUrl() {
  const configuredUrl = import.meta.env.VITE_API_URL || import.meta.env.VITE_BACKEND_URL;
  if (!configuredUrl) return 'http://localhost:8000';
  return configuredUrl.replace(/\/run\/?$/, '').replace(/\/$/, '');
}

export const api = axios.create({
  baseURL: getApiBaseUrl(),
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('verdex_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
