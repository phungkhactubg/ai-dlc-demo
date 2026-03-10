import React, { useState } from 'react';
import {
    CheckCircle2,
    Circle,
    Clock,
    AlertCircle,
    MoreVertical,
    ExternalLink,
    Plus
} from 'lucide-react';

const sagaSteps = [
    { id: '1', name: 'Identity Setup', service: 'SSC', status: 'completed', time: '10:00 AM' },
    { id: '2', name: 'Billing & Subscription', service: 'BMS', status: 'completed', time: '10:15 AM' },
    { id: '3', name: 'Developer API Keys', service: 'DPE', status: 'in-progress', time: '10:30 AM' },
    { id: '4', name: 'Fleet Allocation', service: 'VMS', status: 'upcoming', time: '10:45 AM' },
];

const logs = [
    { time: '10:32:01', id: 'EVT_567', service: 'SSC', action: 'Token Validation', status: 'OK' },
    { time: '10:32:02', id: 'EVT_568', service: 'BMS', action: 'Plan Check', status: 'OK' },
    { time: '10:32:04', id: 'EVT_569', service: 'DPE', action: 'Key Generation', status: 'SUCCESS' },
    { time: '10:32:05', id: 'EVT_570', service: 'SSC', action: 'Service Update', status: 'PENDING' },
];

