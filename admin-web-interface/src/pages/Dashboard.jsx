import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell
} from 'recharts';
import { TrendingUp, Users, Car, AlertTriangle } from 'lucide-react';

const data = [
  { name: '00:00', value: 400 },
  { name: '04:00', value: 300 },
  { name: '08:00', value: 900 },
  { name: '12:00', value: 1200 },
  { name: '16:00', value: 1500 },
  { name: '20:00', value: 1300 },
  { name: '23:59', value: 800 },
];

const barData = [
  { name: 'Mon', value: 45000 },
  { name: 'Tue', value: 52000 },
  { name: 'Wed', value: 48000 },
  { name: 'Thu', value: 61000 },
  { name: 'Fri', value: 75000 },
  { name: 'Sat', value: 82000 },
  { name: 'Sun', value: 70000 },
];

const vehicles = [
  { id: 'AV-101', lat: 21.0285, lng: 105.8542, status: 'active', battery: 85 },
  { id: 'AV-102', lat: 21.0333, lng: 105.8444, status: 'active', battery: 42 },
  { id: 'AV-105', lat: 21.02, lng: 105.83, status: 'charging', battery: 15 },
  { id: 'AV-108', lat: 21.04, lng: 105.86, status: 'active', battery: 92 },
];

const KPICard = ({ title, value, change, icon: Icon, color }) => (
  <div className="glass-card kpi-card">
    <div className="kpi-header">
      <div className={`kpi-icon-bg ${color}`}>
        <Icon size={20} />
      </div>
      <span className={`kpi-change ${change.startsWith('+') ? 'positive' : 'negative'}`}>
        {change}
      </span>
    </div>
    <div className="kpi-content">
      <h3 className="kpi-value">{value}</h3>
      <p className="kpi-title">{title}</p>
    </div>
  </div>
);

const Dashboard = () => {
  return (
    <div className="dashboard-content animate-fade-in">
      <div className="kpi-grid">
        <KPICard
          title="Saga Success Rate (TMS-BL-001)"
          value="99.4%"
          change="+0.2%"
          icon={TrendingUp}
          color="blue"
        />
        <KPICard
          title="System Quota Load (BMS-BL-006)"
          value="78.1%"
          change="+5.4%"
          icon={AlertTriangle}
          color="orange"
        />
        <KPICard
          title="DLQ Message Backlog (NCS)"
          value="142"
          change="-12"
          icon={Users}
          color="red"
        />
        <KPICard
          title="Fraud Held Review (PAY)"
          value="12"
          change="+2"
          icon={Car}
          color="green"
        />
      </div>

      <div className="dashboard-grid">
        <div className="glass-card map-section">
          <div className="section-header">
            <h3>AV Fleet & Incident Map (RHS-SRS)</h3>
            <div className="map-legend">
              <span className="legend-item"><span className="dot active"></span> Tracking</span>
              <span className="dot red-pulse"></span>
              <span className="legend-item">Incident</span>
            </div>
          </div>
          <div className="map-container-inner">
            <MapContainer center={[21.0285, 105.8542]} zoom={13} scrollWheelZoom={false}>
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              />
              {vehicles.map(v => (
                <CircleMarker
                  key={v.id}
                  center={[v.lat, v.lng]}
                  radius={6}
                  pathOptions={{
                    fillColor: v.status === 'active' ? '#00F294' : '#F59E0B',
                    color: '#fff',
                    weight: 1,
                    fillOpacity: 0.8
                  }}
                />
              ))}
              <CircleMarker
                center={[21.035, 105.85]}
                radius={12}
                pathOptions={{ fillColor: '#EF4444', color: '#fff', weight: 2, fillOpacity: 0.4 }}
                className="animate-pulse"
              >
                <Popup><strong>INCIDENT: AV-412</strong><br />Emergency Brake Triggered<br />Status: Safety_Stop</Popup>
              </CircleMarker>
            </MapContainer>
          </div>
        </div>

        <div className="glass-card chart-section">
          <h3>Quota Consumption Analysis</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', border: 'none', borderRadius: '8px' }}
                />
                <Area type="monotone" dataKey="value" stroke="#ef4444" fillOpacity={1} fill="url(#colorValue)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <style jsx>{`
        .dashboard-content {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          padding-bottom: 2rem;
        }

        .kpi-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
          gap: 1.5rem;
        }

        .kpi-card {
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .kpi-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .kpi-icon-bg {
          width: 40px;
          height: 40px;
          border-radius: 0.75rem;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .kpi-icon-bg.blue { background: rgba(0, 71, 186, 0.1); color: #0047BA; }
        .kpi-icon-bg.green { background: rgba(0, 242, 148, 0.1); color: #00F294; }
        .kpi-icon-bg.orange { background: rgba(245, 158, 11, 0.1); color: #F59E0B; }
        .kpi-icon-bg.red { background: rgba(239, 68, 68, 0.1); color: #EF4444; }

        .kpi-change {
          font-size: 0.75rem;
          font-weight: 600;
          padding: 0.25rem 0.5rem;
          border-radius: 1rem;
        }

        .kpi-change.positive { background: rgba(16, 185, 129, 0.1); color: #10B981; }
        .kpi-change.negative { background: rgba(239, 68, 68, 0.1); color: #EF4444; }

        .kpi-value {
          font-size: 1.75rem;
          font-weight: 700;
          margin-bottom: 0.25rem;
        }

        .kpi-title {
          font-size: 0.875rem;
          color: var(--text-secondary);
        }

        .dashboard-grid {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 1.5rem;
          height: 500px;
        }

        @media (max-width: 1200px) {
          .dashboard-grid {
            grid-template-columns: 1fr;
            height: auto;
          }
          .map-section, .chart-section { height: 400px; }
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
        }

        .map-section {
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
        }

        .map-container-inner {
          flex: 1;
          border-radius: 1rem;
          overflow: hidden;
          background: #1e1e1e;
        }

        .map-legend {
          display: flex;
          gap: 1rem;
          font-size: 0.75rem;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: var(--text-secondary);
        }

        .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .dot.active { background: #00F294; }
        .dot.charging { background: #F59E0B; }

        .chart-section {
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .chart-container {
          flex: 1;
          margin-left: -20px;
        }
      `}</style>
    </div>
  );
};

export default Dashboard;
