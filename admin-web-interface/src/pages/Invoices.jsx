import React, { useState } from 'react';
import {
    Receipt,
    Download,
    Filter,
    Search,
    CheckCircle2,
    Clock,
    AlertCircle,
    FileText,
    DollarSign
} from 'lucide-react';

const Invoices = () => {
    const [invoices] = useState([
        {
            id: "INV-2026-001",
            tenant: "Acme Mobility",
            amount: "1,250,000,000",
            currency: "VND",
            status: "Paid",
            date: "2026-03-01",
            dueDate: "2026-03-15",
            taxType: "VAT (10%)",
            taxAmount: "125,000,000",
            plan: "Enterprise"
        },
        {
            id: "INV-2026-002",
            tenant: "Global Logistics",
            amount: "850,000,000",
            currency: "VND",
            status: "Pending",
            date: "2026-03-02",
            dueDate: "2026-03-16",
            taxType: "VAT (10%)",
            taxAmount: "85,000,000",
            plan: "Growth"
        },
        {
            id: "INV-2026-003",
            tenant: "City Rides",
            amount: "150,000,000",
            currency: "VND",
            status: "Overdue",
            date: "2026-02-15",
            dueDate: "2026-03-01",
            taxType: "VAT (10%)",
            taxAmount: "15,000,000",
            plan: "Starter"
        }
    ]);

    const getStatusColor = (status) => {
        switch (status) {
            case 'Paid': return 'var(--success)';
            case 'Pending': return 'var(--warning)';
            case 'Overdue': return 'var(--danger)';
            default: return 'var(--text-secondary)';
        }
    };

    return (
        <div className="page-container">
            <header className="page-header">
                <div className="header-content">
                    <h1>Billing & Invoices</h1>
                    <p>Manage tenant subscriptions, tax compliance, and revenue collection</p>
                </div>
                <div className="header-actions">
                    <button className="btn-secondary">
                        <Filter size={18} />
                        Filter
                    </button>
                    <button className="btn-primary">
                        <Download size={18} />
                        Export Monthly Report
                    </button>
                </div>
            </header>

            <div className="stats-grid">
                <div className="stat-card glass">
                    <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--primary)' }}>
                        <DollarSign size={24} />
                    </div>
                    <div className="stat-info">
                        <span className="stat-label">Total Revenue (MTD)</span>
                        <h2 className="stat-value">2,250M <small>VND</small></h2>
                        <span className="stat-change positive">+12.5% from last month</span>
                    </div>
                </div>
                <div className="stat-card glass">
                    <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)' }}>
                        <CheckCircle2 size={24} />
                    </div>
                    <div className="stat-info">
                        <span className="stat-label">Collected</span>
                        <h2 className="stat-value">1,250M <small>VND</small></h2>
                        <span className="stat-change">92% collection rate</span>
                    </div>
                </div>
                <div className="stat-card glass">
                    <div className="stat-icon" style={{ background: 'rgba(245, 158, 11, 0.1)', color: 'var(--warning)' }}>
                        <Clock size={24} />
                    </div>
                    <div className="stat-info">
                        <span className="stat-label">Pending Approval</span>
                        <h2 className="stat-value">850M <small>VND</small></h2>
                        <span className="stat-change">2 pending invoices</span>
                    </div>
                </div>
            </div>

            <div className="table-container glass">
                <div className="table-header">
                    <h3>Recent Invoices</h3>
                    <div className="search-box">
                        <Search size={18} />
                        <input type="text" placeholder="Search invoices..." />
                    </div>
                </div>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Invoice ID</th>
                            <th>Tenant</th>
                            <th>Plan</th>
                            <th>Date</th>
                            <th>Amount (ex. Tax)</th>
                            <th>Tax</th>
                            <th>Total</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {invoices.map((inv) => (
                            <tr key={inv.id}>
                                <td className="font-mono">{inv.id}</td>
                                <td className="font-bold">{inv.tenant}</td>
                                <td>
                                    <span className="badge-outline">{inv.plan}</span>
                                </td>
                                <td>{inv.date}</td>
                                <td>{inv.amount}</td>
                                <td className="text-secondary">{inv.taxAmount}</td>
                                <td className="font-bold">{inv.currency} {(parseInt(inv.amount.replace(/,/g, '')) + parseInt(inv.taxAmount.replace(/,/g, ''))).toLocaleString()}</td>
                                <td>
                                    <span className="status-badge" style={{
                                        backgroundColor: `${getStatusColor(inv.status)}20`,
                                        color: getStatusColor(inv.status),
                                        borderColor: `${getStatusColor(inv.status)}40`
                                    }}>
                                        {inv.status}
                                    </span>
                                </td>
                                <td>
                                    <div className="action-buttons">
                                        <button className="icon-btn" title="View PDF"><FileText size={16} /></button>
                                        <button className="icon-btn" title="Download"><Download size={16} /></button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Invoices;
