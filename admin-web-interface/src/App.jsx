import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Tenants from './pages/Tenants';
import Pricing from './pages/Pricing';
import Marketplace from './pages/Marketplace';
import Security from './pages/Security';
import Invoices from './pages/Invoices';
import SystemConfig from './pages/SystemConfig';
import Partners from './pages/Partners';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'tenants':
        return <Tenants />;
      case 'pricing':
        return <Pricing />;
      case 'marketplace':
        return <Marketplace />;
      case 'security':
        return <Security />;
      case 'billing':
        return <Invoices />;
      case 'partners':
        return <Partners />;
      case 'config':
        return <SystemConfig />;
      default:
        return (
          <div className="flex items-center justify-center h-full">
            <h2 className="text-2xl text-secondary">Module {activeTab} is under construction...</h2>
          </div>
        );
    }
  };

  return (
    <div className="app-layout">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="main-content">
        <header className="topbar glass-card">
          <div className="search-bar">
            {/* Search input would go here */}
            <input type="text" placeholder="Search for trips, fleet, or tenants..." />
          </div>
          <div className="user-profile">
            <div className="notification-badge">
              <span className="dot"></span>
            </div>
            <div className="profile-info">
              <div className="profile-img"></div>
              <div className="profile-text">
                <p className="name">Admin User</p>
                <p className="role">Platform Admin</p>
              </div>
            </div>
          </div>
        </header>

        <div className="page-container">
          {renderContent()}
        </div>
      </main>

      <style jsx>{`
        .app-layout {
          display: flex;
          min-height: 100vh;
        }

        .main-content {
          flex: 1;
          margin-left: 280px; /* Sidebar width + margin */
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .topbar {
          height: 64px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 1.5rem;
          border-radius: 1rem;
        }

        .search-bar input {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid var(--glass-border);
          padding: 0.5rem 1rem;
          border-radius: 0.5rem;
          color: white;
          width: 320px;
          font-size: 0.875rem;
        }

        .search-bar input::placeholder {
          color: var(--text-tertiary);
        }

        .user-profile {
          display: flex;
          align-items: center;
          gap: 1.5rem;
        }

        .profile-info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .profile-img {
          width: 36px;
          height: 36px;
          background: #334155;
          border-radius: 50%;
        }

        .profile-text {
          line-height: 1.2;
        }

        .name {
          font-size: 0.875rem;
          font-weight: 600;
        }

        .role {
          font-size: 0.75rem;
          color: var(--text-secondary);
        }

        .page-container {
          flex: 1;
          display: flex;
          flex-direction: column;
        }
      `}</style>
    </div>
  );
}

export default App;
