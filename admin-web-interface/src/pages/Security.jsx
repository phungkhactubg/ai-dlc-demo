import React, { useState } from 'react';
import {
    ShieldAlert,
    ShieldCheck,
    AlertTriangle,
    Video,
    User,
    MapPin,
    ExternalLink,
    Ban,
    Check,
    Search,
    MoreHorizontal,
    Zap,
    Power,
    RotateCcw,
    ShieldOff
} from 'lucide-react';

const fraudQueue = [
    { id: 'TX-38491', time: '11:42:01', user: 'J. Carter', amount: '$45.20', vehicle: 'AV-201', method: 'Amex', score: 0.95, status: 'Flagged' },
    { id: 'TX-38490', time: '11:41:45', user: 'M. Lee', amount: '$78.10', vehicle: 'AV-503', method: 'Visa', score: 0.82, status: 'Flagged' },
    { id: 'TX-38489', time: '11:41:35', user: 'S. Rodriguez', amount: '$12.50', vehicle: 'AV-112', method: 'Cash', score: 0.35, status: 'Approved' },
    { id: 'TX-38488', time: '11:41:30', user: 'J. Carter', amount: '$45.20', vehicle: 'AV-201', method: 'Amex', score: 0.35, status: 'Approved' },
    { id: 'TX-38487', time: '11:41:30', user: 'M. Lee', amount: '$78.10', vehicle: 'AV-503', method: 'Visa', score: 0.25, status: 'Approved' },
    { id: 'TX-38486', time: '11:41:30', user: 'S. Rodriguez', amount: '$12.50', vehicle: 'AV-112', method: 'Cash', score: 0.15, status: 'Approved' },
];

