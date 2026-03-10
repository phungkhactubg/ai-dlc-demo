import React, { useState } from 'react';
import {
    ShoppingBag,
    ShieldCheck,
    Star,
    Search,
    Filter,
    ArrowRight,
    CheckCircle,
    ExternalLink
} from 'lucide-react';

const plugins = [
    { id: 1, name: 'VNPT Insurance', developer: 'VNPT Platform', category: 'Insurance', rating: 4.8, price: '$450/mo', status: 'Certified', icon: 'shield-check' },
    { id: 2, name: 'SAP Concur', developer: 'SAP', category: 'Corporate Travel', rating: 4.9, price: 'Free Trail', status: 'Certified', icon: 'briefcase' },
    { id: 3, name: 'Accessibility Pack', developer: 'VinaMove', category: 'Accessibility', rating: 4.7, price: '$199/mo', status: 'Certified', icon: 'user' },
    { id: 4, name: 'HERE Technologies', developer: 'HERE', category: 'HD Maps', rating: 4.8, price: '$250/mo', status: 'Certified', icon: 'map' },
    { id: 5, name: 'Analytics Pro', developer: 'ABI Group', category: 'Analytics', rating: 5.0, price: 'Enterprise', status: 'Certified', icon: 'bar-chart' },
    { id: 6, name: 'Stripe Payments', developer: 'Stripe', category: 'Payment', rating: 4.9, price: 'Custom', status: 'Certified', icon: 'credit-card' },
];

const Marketplace = () => {
    const [searchTerm, setSearchTerm] = useState('');

    return (
        <div className="marketplace-container animate-fade-in">
            <div className="page-header">
                <div className="text-center w-full max-w-2xl mx-auto mb-8">
                    <h1 className="page-title text-3xl">AVX Marketplace</h1>
                    <p className="page-subtitle text-lg">Enhance your autonomous fleet with trusted extensions and certified integrations.</p>
                    <div className="search-bar-large glass-card mt-6">
                        <Search size={20} className="text-tertiary" />
                        <input
                            type="text"
                            placeholder="Search plugins, categories, or developers..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>
            </div>

            <div className="marketplace-layout">
                <aside className="filters-sidebar glass-card">
                    <div className="filter-group">
                        <h3>Categories</h3>
                        <div className="checkbox-group">
                            <label><input type="checkbox" defaultChecked /> AV Fleet Ops</label>
                            <label><input type="checkbox" /> Insurance</label>
                            <label><input type="checkbox" /> Accessibility</label>
                            <label><input type="checkbox" /> Corporate Travel</label>
                            <label><input type="checkbox" /> Mapping</label>
                        </div>
                    </div>
                    <div className="filter-group mt-6">
                        <h3>Pricing</h3>
                        <div className="checkbox-group">
                            <label><input type="checkbox" /> Free</label>
                            <label><input type="checkbox" /> Under $100</label>
                            <label><input type="checkbox" /> Enterprise</label>
                        </div>
                    </div>
                </aside>

                <div className="plugins-grid">
                    {plugins.map(plugin => (
                        <div key={plugin.id} className="glass-card plugin-card">
                            <div className="plugin-header">
                                <div className="plugin-icon-container">
                                    <div className={`plugin-icon ${plugin.category.toLowerCase().replace(' ', '-')}`}></div>
                                </div>
                                <div className="plugin-rating">
                                    <Star size={14} className="fill-yellow-400 text-yellow-400" />
                                    <span>{plugin.rating}</span>
                                </div>
                            </div>
                            <div className="plugin-body">
                                <h3 className="plugin-name">{plugin.name}</h3>
                                <p className="text-xs text-tertiary font-mono mb-2">SRS-CERT: CERT-00{plugin.id}</p>
                                <p className="plugin-category">{plugin.category} • {plugin.developer}</p>
                                <div className="certification-badge">
                                    <ShieldCheck size={14} className="text-blue-500" />
                                    <span>{plugin.status} (Audit Passed)</span>
                                </div>
                            </div>
                            <div className="plugin-footer">
                                <span className="plugin-price">{plugin.price}</span>
                                <button className="btn-primary btn-sm">
                                    Activate (TMS)
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <style jsx>{`
        .marketplace-container { display: flex; flex-direction: column; gap: 1.5rem; padding-bottom: 3rem; }
        
        .search-bar-large { display: flex; align-items: center; gap: 1rem; padding: 1rem 1.5rem; border-radius: 2rem; width: 100%; border: 1px solid var(--glass-border); }
        .search-bar-large input { background: transparent; border: none; font-size: 1rem; color: white; width: 100%; outline: none; }
        
        .marketplace-layout { display: grid; grid-template-columns: 240px 1fr; gap: 2rem; }
        
        .filters-sidebar { padding: 1.5rem; height: fit-content; }
        .filter-group h3 { font-size: 0.875rem; color: var(--text-tertiary); margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 0.05em; }
        .checkbox-group { display: flex; flex-direction: column; gap: 0.75rem; }
        .checkbox-group label { display: flex; align-items: center; gap: 0.75rem; font-size: 0.875rem; color: var(--text-secondary); cursor: pointer; }
        .checkbox-group input { accent-color: var(--accent-primary); }

        .plugins-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem; }
        
        .plugin-card { padding: 1.5rem; transition: transform 0.2s; cursor: pointer; display: flex; flex-direction: column; }
        .plugin-card:hover { transform: translateY(-5px); border-color: var(--accent-primary); }

        .plugin-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem; }
        .plugin-icon-container { width: 48px; height: 48px; border-radius: 0.75rem; background: var(--bg-tertiary); padding: 8px; }
        .plugin-icon { width: 100%; height: 100%; border-radius: 0.25rem; background: linear-gradient(135deg, #3b82f6, #00f294); }
        .plugin-rating { display: flex; align-items: center; gap: 0.25rem; font-size: 0.75rem; color: var(--text-secondary); }

        .plugin-name { font-size: 1.125rem; font-weight: 600; margin-bottom: 0.25rem; }
        .plugin-category { font-size: 0.8125rem; color: var(--text-secondary); margin-bottom: 0.75rem; }
        
        .certification-badge { display: flex; align-items: center; gap: 0.375rem; font-size: 0.75rem; font-weight: 600; color: var(--accent-primary); background: rgba(0, 71, 186, 0.1); width: fit-content; padding: 0.25rem 0.5rem; border-radius: 0.5rem; }
        
        .plugin-footer { margin-top: auto; padding-top: 1.5rem; display: flex; justify-content: space-between; align-items: center; }
        .plugin-price { font-weight: 600; font-size: 1rem; color: var(--text-primary); }
        .view-btn { background: transparent; color: var(--accent-primary); display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; font-weight: 500; }
        .view-btn:hover { color: white; }
      `}</style>
        </div>
    );
};

export default Marketplace;
