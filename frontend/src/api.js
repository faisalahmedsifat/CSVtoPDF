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
export const deleteMonth = (year, month) => api.delete(`/api/months/${year}/${month}`);

// ── PDF ───────────────────────────────────────────────────────────
export const generatePdf = async (year, month, twoUp = false) => {
    const res = await api.post(
        `/api/months/${year}/${month}/generate-pdf?two_up=${twoUp}`,
        {},
        { responseType: 'blob' } // Important for binary data (PDF)
    );
    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `bills_${year}_${String(month).padStart(2, '0')}.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
};

// ── CSV Import ────────────────────────────────────────────────────
export const importCSV = (year, month, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/months/import-csv?year=${year}&month=${month}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
};

// ── CSV / Excel Export ─────────────────────────────────────────────
export const exportMonth = async (year, month, format = 'csv') => {
    const res = await api.get(`/api/months/${year}/${month}/export?format=${format}`, {
        responseType: 'blob',
    });
    const ext = format === 'xlsx' ? 'xlsx' : 'csv';
    const mimeType = format === 'xlsx'
        ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        : 'text/csv';
    const url = window.URL.createObjectURL(new Blob([res.data], { type: mimeType }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `bills_${year}_${String(month).padStart(2, '0')}.${ext}`;
    a.click();
    window.URL.revokeObjectURL(url);
};
