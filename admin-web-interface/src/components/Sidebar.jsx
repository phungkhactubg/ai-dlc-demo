import React from 'react';
import {
  LayoutDashboard,
  Users,
  CreditCard,
  TrendingUp,
  ShieldAlert,
  ShoppingBag,
  Bell,
  BarChart3,
  Settings,
  Car
} from 'lucide-react';

const Sidebar = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'tenants', icon: Users, label: 'Tenants' },
    { id: 'billing', icon: CreditCard, label: 'Invoices' },
    { id: 'pricing', icon: TrendingUp, label: 'Pricing' },
    { id: 'partners', icon: Users, label: 'Ecosystem' },
    { id: 'security', icon: ShieldAlert, label: 'Security' },
    { id: 'marketplace', icon: ShoppingBag, label: 'Marketplace' },
  ];

  return (
    <aside className="sidebar glass-card">
      <div className="sidebar-logo">
        <div className="logo-icon"></div>
        <h1 className="logo-text">VNPT <span>AV</span></h1>
      </div>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
          >
            <item.icon size={20} />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-footer">
        <button
          className={`nav-item ${activeTab === 'config' ? 'active' : ''}`}
          onClick={() => setActiveTab('config')}
        >
          <Settings size={20} />
          <span>System Config</span>
        </button>
      </div>

      <style jsx>{`
        .sidebar {
          width: 260px;
          height: calc(100vh - 2rem);
          margin: 1rem;
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          position: fixed;
          left: 0;
          top: 0;
          border-radius: 1.5rem;
          z-index: 100;
        }

        .sidebar-logo {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 2.5rem;
          padding-left: 0.5rem;
        }

        .logo-icon {
          width: 32px;
          height: 32px;
          background: linear-gradient(135deg, #0047BA, #00F294);
          border-radius: 0.5rem;
        }

        .logo-text {
          font-size: 1.25rem;
          letter-spacing: -0.5px;
        }

        .logo-text span {
          color: var(--accent-secondary);
        }

        .sidebar-nav {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 0.75rem 1rem;
          border-radius: 0.75rem;
          color: var(--text-secondary);
          background: transparent;
          transition: all 0.2s;
          width: 100%;
          text-align: left;
        }

        .nav-item:hover {
          background: rgba(255, 255, 255, 0.05);
          color: var(--text-primary);
        }

        .nav-item.active {
          background: var(--accent-primary);
          color: white;
          box-shadow: 0 4px 12px rgba(0, 71, 186, 0.3);
        }

        .nav-item span {
          font-size: 0.9375rem;
          font-weight: 500;
        }

        .sidebar-footer {
          margin-top: auto;
          padding-top: 1rem;
          border-top: 1px solid var(--glass-border);
        }
      `}</style>
    </aside>
  );
};

export default Sidebar;
