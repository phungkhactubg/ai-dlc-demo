import React, { useState } from 'react';
import {
    Settings,
    Webhook,
    Mail,
    Shield,
    Database,
    Globe,
    Plus,
    Trash2,
    RefreshCw,
    Code
} from 'lucide-react';

const SystemConfig = () => {
    const [activeTab, setActiveTab] = useState('webhooks');

    const [webhooks] = useState([
        {
            id: "WH-001",
            tenant: "Acme Mobility",
            url: "https://api.acme.com/v1/webhook",
            events: ["ride.completed", "payment.captured"],
            status: "Active",
            lastSuccess: "2026-03-10 10:45",
            failureCount: 0
        },
        {
            id: "WH-002",
            tenant: "Global Logistics",
            url: "https://hooks.global-log.com/av-events",
            events: ["ride.safety_stop", "vehicle.emergency"],
            status: "Failing",
            lastSuccess: "2026-03-09 15:20",
            failureCount: 12
        }
    ]);

    const [templates] = useState([
        {
            id: "TMP-001",
            name: "Ride Completed Receipt",
            channel: "Email",
            event: "ride.completed",
            locale: "vi-VN"
        },
        {
            id: "TMP-002",
            name: "Safety Emergency SMS",
            channel: "SMS",
            event: "ride.safety_stop",
            locale: "en-US"
        }
    ]);

    return (
        <div className="page-container">
            <header className="page-header">
                <div className="header-content">
                    <h1>System Configuration</h1>
                    <p>Global settings, notification templates, and integration hooks</p>
                </div>
            </header>

            <div className="tab-navigation">
                <button
                    className={`tab-btn ${activeTab === 'webhooks' ? 'active' : ''}`}
                    onClick={() => setActiveTab('webhooks')}
                >
                    <Webhook size={18} />
                    Webhooks
                </button>
                <button
                    className={`tab-btn ${activeTab === 'templates' ? 'active' : ''}`}
                    onClick={() => setActiveTab('templates')}
                >
                    <Mail size={18} />
                    Templates
                </button>
                <button
                    className={`tab-btn ${activeTab === 'security' ? 'active' : ''}`}
                    onClick={() => setActiveTab('security')}
                >
                    <Shield size={18} />
                    Security (IAM)
                </button>
                <button
                    className={`tab-btn ${activeTab === 'infra' ? 'active' : ''}`}
                    onClick={() => setActiveTab('infra')}
                >
                    <Database size={18} />
                    Infrastructure
                </button>
            </div>

            <div className="config-content">
                {activeTab === 'webhooks' && (
                    <div className="config-section glass">
                        <div className="section-header">
                            <h2>Webhook Registry</h2>
                            <button className="btn-primary btn-sm">
                                <Plus size={16} />
                                Add Webhook
                            </button>
                        </div>
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Tenant</th>
                                    <th>Endpoint URL</th>
                                    <th>Events</th>
                                    <th>Status</th>
                                    <th>Reliability</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {webhooks.map(wh => (
                                    <tr key={wh.id}>
                                        <td className="font-mono">{wh.id}</td>
                                        <td>{wh.tenant}</td>
                                        <td className="text-secondary font-mono text-xs">{wh.url}</td>
                                        <td>
                                            <div className="tag-cloud">
                                                {wh.events.map(ev => <span key={ev} className="badge-sm">{ev}</span>)}
                                            </div>
                                        </td>
                                        <td>
                                            <span className={`status-dot ${wh.status.toLowerCase()}`}></span>
                                            {wh.status}
                                        </td>
                                        <td>
                                            <div className="flex-stack">
                                                <span>Success: {wh.lastSuccess}</span>
                                                <small className={wh.failureCount > 0 ? "text-danger" : "text-secondary"}>
                                                    Failures: {wh.failureCount}
                                                </small>
                                            </div>
                                        </td>
                                        <td>
                                            <div className="action-buttons">
                                                <button className="icon-btn"><RefreshCw size={14} /></button>
                                                <button className="icon-btn"><Trash2 size={14} /></button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {activeTab === 'templates' && (
                    <div className="config-section glass">
                        <div className="section-header">
                            <h2>Handlebars Templates</h2>
                            <button className="btn-primary btn-sm">
                                <Plus size={16} />
                                New Template
                            </button>
                        </div>
                        <div className="template-grid">
                            {templates.map(tmp => (
                                <div key={tmp.id} className="template-card glass-card">
                                    <div className="card-header">
                                        <span className="badge-outline">{tmp.channel}</span>
                                        <Globe size={14} className="text-secondary" />
                                        <span>{tmp.locale}</span>
                                    </div>
                                    <h3>{tmp.name}</h3>
                                    <code className="event-tag">{tmp.event}</code>
                                    <div className="card-footer">
                                        <button className="btn-ghost btn-sm">
                                            <Code size={14} />
                                            Edit Source
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {activeTab === 'security' && (
                    <div className="config-section glass p-8">
                        <div className="empty-state">
                            <Shield size={48} className="text-primary opacity-20" />
                            <h3>IAM & Gateway Policies</h3>
                            <p>Platform-wide security settings and rate limiting policies are managed here.</p>
                            <button className="btn-secondary">View Audit Logs</button>
                        </div>
                    </div>
                )}
            </div>

            <style jsx>{`
        .tab-navigation {
          display: flex;
          gap: 1rem;
          margin-bottom: 2rem;
          border-bottom: 1px solid var(--border-color);
          padding-bottom: 1px;
        }
        .tab-btn {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1.5rem;
          background: none;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
          border-bottom: 2px solid transparent;
        }
        .tab-btn:hover {
          color: var(--text-main);
        }
        .tab-btn.active {
          color: var(--primary);
          border-bottom-color: var(--primary);
        }
        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
          padding: 1rem;
        }
        .flex-stack {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }
        .tag-cloud {
          display: flex;
          flex-wrap: wrap;
          gap: 0.25rem;
        }
        .template-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 1.5rem;
          padding: 1rem;
        }
        .template-card {
          padding: 1.5rem;
        }
        .template-card h3 {
          margin: 1rem 0 0.5rem;
          font-size: 1.1rem;
        }
        .event-tag {
          font-family: monospace;
          background: rgba(255,255,255,0.05);
          padding: 0.2rem 0.5rem;
          border-radius: 4px;
          font-size: 0.8rem;
        }
        .card-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.8rem;
          color: var(--text-secondary);
        }
        .card-footer {
          margin-top: 1.5rem;
          display: flex;
          justify-content: flex-end;
        }
      `}</style>
        </div>
    );
};

export default SystemConfig;
