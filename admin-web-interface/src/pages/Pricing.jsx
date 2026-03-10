import React, { useState } from 'react';
import { MapContainer, TileLayer, Polygon, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import {
    Zap,
    Settings2,
    Calendar,
    ChevronRight,
    Save,
    Info
} from 'lucide-react';

const eventRules = [
    { id: 1, name: 'Lunar New Year', status: 'Active', multiplier: '+1.0x', date: '10-18 Feb 2024' },
    { id: 2, name: 'Hanoi Marathon', status: 'Active', multiplier: '+0.8x', date: '14 Apr 2024' },
    { id: 3, name: 'Music Festival', status: 'Active', multiplier: '+1.2x', date: '25 May 2024' },
    { id: 4, name: 'Heavy Rain Alert', status: 'Draft', multiplier: '+0.5x', date: 'Auto-trigger' },
];

const hexagons = [
    { id: 1, coords: [[21.03, 105.84], [21.035, 105.845], [21.035, 105.855], [21.03, 105.86], [21.025, 105.855], [21.025, 105.845]], surge: 2.7, label: 'Hoan Kiem Peak' },
    { id: 2, coords: [[21.04, 105.82], [21.045, 105.825], [21.045, 105.835], [21.04, 105.84], [21.035, 105.835], [21.035, 105.825]], surge: 1.4, label: 'Ba Dinh' },
    { id: 3, coords: [[21.02, 105.85], [21.025, 105.855], [21.025, 105.865], [21.02, 105.87], [21.015, 105.865], [21.015, 105.855]], surge: 1.4, label: 'Bclanh' },
];

const Pricing = () => {
    const [multiplier, setMultiplier] = useState(1.8);

    const getSurgeColor = (surge) => {
        if (surge >= 2.5) return '#ef4444';
        if (surge >= 2.0) return '#f97316';
        if (surge >= 1.5) return '#eab308';
        return '#3b82f6';
    };

    return (
        <div className="pricing-container animate-fade-in">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Fare & Pricing Engine</h1>
                    <p className="page-subtitle">Dynamic surge multiplier and event-based pricing configuration.</p>
                </div>
                <div className="flex gap-2">
                    <button className="glass-card flex items-center gap-2 px-4 py-2 text-sm">
                        <Settings2 size={16} />
                        <span>Global Settings</span>
                    </button>
                    <button className="btn-primary flex items-center gap-2">
                        <Save size={18} />
                        <span>Publish Changes</span>
                    </button>
                </div>
            </div>

            <div className="pricing-layout">
                <div className="glass-card map-section">
                    <div className="section-header">
                        <h3>Surge Map — Hanoi Operations</h3>
                        <div className="demand-index">
                            <span>Low</span>
                            <div className="gradient-bar"></div>
                            <span>High</span>
                        </div>
                    </div>
                    <div className="map-wrapper">
                        <MapContainer center={[21.03, 105.85]} zoom={13} style={{ height: '100%', width: '100%' }}>
                            <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
                            {hexagons.map(hex => (
                                <Polygon
                                    key={hex.id}
                                    positions={hex.coords}
                                    pathOptions={{
                                        fillColor: getSurgeColor(hex.surge),
                                        fillOpacity: 0.4,
                                        color: getSurgeColor(hex.surge),
                                        weight: 2
                                    }}
                                >
                                    <Popup>
                                        <strong>{hex.label}</strong><br />
                                        Current Surge: {hex.surge}x
                                    </Popup>
                                </Polygon>
                            ))}
                        </MapContainer>
                    </div>
                </div>

                <div className="sidebar-config">
                    <div className="glass-card config-card mb-6">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="flex items-center gap-2">
                                <Zap size={18} className="text-yellow-400" />
                                Surge Multiplier Caps
                            </h3>
                            <span className="badge active">LIVE</span>
                        </div>

                        <div className="config-item">
                            <div className="flex justify-between mb-2">
                                <label>Citywide Default</label>
                                <span className="value">1.8x</span>
                            </div>
                            <input
                                type="range"
                                min="1" max="3" step="0.1"
                                value={multiplier}
                                onChange={(e) => setMultiplier(e.target.value)}
                                className="surge-slider"
                            />
                        </div>
                    </div>

                    <div className="glass-card revenue-card mb-6">
                        <h3 className="flex items-center gap-2 mb-4">
                            <Info size={18} className="text-blue-400" />
                            Revenue Share (FPE-SRS)
                        </h3>
                        <div className="revenue-split">
                            <div className="split-row">
                                <span>Platform Fee</span>
                                <span className="font-bold">5% (Fixed)</span>
                            </div>
                            <div className="split-row">
                                <span>Tenant Margin</span>
                                <span className="font-bold">95%</span>
                            </div>
                            <div className="progress-mini mt-2">
                                <div className="progress-bar" style={{ width: '5%', background: 'var(--primary)' }}></div>
                                <div className="progress-bar" style={{ width: '95%', background: 'var(--accent-secondary)' }}></div>
                            </div>
                        </div>
                    </div>

                    <div className="glass-card events-card">
                        <h3 className="flex items-center gap-2 mb-4">
                            <Calendar size={18} />
                            Promotion Rules (BL-009)
                        </h3>
                        <div className="rules-list">
                            {eventRules.map(rule => (
                                <div key={rule.id} className="rule-item">
                                    <div className="rule-info">
                                        <p className="rule-name">{rule.name}</p>
                                        <p className="rule-date">{rule.date}</p>
                                    </div>
                                    <div className="rule-action text-right">
                                        <p className="rule-multiplier">{rule.multiplier}</p>
                                        <button className="edit-btn">Edit</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <style jsx>{`
        .pricing-container { display: flex; flex-direction: column; gap: 1.5rem; }
        .pricing-layout { display: grid; grid-template-columns: 1fr 380px; gap: 1.5rem; height: calc(100vh - 180px); }

        .map-section { padding: 1.5rem; display: flex; flex-direction: column; }
        .map-wrapper { flex: 1; border-radius: 1rem; overflow: hidden; margin-top: 1rem; position: relative; }

        .sidebar-config { display: flex; flex-direction: column; gap: 1.5rem; }
        .config-card, .events-card { padding: 1.5rem; }

        .demand-index { display: flex; align-items: center; gap: 0.75rem; font-size: 0.75rem; color: var(--text-secondary); }
        .gradient-bar { width: 120px; height: 8px; border-radius: 4px; background: linear-gradient(to right, #3b82f6, #eab308, #f97316, #ef4444); }

        .config-item label { font-size: 0.875rem; font-weight: 500; }
        .config-item .value { font-weight: 600; color: var(--accent-secondary); }

        .surge-slider { width: 100%; -webkit-appearance: none; background: var(--bg-tertiary); height: 6px; border-radius: 3px; outline: none; }
        .surge-slider::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; width: 18px; height: 18px; border-radius: 50%; background: var(--accent-primary); cursor: pointer; border: 2px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.5); }

        .toggle { width: 40px; height: 20px; background: var(--bg-tertiary); border-radius: 10px; position: relative; cursor: pointer; }
        .toggle.active { background: var(--accent-primary); }
        .toggle:after { content: ''; position: absolute; left: 2px; top: 2px; width: 16px; height: 16px; background: white; border-radius: 50%; transition: all 0.2s; }
        .toggle.active:after { left: 22px; }

        .rules-list { display: flex; flex-direction: column; gap: 1rem; }
        .rule-item { display: flex; justify-content: space-between; align-items: center; padding-bottom: 1rem; border-bottom: 1px solid var(--glass-border); }
        .rule-name { font-size: 0.875rem; font-weight: 500; }
        .rule-date { font-size: 0.75rem; color: var(--text-secondary); }
        .rule-multiplier { font-weight: 600; color: var(--accent-secondary); font-size: 0.875rem; }
        .edit-btn { font-size: 0.75rem; color: var(--accent-primary); background: transparent; }
      `}</style>
        </div>
    );
};

export default Pricing;
