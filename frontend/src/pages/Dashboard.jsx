import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { getMonths, createMonth, importCSV, deleteMonth } from '../api';
import { useToast } from '../App';

const MONTH_NAMES = [
    '', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
];

export default function Dashboard() {
    const [months, setMonths] = useState([]);
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);
    const [importing, setImporting] = useState(false);
    const [showNew, setShowNew] = useState(false);
    const [newYear, setNewYear] = useState(dayjs().year());
    const [newMonth, setNewMonth] = useState(dayjs().month() + 1);
    const fileInputRef = useRef(null);
    const navigate = useNavigate();
    const toast = useToast();

    const fetchMonths = async () => {
        try {
            const res = await getMonths();
            setMonths(res.data);
        } catch {
            toast('Failed to load months', 'error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchMonths(); }, []);

    const handleCreate = async () => {
        setCreating(true);
        try {
            await createMonth(newYear, newMonth);
            toast(`${MONTH_NAMES[newMonth]} ${newYear} created!`);
            setShowNew(false);
            fetchMonths();
        } catch (err) {
            toast(err.response?.data?.detail || 'Error creating month', 'error');
        } finally {
            setCreating(false);
        }
    };

    const handleImportClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setImporting(true);
        try {
            const res = await importCSV(newYear, newMonth, file);
            toast(res.data.message || `Imported ${res.data.rooms_imported} rooms!`);
            setShowNew(false);
            fetchMonths();
        } catch (err) {
            toast(err.response?.data?.detail || 'Error importing CSV', 'error');
        } finally {
            setImporting(false);
            // Reset file input so same file can be selected again
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleDelete = async (year, month, monthName) => {
        if (!window.confirm(`Delete ${monthName} ${year}? This will remove all room data. This cannot be undone.`)) return;
        try {
            await deleteMonth(year, month);
            toast(`${monthName} ${year} deleted`);
            fetchMonths();
        } catch (err) {
            toast(err.response?.data?.detail || 'Error deleting month', 'error');
        }
    };

    return (
        <div className="page">
            <div className="page-header flex justify-between items-center">
                <div>
                    <h1>Monthly Bills</h1>
                    <p className="text-muted">Select a month to edit readings and generate PDFs</p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowNew(!showNew)}>
                    {showNew ? '✕ Cancel' : '+ New Month'}
                </button>
            </div>

            {/* New month form */}
            {showNew && (
                <div className="card mt-4" style={{ padding: '1.5rem' }}>
                    <div className="flex gap-4 items-center wrap">
                        <div>
                            <label className="text-muted text-sm" style={{ display: 'block', marginBottom: 4 }}>Year</label>
                            <input
                                type="number" value={newYear} min={2020} max={2099}
                                onChange={(e) => setNewYear(+e.target.value)}
                                style={{ width: 90 }}
                            />
                        </div>
                        <div>
                            <label className="text-muted text-sm" style={{ display: 'block', marginBottom: 4 }}>Month</label>
                            <select value={newMonth} onChange={(e) => setNewMonth(+e.target.value)} style={{ width: 140 }}>
                                {MONTH_NAMES.slice(1).map((m, i) => (
                                    <option key={i + 1} value={i + 1}>{m}</option>
                                ))}
                            </select>
                        </div>
                        <button
                            className="btn btn-success"
                            style={{ alignSelf: 'flex-end' }}
                            disabled={creating}
                            onClick={handleCreate}
                        >
                            {creating ? 'Creating…' : 'Create Empty Month'}
                        </button>
                    </div>

                    {/* CSV Import section */}
                    <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', marginTop: '1rem', paddingTop: '1rem' }}>
                        <p className="text-muted text-sm" style={{ marginBottom: 8 }}>
                            Or import from an existing CSV file:
                        </p>
                        <input
                            type="file"
                            accept=".csv"
                            ref={fileInputRef}
                            onChange={handleFileChange}
                            style={{ display: 'none' }}
                        />
                        <button
                            className="btn"
                            style={{ background: '#2563eb', color: '#fff' }}
                            disabled={importing}
                            onClick={handleImportClick}
                        >
                            {importing ? 'Importing…' : '📄 Import CSV'}
                        </button>
                    </div>
                </div>
            )}

            {/* Month cards */}
            {loading ? (
                <p className="text-muted mt-4">Loading…</p>
            ) : months.length === 0 ? (
                <div className="card mt-4" style={{ textAlign: 'center', padding: '3rem' }}>
                    <p style={{ fontSize: '2rem' }}>📋</p>
                    <p className="mt-2">No months yet. Create your first month above.</p>
                </div>
            ) : (
                <div className="months-grid">
                    {months.map((m) => (
                        <div
                            key={`${m.year}-${m.month}`}
                            className="card month-card"
                            style={{ position: 'relative' }}
                        >
                            <div onClick={() => navigate(`/month/${m.year}/${m.month}`)} style={{ cursor: 'pointer', flex: 1 }}>
                                <h2>{m.month_name}</h2>
                                <p className="year">{m.year}</p>
                                <div className="flex gap-2 mt-3 wrap">
                                    <span className="badge badge-purple">৳{m.electricity_rate}/unit</span>
                                    {m.rate_threshold_units > 0 && (
                                        <span className="badge badge-green">Tiered billing</span>
                                    )}
                                </div>
                                <p className="text-muted mt-2" style={{ fontSize: '0.75rem' }}>
                                    Created {dayjs(m.created_at).format('MMM D, YYYY')}
                                </p>
                            </div>
                            <button
                                className="btn"
                                style={{
                                    position: 'absolute', top: 8, right: 8,
                                    background: 'rgba(239,68,68,0.15)', color: '#ef4444',
                                    padding: '4px 10px', fontSize: '0.75rem', borderRadius: 6,
                                }}
                                onClick={(e) => { e.stopPropagation(); handleDelete(m.year, m.month, m.month_name); }}
                                title="Delete this month"
                            >
                                🗑
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
