import React, { useState } from 'react';
import {
    Users,
    ShieldCheck,
    Cpu,
    ExternalLink,
    CheckCircle,
    AlertTriangle,
    FileText,
    Search,
    Filter
} from 'lucide-react';

const Partners = () => {
    const [partners] = useState([
        {
            id: "PRT-001",
            name: "VNPT Insurance",
            category: "Insurance",
            status: "Published",
            auditStatus: "Passed",
            perfScore: 98,
            commission: "1.5%",
            plugins: 3
        },
        {
            id: "PRT-002",
            name: "Accessibility First",
            category: "Accessibility",
            status: "SecurityAudit",
            auditStatus: "Pending",
            perfScore: null,
            commission: "0%",
            plugins: 1
        },
        {
            id: "PRT-003",
            name: "Global Tech Connect",
            category: "Connectors",
            status: "PerformanceTest",
            auditStatus: "Passed",
            perfScore: 85,
            commission: "5%",
            plugins: 2
        }
    ]);

    const getStatusBadge = (status) => {
        switch (status) {
            case 'Published': return 'status-published';
            case 'SecurityAudit': return 'status-audit';
            case 'PerformanceTest': return 'status-perf';
            default: return '';
        }
    };

    return (
        <div className="page-container">
            <header className="page-header">
                <div className="header-content">
                    <h1>Ecosystem & Marketplace</h1>
                    <p>Partner lifecycle management, security audits, and revenue payouts</p>
                </div>
                <div className="header-actions">
                    <button className="btn-secondary">
                        <Users size={18} />
                        Partner Portal
                    </button>
                    <button className="btn-primary">
                        Submit New Plugin
                    </button>
                </div>
            </header>

            <div className="grid-3">
                <div className="card-mini glass">
                    <div className="mini-content">
                        <span className="mini-label">Active Partners</span>
                        <div className="mini-value-row">
                            <span className="mini-value">42</span>
                            <span className="trend positive">+3 this month</span>
                        </div>
                    </div>
                    <Users size={24} className="icon-accent" />
                </div>
                <div className="card-mini glass">
                    <div className="mini-content">
                        <span className="mini-label">Certification Queue</span>
                        <div className="mini-value-row">
                            <span className="mini-value">8</span>
                            <span className="trend">6 Security / 2 Perf</span>
                        </div>
                    </div>
                    <ShieldCheck size={24} className="icon-accent" />
                </div>
                <div className="card-mini glass">
                    <div className="mini-content">
                        <span className="mini-label">Total Payouts (MTD)</span>
                        <div className="mini-value-row">
                            <span className="mini-value">125.4M <small>VND</small></span>
                            <span className="trend positive">+8.2%</span>
                        </div>
                    </div>
                    <ExternalLink size={24} className="icon-accent" />
                </div>
            </div>

            <div className="table-container glass mt-8">
                <div className="table-header">
                    <h3>Partner Certification Gateway</h3>
                    <div className="filters">
                        <div className="search-box">
                            <Search size={18} />
                            <input type="text" placeholder="Search partners..." />
                        </div>
                    </div>
                </div>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Partner Name</th>
                            <th>Category</th>
                            <th>Lifecycle Status</th>
                            <th>Security Audit</th>
                            <th>Perf Score</th>
                            <th>Revenue Share</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {partners.map(p => (
                            <tr key={p.id}>
                                <td className="font-mono">{p.id}</td>
                                <td>
                                    <div className="flex-stack">
                                        <span className="font-bold">{p.name}</span>
                                        <small className="text-secondary">{p.plugins} plugins live</small>
                                    </div>
                                </td>
                                <td>{p.category}</td>
                                <td>
                                    <span className={`badge-pill ${getStatusBadge(p.status)}`}>
                                        {p.status}
                                    </span>
                                </td>
                                <td>
                                    <div className="flex-align text-sm">
                                        {p.auditStatus === 'Passed' ? (
                                            <CheckCircle size={14} className="text-success mr-2" />
                                        ) : (
                                            <AlertTriangle size={14} className="text-warning mr-2" />
                                        )}
                                        {p.auditStatus}
                                    </div>
                                </td>
                                <td>
                                    {p.perfScore ? (
                                        <div className="flex-align">
                                            <div className="progress-mini">
                                                <div className="progress-bar" style={{ width: `${p.perfScore}%` }}></div>
                                            </div>
                                            <span className="ml-2">{p.perfScore}%</span>
                                        </div>
                                    ) : <span className="text-secondary">—</span>}
                                </td>
                                <td>{p.commission}</td>
                                <td>
                                    <div className="action-buttons">
                                        <button className="icon-btn" title="Audit Details"><FileText size={14} /></button>
                                        <button className="icon-btn" title="Configure"><Cpu size={14} /></button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <style jsx>{`
        .status-published { background: rgba(16, 185, 129, 0.1); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.2); }
        .status-audit { background: rgba(59, 130, 246, 0.1); color: var(--primary); border: 1px solid rgba(59, 130, 246, 0.2); }
        .status-perf { background: rgba(245, 158, 11, 0.1); color: var(--warning); border: 1px solid rgba(245, 158, 11, 0.2); }
        
        .badge-pill {
          padding: 0.25rem 0.75rem;
          border-radius: 999px;
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .progress-mini {
          width: 60px;
          height: 6px;
          background: rgba(255,255,255,0.1);
          border-radius: 3px;
          overflow: hidden;
        }
        .progress-bar {
          height: 100%;
          background: var(--primary);
        }
        .flex-align {
          display: flex;
          align-items: center;
        }
        .icon-accent {
          opacity: 0.5;
          color: var(--primary);
        }
      `}</style>
        </div>
    );
};

export default Partners;