const Tenants = () => {
    const [showSaga, setShowSaga] = useState(true);

    return (
        <div className="tenants-container animate-fade-in">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Tenant Management</h1>
                    <p className="page-subtitle">Onboard and manage enterprise fleet operators.</p>
                </div>
                <button className="btn-primary flex items-center gap-2">
                    <Plus size={18} />
                    <span>Onboard New Tenant</span>
                </button>
            </div>

            <div className="page-grid">
                <div className="glass-card tenant-list-section">
                    <div className="section-header">
                        <h3>Active Tenants</h3>
                    </div>
                    <div className="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Tenant Name</th>
                                    <th>ID</th>
                                    <th>Subscription</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr className="active-row">
                                    <td>
                                        <div className="flex items-center gap-2">
                                            <div className="avatar">AL</div>
                                            <span>Aura Logistics</span>
                                        </div>
                                    </td>
                                    <td><code className="code">AL-78432</code></td>
                                    <td>Enterprise</td>
                                    <td><span className="badge processing">Onboarding</span></td>
                                    <td><button className="icon-btn"><MoreVertical size={16} /></button></td>
                                </tr>
                                <tr>
                                    <td>
                                        <div className="flex items-center gap-2">
                                            <div className="avatar bg-blue">VM</div>
                                            <span>VinaMove Corp</span>
                                        </div>
                                    </td>
                                    <td><code className="code">VM-10293</code></td>
                                    <td>Growth</td>
                                    <td><span className="badge active">Active</span></td>
                                    <td><button className="icon-btn"><MoreVertical size={16} /></button></td>
                                </tr>
                                <tr>
                                    <td>
                                        <div className="flex items-center gap-2">
                                            <div className="avatar bg-green">SF</div>
                                            <span>SwiftFleet</span>
                                        </div>
                                    </td>
                                    <td><code className="code">SF-99212</code></td>
                                    <td>Starter</td>
                                    <td><span className="badge active">Active</span></td>
                                    <td><button className="icon-btn"><MoreVertical size={16} /></button></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                {showSaga && (
                    <div className="glass-card saga-section">
                        <div className="section-header">
                            <h3>Tenant Context: Aura Logistics</h3>
                        </div>

                        <div className="tenant-meta-grid">
                            <div className="meta-box glass-card">
                                <span>Quota Usage</span>
                                <div className="quota-bar"><div className="fill" style={{ width: '78%' }}></div></div>
                                <small>78% used (Warning at 80%)</small>
                            </div>
                            <div className="meta-box glass-card">
                                <span>Feature Flags</span>
                                <p className="text-xs text-secondary">AV_POOLING: ON<br />INTER_PROVINCE: OFF</p>
                            </div>
                        </div>

                        <div className="saga-workflow mt-4">
                            <h4>Onboarding Saga (TMS-BL-001)</h4>
                            {sagaSteps.map((step, idx) => (
                                <div key={step.id} className="saga-step">
                                    <div className={`step-connector ${idx === 0 ? 'first' : ''} ${step.status}`}></div>
                                    <div className={`step-icon ${step.status}`}>
                                        {step.status === 'completed' && <CheckCircle2 size={18} />}
                                        {step.status === 'in-progress' && <div className="pulse"></div>}
                                        {step.status === 'upcoming' && <Circle size={18} />}
                                    </div>
                                    <div className="step-info">
                                        <p className="step-name">{step.name}</p>
                                        <p className="step-meta">{step.service} • {step.status === 'in-progress' ? 'Processing...' : step.time}</p>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="technical-logs">
                            <h4>Microservices Ledger (Immutable)</h4>
                            <div className="log-table">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Time</th>
                                            <th>Service</th>
                                            <th>Action</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {logs.map((log, i) => (
                                            <tr key={i}>
                                                <td>{log.time}</td>
                                                <td><span className="service-tag">{log.service}</span></td>
                                                <td>{log.action}</td>
                                                <td className={log.status === 'OK' || log.status === 'SUCCESS' ? 'text-success' : 'text-warning'}>
                                                    {log.status}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <style jsx>{`
        .tenants-container {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .page-title { font-size: 1.5rem; margin-bottom: 0.25rem; }
        .page-subtitle { color: var(--text-secondary); font-size: 0.875rem; }

        .page-grid {
          display: grid;
          grid-template-columns: 1fr 400px;
          gap: 1.5rem;
          min-height: 600px;
        }

        .tenant-list-section { padding: 1.5rem; }
        .saga-section { padding: 1.5rem; display: flex; flex-direction: column; gap: 1.5rem; }

        .table-container { margin-top: 1rem; }
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; padding: 1rem; color: var(--text-tertiary); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--glass-border); }
        td { padding: 1rem; font-size: 0.875rem; border-bottom: 1px solid var(--glass-border); }

        .avatar { width: 32px; height: 32px; border-radius: 0.5rem; background: var(--accent-primary); display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.75rem; }
        .bg-blue { background: #3b82f6; }
        .bg-green { background: #10b981; }

        .code { font-family: monospace; background: rgba(255,255,255,0.05); padding: 0.2rem 0.4rem; border-radius: 0.25rem; font-size: 0.8125rem; }
        
        .badge { padding: 0.25rem 0.625rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 500; }
        .badge.active { background: rgba(16, 185, 129, 0.1); color: #10b981; }
        .badge.processing { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }

        .active-row { background: rgba(0, 71, 186, 0.05); }

        .saga-workflow { display: flex; flex-direction: column; gap: 0; padding-left: 0.5rem; }
        .saga-step { display: flex; gap: 1.5rem; position: relative; padding-bottom: 1.5rem; }
        
        .step-icon { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; z-index: 10; background: var(--bg-tertiary); }
        .step-icon.completed { background: var(--accent-secondary); color: var(--bg-primary); }
        .step-icon.in-progress { border: 2px solid var(--accent-primary); background: var(--bg-primary); }
        
        .step-connector { position: absolute; left: 15px; top: 0; width: 2px; height: 100%; background: var(--glass-border); z-index: 1; }
        .step-connector.completed { background: var(--accent-secondary); }
        .step-connector.first { top: 16px; height: calc(100% - 16px); }

        .pulse { width: 10px; height: 10px; background: var(--accent-primary); border-radius: 50%; box-shadow: 0 0 0 0 rgba(0, 71, 186, 0.7); animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 71, 186, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(0, 71, 186, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 71, 186, 0); } }

        .step-name { font-size: 0.875rem; font-weight: 600; margin-bottom: 0.125rem; }
        .step-meta { font-size: 0.75rem; color: var(--text-secondary); }

        .technical-logs { display: flex; flex-direction: column; gap: 0.75rem; }
        .technical-logs h4 { font-size: 0.875rem; color: var(--text-tertiary); }
        .log-table { background: rgba(0,0,0,0.2); border-radius: 0.75rem; overflow: hidden; }
        .log-table td, .log-table th { padding: 0.625rem 0.75rem; font-size: 0.75rem; border: none; }
        .service-tag { background: var(--bg-tertiary); padding: 0.125rem 0.375rem; border-radius: 0.25rem; color: var(--text-primary); }
      `}</style>
        </div>
    );
};

export default Tenants;