const Security = () => {
    const [activeAlert, setActiveAlert] = useState(true);

    const getRiskColor = (score) => {
        if (score >= 0.8) return '#ef4444';
        if (score >= 0.5) return '#f97316';
        return '#10b981';
    };

    return (
        <div className="security-container animate-fade-in">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Security & Fraud Hub</h1>
                    <p className="page-subtitle">Mission-critical safety monitoring and transaction risk management.</p>
                </div>
                <div className="flex gap-2">
                    <div className="status-label flex items-center gap-2 px-3 py-1 bg-green-500/10 text-green-500 rounded-lg text-sm font-medium">
                        <span className="dot bg-green-500 w-2 h-2 rounded-full"></span>
                        Guardian Active
                    </div>
                </div>
            </div>

            <div className="security-stats grid-4 mb-6">
                <div className="stat-pill glass">
                    <span className="label">Gateway Health</span>
                    <span className="value text-success">99.98%</span>
                </div>
                <div className="stat-pill glass">
                    <span className="label">Held (Fraud)</span>
                    <span className="value text-warning">12</span>
                </div>
                <div className="stat-pill glass">
                    <span className="label">PCI-DSS Status</span>
                    <span className="value text-primary">Compliant</span>
                </div>
                <div className="stat-pill glass">
                    <span className="label">Failover Events</span>
                    <span className="value text-tertiary">0 (Last 24h)</span>
                </div>
            </div>

            <div className="security-grid">
                <div className="safety-monitor-section">
                    <div className="glass-card monitor-card">
                        <div className="section-header mb-6">
                            <h3 className="flex items-center gap-2">
                                <Video size={18} />
                                AV Fleet Safety Monitor (RHS-SRS)
                            </h3>
                            <span className="text-tertiary text-sm">UTC 11:43:05</span>
                        </div>

                        {activeAlert ? (
                            <div className="alert-card animate-pulse-border">
                                <div className="alert-header">
                                    <div className="alert-badge">
                                        <AlertTriangle size={16} />
                                        <span>FLASHING ALERT (BL-007)</span>
                                    </div>
                                    <button onClick={() => setActiveAlert(false)} className="close-btn">&times;</button>
                                </div>
                                <div className="alert-body">
                                    <div className="alert-info">
                                        <div className="icon-box red">
                                            <Zap size={24} />
                                        </div>
                                        <div>
                                            <h4 className="alert-title">Safety Stop — Emergency Brake</h4>
                                            <p className="alert-meta">Vehicle: <strong>AV-412</strong> | Status: <strong>Safety_Stop</strong></p>
                                        </div>
                                    </div>
                                    <div className="video-placeholder">
                                        <div className="video-overlay">
                                            <span className="status-tag">STATIONARY • STATE_11</span>
                                        </div>
                                        <div className="scan-line"></div>
                                        <p className="placeholder-text">LIVE AV CAMERA FEED (MISSION BAY)</p>
                                    </div>
                                    <div className="remote-actions">
                                        <h5>Saga Rollback / Intervention</h5>
                                        <div className="action-buttons">
                                            <button className="btn-action red">REMOTE STOP</button>
                                            <button className="btn-action yellow">OVERRIDE</button>
                                            <button className="btn-action blue">PARKING</button>
                                            <button className="btn-action ghost">POLICE</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="empty-state">
                                <ShieldCheck size={48} className="text-green-500 mb-4 opacity-50" />
                                <p>All vehicles operating within safety parameters.</p>
                            </div>
                        )}
                    </div>
                </div>

                <div className="fraud-queue-section">
                    <div className="glass-card queue-card">
                        <div className="section-header mb-4">
                            <h3 className="flex items-center gap-2">
                                <ShieldOff size={18} />
                                PCI-DSS Review Queue (PAY-BL-008)
                            </h3>
                            <div className="search-small glass-card">
                                <Search size={14} className="text-tertiary" />
                                <input type="text" placeholder="Search..." />
                            </div>
                        </div>

                        <div className="queue-table">
                            <table>
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Reasoning</th>
                                        <th>Gateway</th>
                                        <th>Score</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {fraudQueue.map(item => (
                                        <tr key={item.id}>
                                            <td><span className="id-tag">{item.id}</span></td>
                                            <td className="text-xs">Velocached / IP Mismatch</td>
                                            <td>VNPay</td>
                                            <td>
                                                <div className="flex items-center gap-2">
                                                    <div className="risk-bar-bg">
                                                        <div className="risk-bar-fill" style={{ width: `${item.score * 100}%`, backgroundColor: getRiskColor(item.score) }}></div>
                                                    </div>
                                                    <span className="score-text" style={{ color: getRiskColor(item.score) }}>{item.score}</span>
                                                </div>
                                            </td>
                                            <td>
                                                <div className="flex gap-2">
                                                    <button className="action-btn-sm check"><Check size={14} /></button>
                                                    <button className="action-btn-sm ban"><Ban size={14} /></button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <style jsx>{`
        .security-container { display: flex; flex-direction: column; gap: 1.5rem; }
        .security-grid { display: grid; grid-template-columns: 2fr 3fr; gap: 1.5rem; height: calc(100vh - 180px); }

        .monitor-card, .queue-card { padding: 1.5rem; height: 100%; display: flex; flex-direction: column; }
        
        .alert-card { background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 1rem; overflow: hidden; }
        .animate-pulse-border { animation: pulse-border 2s infinite; }
        @keyframes pulse-border { 0% { border-color: rgba(239, 68, 68, 0.2); } 50% { border-color: rgba(239, 68, 68, 0.6); box-shadow: 0 0 15px rgba(239, 68, 68, 0.2); } 100% { border-color: rgba(239, 68, 68, 0.2); } }

        .alert-header { padding: 0.75rem 1rem; background: rgba(239, 68, 68, 0.1); display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(239, 68, 68, 0.2); }
        .alert-badge { display: flex; align-items: center; gap: 0.5rem; color: #ef4444; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em; }
        .close-btn { background: transparent; color: var(--text-tertiary); font-size: 1.25rem; line-height: 1; }

        .alert-body { padding: 1.25rem; display: flex; flex-direction: column; gap: 1.25rem; }
        .alert-info { display: flex; gap: 1rem; align-items: center; }
        .icon-box { width: 56px; height: 56px; border-radius: 1rem; display: flex; align-items: center; justify-content: center; }
        .icon-box.red { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
        .alert-title { font-size: 1.125rem; font-weight: 600; color: #ef4444; margin-bottom: 0.25rem; }
        .alert-meta { font-size: 0.8125rem; color: var(--text-secondary); }

        .video-placeholder { aspect-ratio: 16/9; background: #000; border-radius: 0.75rem; position: relative; display: flex; align-items: center; justify-content: center; overflow: hidden; border: 2px solid #1e1e1e; }
        .video-overlay { position: absolute; top: 1rem; left: 1rem; }
        .status-tag { background: rgba(239, 68, 68, 0.9); color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.625rem; font-weight: 700; }
        .placeholder-text { font-size: 0.75rem; color: #334155; font-family: monospace; letter-spacing: 0.1em; }
        .scan-line { position: absolute; width: 100%; height: 2px; background: rgba(0, 242, 148, 0.1); top: 0; animation: scan 3s linear infinite; }
        @keyframes scan { from { top: 0; } to { top: 100%; } }
        
        .video-controls { position: absolute; bottom: 0.5rem; right: 0.5rem; display: flex; gap: 0.5rem; }
        .ctrl-btn { background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1); color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.625rem; display: flex; align-items: center; gap: 0.25rem; }
        .ctrl-btn.active { background: #1e293b; border-color: rgba(255,255,255,0.2); }

        .remote-actions h5 { font-size: 0.75rem; text-transform: uppercase; color: var(--text-tertiary); margin-bottom: 0.75rem; letter-spacing: 0.05em; }
        .action-buttons { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
        .btn-action { padding: 0.625rem; border-radius: 0.5rem; font-size: 0.75rem; font-weight: 600; font-family: var(--font-display); }
        .btn-action.red { background: #ef4444; color: white; }
        .btn-action.yellow { background: #f59e0b; color: white; }
        .btn-action.blue { background: #3b82f6; color: white; }
        .btn-action.ghost { border: 1px solid var(--glass-border); color: var(--text-primary); }

        .error-log { font-family: monospace; font-size: 0.6875rem; color: #94a3b8; background: #0b1120; padding: 0.75rem; border-radius: 0.5rem; border: 1px solid #1e293b; }

        .search-small { display: flex; align-items: center; gap: 0.5rem; padding: 0.375rem 0.75rem; border-radius: 0.5rem; }
        .search-small input { background: transparent; border: none; font-size: 0.75rem; color: white; width: 80px; outline: none; }
        
        .queue-table { flex: 1; margin-top: 1rem; overflow-y: auto; }
        .queue-table table { width: 100%; border-collapse: collapse; }
        .queue-table th { font-size: 0.6875rem; color: var(--text-tertiary); text-transform: uppercase; padding: 0.75rem; border-bottom: 1px solid var(--glass-border); text-align: left; }
        .queue-table td { font-size: 0.75rem; padding: 0.75rem; border-bottom: 1px solid var(--glass-border); }
        .id-tag { font-family: monospace; background: rgba(255,255,255,0.05); padding: 0.125rem 0.375rem; border-radius: 0.25rem; font-size: 0.75rem; }
        
        .risk-bar-bg { width: 48px; height: 6px; background: var(--bg-tertiary); border-radius: 3px; overflow: hidden; }
        .risk-bar-fill { height: 100%; border-radius: 3px; }
        .score-text { font-weight: 700; font-size: 0.75rem; }

        .action-btn-sm { width: 28px; height: 28px; border-radius: 0.375rem; display: flex; align-items: center; justify-content: center; }
        .action-btn-sm.check { background: rgba(16, 185, 129, 0.1); color: #10b981; }
        .action-btn-sm.ban { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
        .action-btn-sm.ghost { background: var(--bg-tertiary); color: var(--text-tertiary); }

        .queue-footer { padding-top: 1.5rem; text-align: center; }
        .view-all-btn { font-size: 0.8125rem; color: var(--accent-primary); background: transparent; display: flex; align-items: center; gap: 0.5rem; margin: 0 auto; }
      `}</style>
        </div>
    );
};

export default Security;
