import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { getMonth, updateRate, updateRooms, generatePdf } from '../api';
import { useToast } from '../App';

// ── Live calculation helpers (mirrors the Python model) ───────────────────────
function calcRoom(room, rate, highRate, threshold) {
    const units = Math.max(0, Number(room.present_units) - Number(room.previous_units));
    let eb;
    if (threshold > 0 && units > threshold) {
        eb = threshold * rate + (units - threshold) * highRate;
    } else {
        eb = units * rate;
    }
    const total =
        eb +
        Number(room.gas_bill) +
        Number(room.service_charge) +
        Number(room.rent) +
        Number(room.previous_due) -
        Number(room.paid);
    return {
        units_used: units,
        electric_bill: Math.round(eb * 100) / 100,
        total_bill: Math.round(total * 100) / 100,
    };
}

// ── Editable number cell (desktop table) ──────────────────────────────────────
function NumCell({ value, onChange, highlight }) {
    return (
        <td>
            <input
                type="number"
                value={value}
                onChange={(e) => onChange(Number(e.target.value))}
                style={highlight ? { borderColor: 'var(--accent)', color: 'var(--accent2)' } : {}}
            />
        </td>
    );
}

// ── Desktop building table (hidden on mobile via CSS) ─────────────────────────
function BuildingTable({ building, rooms, onChange, rate, highRate, threshold }) {
    return (
        <div className="table-wrap">
            <div className="building-label">🏠 {building.label} — House {building.id}</div>
            <table>
                <thead>
                    <tr>
                        <th>Room</th>
                        <th>Meter No.</th>
                        <th>Prev. Units</th>
                        <th style={{ color: 'var(--accent2)' }}>Present Units ✏️</th>
                        <th>Used</th>
                        <th>Elec. Bill</th>
                        <th>Gas</th>
                        <th>Service</th>
                        <th>Rent</th>
                        <th>Prev. Due</th>
                        <th>Paid</th>
                        <th>Total</th>
                        <th>Comments</th>
                    </tr>
                </thead>
                <tbody>
                    {rooms.map((room) => {
                        const calc = calcRoom(room, rate, highRate, threshold);
                        return (
                            <tr key={room.room_no}>
                                <td><strong>{room.room_no}</strong></td>
                                <td style={{ color: 'var(--muted)' }}>{room.meter_no || '—'}</td>
                                <td style={{ color: 'var(--muted)' }}>{room.previous_units}</td>
                                <NumCell
                                    value={room.present_units}
                                    highlight
                                    onChange={(v) => onChange(building.id, room.room_no, 'present_units', v)}
                                />
                                <td className="derived">{calc.units_used}</td>
                                <td className="derived">৳{calc.electric_bill}</td>
                                <NumCell value={room.gas_bill} onChange={(v) => onChange(building.id, room.room_no, 'gas_bill', v)} />
                                <NumCell value={room.service_charge} onChange={(v) => onChange(building.id, room.room_no, 'service_charge', v)} />
                                <NumCell value={room.rent} onChange={(v) => onChange(building.id, room.room_no, 'rent', v)} />
                                <NumCell value={room.previous_due} onChange={(v) => onChange(building.id, room.room_no, 'previous_due', v)} />
                                <NumCell value={room.paid} onChange={(v) => onChange(building.id, room.room_no, 'paid', v)} />
                                <td className="total">৳{calc.total_bill}</td>
                                <td>
                                    <input
                                        type="text"
                                        value={room.comments}
                                        onChange={(e) => onChange(building.id, room.room_no, 'comments', e.target.value)}
                                        style={{ minWidth: 100 }}
                                        placeholder="Optional note…"
                                    />
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}

// ── Mobile room card (shown on mobile via CSS) ────────────────────────────────
function RoomCard({ room, buildingId, onChange, rate, highRate, threshold }) {
    const [expanded, setExpanded] = useState(false);
    const calc = calcRoom(room, rate, highRate, threshold);

    const field = (label, field, highlight = false) => (
        <div className={`room-card-field${highlight ? ' highlight' : ''}`}>
            <label>{label}</label>
            <input
                type="number"
                value={room[field]}
                onChange={(e) => onChange(buildingId, room.room_no, field, Number(e.target.value))}
            />
        </div>
    );

    return (
        <div className="room-card">
            <div className="room-card-header">
                <h3>
                    {room.room_no}
                    {room.meter_no && <span style={{ color: 'var(--muted)', fontWeight: 400, fontSize: '0.8rem', marginLeft: 6 }}>#{room.meter_no}</span>}
                </h3>
                <div className="room-card-total">৳{calc.total_bill}</div>
            </div>

            {/* Primary fields — always visible */}
            <div className="room-card-fields">
                <div className="room-card-field">
                    <label>Prev. Units</label>
                    <input type="number" value={room.previous_units} readOnly
                        style={{ opacity: 0.6, cursor: 'default' }} />
                </div>
                {field('Present Units ✏️', 'present_units', true)}
            </div>

            {/* Derived values */}
            <div className="room-card-derived">
                <div>Used: <span>{calc.units_used}</span></div>
                <div>Elec: <span>৳{calc.electric_bill}</span></div>
            </div>

            {/* Expandable details */}
            <button className="room-card-expand" onClick={() => setExpanded(!expanded)}>
                {expanded ? '▲ Hide details' : '▼ More details'}
            </button>

            {expanded && (
                <div className="room-card-details">
                    <div className="room-card-fields">
                        {field('Rent', 'rent')}
                        {field('Gas Bill', 'gas_bill')}
                        {field('Service Charge', 'service_charge')}
                        {field('Previous Due', 'previous_due')}
                        {field('Paid', 'paid')}
                        <div className="room-card-field">
                            <label>Comments</label>
                            <input
                                type="text"
                                value={room.comments}
                                onChange={(e) => onChange(buildingId, room.room_no, 'comments', e.target.value)}
                                placeholder="Note…"
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// ── Mobile building card list ─────────────────────────────────────────────────
function BuildingCards({ building, rooms, onChange, rate, highRate, threshold }) {
    return (
        <div className="room-cards">
            {rooms.map((room) => (
                <RoomCard
                    key={room.room_no}
                    room={room}
                    buildingId={building.id}
                    onChange={onChange}
                    rate={rate}
                    highRate={highRate}
                    threshold={threshold}
                />
            ))}
        </div>
    );
}

// ── Main MonthEditor page ─────────────────────────────────────────────────────
export default function MonthEditor() {
    const { year, month } = useParams();
    const navigate = useNavigate();
    const toast = useToast();

    const [data, setData] = useState(null);
    const [rooms, setRooms] = useState([]);
    const [rate, setRate] = useState(9);
    const [highRate, setHighRate] = useState(10);
    const [threshold, setThreshold] = useState(0);
    const [saving, setSaving] = useState(false);
    const [generatingPdf, setGeneratingPdf] = useState(false);
    const [dirty, setDirty] = useState(false);

    useEffect(() => {
        getMonth(year, month)
            .then((res) => {
                setData(res.data);
                setRooms(res.data.rooms.map((r) => ({ ...r })));
                setRate(res.data.electricity_rate);
                setHighRate(res.data.electricity_rate_high);
                setThreshold(res.data.rate_threshold_units);
            })
            .catch(() => toast('Failed to load month data', 'error'));
    }, [year, month]);

    const handleCellChange = useCallback((buildingNum, roomNo, field, value) => {
        setRooms((prev) =>
            prev.map((r) =>
                r.building_num === buildingNum && r.room_no === roomNo
                    ? { ...r, [field]: value }
                    : r
            )
        );
        setDirty(true);
    }, []);

    const handleSave = async () => {
        setSaving(true);
        try {
            await updateRate(year, month, {
                electricity_rate: rate,
                electricity_rate_high: highRate,
                rate_threshold_units: threshold,
            });
            const saved = await updateRooms(year, month, rooms);
            setRooms(saved.data.map((r) => ({ ...r })));
            setDirty(false);
            toast('Saved successfully!');
        } catch {
            toast('Save failed. Please try again.', 'error');
        } finally {
            setSaving(false);
        }
    };

    const handleGeneratePdf = async () => {
        if (dirty) {
            toast('Please save your changes before generating PDF.', 'error');
            return;
        }
        setGeneratingPdf(true);
        try {
            await generatePdf(year, month);
            toast('PDF downloaded!');
        } catch {
            toast('PDF generation failed.', 'error');
        } finally {
            setGeneratingPdf(false);
        }
    };

    if (!data) {
        return (
            <div className="page">
                <p className="text-muted">Loading month data…</p>
            </div>
        );
    }

    // Group rooms by building
    const buildingGroups = {};
    rooms.forEach((r) => {
        if (!buildingGroups[r.building_num]) buildingGroups[r.building_num] = [];
        buildingGroups[r.building_num].push(r);
    });

    // Overall totals
    const grandTotal = rooms.reduce((sum, r) => {
        const c = calcRoom(r, rate, highRate, threshold);
        return sum + c.total_bill;
    }, 0);

    return (
        <div className="page">
            {/* ── Header ── */}
            <div className="flex justify-between items-center wrap gap-3">
                <div className="page-header">
                    <h1>{data.month_name} {year}</h1>
                    <p className="text-muted">
                        Edit present units and other fields. Totals update live.
                        {dirty && <span style={{ color: 'var(--warning)', marginLeft: 8 }}>● Unsaved</span>}
                    </p>
                </div>
                {/* Desktop actions (hidden on mobile via CSS) */}
                <div className="desktop-actions">
                    <button className="btn btn-ghost" onClick={() => navigate('/')}>← Dashboard</button>
                    <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                        {saving ? '⏳ Saving…' : '💾 Save'}
                    </button>
                    <button className="btn btn-success" onClick={handleGeneratePdf} disabled={generatingPdf || dirty}>
                        {generatingPdf ? '⏳ Generating…' : '📄 Generate PDF'}
                    </button>
                </div>
            </div>

            {/* ── Rate settings ── */}
            <div className="rate-bar">
                <div className="field">
                    <label>Base Rate (৳/unit)</label>
                    <input type="number" value={rate} min={1} step={0.5} style={{ width: 100 }}
                        onChange={(e) => { setRate(+e.target.value); setDirty(true); }} />
                </div>
                <div className="field">
                    <label>High Rate (৳/unit)</label>
                    <input type="number" value={highRate} min={1} step={0.5} style={{ width: 100 }}
                        onChange={(e) => { setHighRate(+e.target.value); setDirty(true); }} />
                </div>
                <div className="field">
                    <label>Threshold (units, 0 = flat rate)</label>
                    <input type="number" value={threshold} min={0} style={{ width: 110 }}
                        onChange={(e) => { setThreshold(+e.target.value); setDirty(true); }} />
                </div>
                <div className="grand-total-desktop" style={{ marginLeft: 'auto', alignSelf: 'flex-end' }}>
                    <div className="text-muted text-sm">Grand Total</div>
                    <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#4ade80' }}>
                        ৳{Math.round(grandTotal).toLocaleString()}
                    </div>
                </div>
                {/* Mobile-visible grand total (always inside rate bar) */}
                <div style={{ textAlign: 'center', padding: '0.25rem 0' }} className="mobile-only-total">
                    <span className="text-muted text-sm">Grand Total:</span>
                    <span style={{ fontSize: '1.2rem', fontWeight: 800, color: '#4ade80', marginLeft: 8 }}>
                        ৳{Math.round(grandTotal).toLocaleString()}
                    </span>
                </div>
            </div>

            {/* ── Building tables/cards ── */}
            {[220, 226].map((bldgId) => {
                const bldgRooms = buildingGroups[bldgId] || [];
                const bldgTotal = bldgRooms.reduce((s, r) => s + calcRoom(r, rate, highRate, threshold).total_bill, 0);
                const fakeBuilding = { id: bldgId, label: `House ${bldgId}` };
                return (
                    <div key={bldgId} style={{ marginTop: '1.75rem' }}>
                        <div className="flex justify-between items-center">
                            <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--accent2)' }}>
                                🏠 House {bldgId}
                            </h2>
                            <span className="badge badge-green">Total: ৳{Math.round(bldgTotal).toLocaleString()}</span>
                        </div>
                        {/* Desktop table */}
                        <BuildingTable
                            building={fakeBuilding}
                            rooms={bldgRooms}
                            onChange={handleCellChange}
                            rate={rate}
                            highRate={highRate}
                            threshold={threshold}
                        />
                        {/* Mobile cards */}
                        <BuildingCards
                            building={fakeBuilding}
                            rooms={bldgRooms}
                            onChange={handleCellChange}
                            rate={rate}
                            highRate={highRate}
                            threshold={threshold}
                        />
                    </div>
                );
            })}

            {/* ── Mobile sticky action bar ── */}
            <div className="mobile-action-bar">
                <button className="btn btn-ghost btn-sm" onClick={() => navigate('/')}>← Back</button>
                <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                    {saving ? '⏳' : '💾 Save'}
                </button>
                <button className="btn btn-success" onClick={handleGeneratePdf} disabled={generatingPdf || dirty}>
                    {generatingPdf ? '⏳' : '📄 PDF'}
                </button>
            </div>
        </div>
    );
}
