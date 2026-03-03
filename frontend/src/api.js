import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '';

const api = axios.create({ baseURL: API_BASE });

// Attach JWT on every request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

// Auto-logout on 401
api.interceptors.response.use(
    (r) => r,
    (err) => {
        if (err.response?.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(err);
    }
);

export default api;

// ── Auth ──────────────────────────────────────────────────────────
export const login = (password) => {
    const form = new URLSearchParams();
    form.append('username', 'admin');  // fixed
    form.append('password', password);
    return api.post('/api/auth/login', form, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
};

// ── Buildings ─────────────────────────────────────────────────────
export const getBuildings = () => api.get('/api/buildings');

// ── Months ────────────────────────────────────────────────────────
export const getMonths = () => api.get('/api/months');
export const createMonth = (year, month) => api.post('/api/months', { year, month });
export const getMonth = (year, month) => api.get(`/api/months/${year}/${month}`);
export const updateRate = (year, month, rateData) => api.put(`/api/months/${year}/${month}/rate`, rateData);
export const updateRooms = (year, month, rooms) => api.put(`/api/months/${year}/${month}/rooms`, rooms);

// ── PDF ───────────────────────────────────────────────────────────
export const generatePdf = async (year, month) => {
    const res = await api.post(`/api/months/${year}/${month}/generate-pdf`, {}, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `bills_${year}_${String(month).padStart(2, '0')}.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
};
