import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import {
  Activity, ArrowDownToLine, ArrowUpFromLine, Battery, BatteryCharging, Boxes,
  ChevronRight, ChevronLeft, ChevronDown, Edit3, LayoutDashboard, Plus, Search,
  Users, X, Trash2, Zap, Package, AlertTriangle, CheckCircle2, XCircle, Minus,
  Menu, PanelLeftClose, Truck, Settings as SettingsIcon, TrendingUp, ShoppingCart,
  Flame, RefreshCcw
} from 'lucide-react';
import '@/App.css';
import '@/responsive.css';
import '@/psc-overrides.css';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const typeMeta = {
  battery: { icon: BatteryCharging, label: 'Battery', tone: 'battery' },
  inverter: { icon: Zap, label: 'Inverter', tone: 'inverter' },
  trolley: { icon: Package, label: 'Trolley', tone: 'trolley' },
};

export default function App() {
  const [data, setData] = useState({ brands: [], products: [], suppliers: [], dealers: [] });
  const [stock, setStock] = useState([]);
  const [dash, setDash] = useState({});
  const [history, setHistory] = useState([]);
  const [tab, setTab] = useState('dashboard');
  const [modal, setModal] = useState(null);
  const [editing, setEditing] = useState(null);
  const [quickKind, setQuickKind] = useState(null);
  const [profile, setProfile] = useState(null);
  const [selectedBrand, setSelectedBrand] = useState(null);
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('psc-collapsed') === '1');
  const [mobileOpen, setMobileOpen] = useState(false);
  const [drill, setDrill] = useState(null); // { title, items }

  const load = async () => {
    const [b, s, d, l] = await Promise.all([
      axios.get(`${API}/bootstrap`),
      axios.get(`${API}/stock`),
      axios.get(`${API}/dashboard`),
      axios.get(`${API}/ledger`),
    ]);
    setData(b.data); setStock(s.data); setDash(d.data); setHistory(l.data);
  };
  useEffect(() => { load(); }, []);
  useEffect(() => { window.__pscData = data; }, [data]);
  useEffect(() => { localStorage.setItem('psc-collapsed', collapsed ? '1' : '0'); }, [collapsed]);

  const nav = [
    ['dashboard', 'Dashboard', LayoutDashboard],
    ['stock', 'Current Stock', Boxes],
    ['history', 'History', Activity],
    ['dealers', 'Dealers', Users],
    ['suppliers', 'Suppliers', Truck],
    ['catalog', 'Brands', BatteryCharging],
    ['settings', 'Settings', SettingsIcon],
  ];

  const titles = {
    dashboard: 'Dashboard',
    stock: 'Current stock',
    history: 'Movement history',
    dealers: 'Dealers',
    suppliers: 'Suppliers',
    catalog: 'Brands',
    settings: 'Settings',
  };

  const goto = (id) => { setTab(id); setSelectedBrand(null); setMobileOpen(false); };
  const openQuick = (kind) => setQuickKind(kind);

  return (
    <div className={`app-shell ${collapsed ? 'is-collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
      {mobileOpen && <div className="mobile-backdrop" onClick={() => setMobileOpen(false)} />}
      <aside className="sidebar">
        <div className="sidebar-top">
          <div className="brandmark">
            <div className="mark">P</div>
            <div className="brandmark-text"><strong>PSC</strong><span>STOCK CONTROL</span></div>
          </div>
          <button className="collapse-btn" data-testid="sidebar-collapse-button"
            onClick={() => setCollapsed(c => !c)} title="Collapse sidebar">
            <PanelLeftClose size={16} />
          </button>
        </div>
        <div className="workspace-label">WORKSPACE</div>
        {nav.map(([id, label, Icon]) => (
          <button key={id} data-testid={`nav-${id}-button`}
            className={`nav-item ${tab === id ? 'active' : ''}`}
            onClick={() => goto(id)} title={label}>
            <Icon size={17} /><span>{label}</span><ChevronRight size={14} />
          </button>
        ))}
        <div className="sidebar-foot">
          <div className="status-dot" /><span>One stock location</span>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="topbar-left">
            <button className="hamburger" data-testid="mobile-menu-button"
              onClick={() => setMobileOpen(o => !o)} aria-label="Menu">
              <Menu size={20} />
            </button>
            <div>
              <div className="eyebrow">PSC WORKSPACE</div>
              <h1 data-testid="page-title">{titles[tab]}</h1>
            </div>
          </div>
          <div className="top-actions">
            <button data-testid="quick-inward-button" className="outline-btn"
              onClick={() => setModal('inward')}>
              <ArrowDownToLine size={16} /><span>Stock In</span>
            </button>
            <button data-testid="quick-outward-button" className="primary-btn"
              onClick={() => setModal('outward')}>
              <ArrowUpFromLine size={16} /><span>Stock Out</span>
            </button>
          </div>
        </header>

        {tab === 'dashboard' && (
          <Dashboard dash={dash} stock={stock} data={data}
            setTab={goto} setModal={setModal} setSelectedBrand={setSelectedBrand}
            setDrill={setDrill} />
        )}
        {tab === 'stock' && <Stock stock={stock} data={data} />}
        {tab === 'history' && <History rows={history} onEdit={setEditing} />}
        {tab === 'dealers' && (
          <Directory kind="dealer" items={data.dealers}
            onSelect={(id) => setProfile({ id, kind: 'dealer' })}
            setQuick={openQuick} />
        )}
        {tab === 'suppliers' && (
          <Directory kind="supplier" items={data.suppliers}
            onSelect={(id) => setProfile({ id, kind: 'supplier' })}
            setQuick={openQuick} />
        )}
        {tab === 'catalog' && (
          <Catalog data={data} stock={stock} setQuick={openQuick}
            selectedBrand={selectedBrand} setSelectedBrand={setSelectedBrand}
            onReload={load} />
        )}
        {tab === 'settings' && <SettingsPage onReset={load} />}
      </main>

      {modal && (
        <TransactionModal type={modal} data={data} editing={editing}
          onClose={() => { setModal(null); setEditing(null); }}
          onSaved={() => { setModal(null); setEditing(null); load(); }} />
      )}
      {editing && modal === null && (
        <TransactionModal type={editing.kind} data={data} editing={editing}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); load(); }} />
      )}
      {quickKind && (
        <MasterModal kind={quickKind} presetBrandId={selectedBrand}
          onClose={() => setQuickKind(null)}
          onSaved={() => { setQuickKind(null); load(); }} />
      )}
      {profile && (
        <PartyProfile id={profile.id} kind={profile.kind}
          onClose={() => setProfile(null)} />
      )}
      {drill && <DrillDrawer title={drill.title} items={drill.items}
        onClose={() => setDrill(null)} />}
    </div>
  );
}

/* ================== DASHBOARD ================== */
function Dashboard({ dash, stock, data, setTab, setModal, setSelectedBrand, setDrill }) {
  const [expandedBrand, setExpandedBrand] = useState(null);

  const openStockList = (filter, title) => {
    const items = stock.filter(filter).map(s => ({ ...s }));
    setDrill({ title, items });
  };

  const brandData = data.brands.map(b => {
    const rows = stock.filter(s => s.brand_id === b.id);
    const total = rows.reduce((a, x) => a + (x.available || 0), 0);
    const low = rows.filter(r => r.available > 0 && r.available <= r.reorder_level).length;
    const out = rows.filter(r => r.available <= 0).length;
    return { ...b, rows, total, low, out };
  });

  // Reorder recommendations — sort by urgency (out first, then low)
  const reorderList = useMemo(() => {
    return stock
      .filter(s => s.available <= s.reorder_level)
      .map(s => ({
        ...s,
        urgency: s.available <= 0 ? 2 : 1,
        suggested: Math.max((s.reorder_level || 10) * 2 - s.available, s.reorder_level || 10),
      }))
      .sort((a, b) => b.urgency - a.urgency || a.available - b.available);
  }, [stock]);

  // Top movers by outward
  const topMovers = useMemo(() => {
    return [...stock]
      .filter(s => s.outward > 0)
      .sort((a, b) => b.outward - a.outward)
      .slice(0, 5);
  }, [stock]);

  const openBrand = (id) => { setSelectedBrand(id); setTab('catalog'); };
  const isEmpty = stock.length === 0;

  return (
    <div className="content">
      {isEmpty && (
        <div className="empty-state" data-testid="empty-dashboard">
          <div className="empty-icon"><Boxes size={28} /></div>
          <h3>Fresh canvas</h3>
          <p>Add a brand, then a product, and start recording stock in / stock out.</p>
          <div className="empty-actions">
            <button className="primary-btn" onClick={() => { setTab('catalog'); }}>
              <Plus size={16} /> Start with a brand
            </button>
          </div>
        </div>
      )}

      {/* Big action row */}
      <section className="big-actions">
        <button data-testid="dashboard-stock-in-action" className="big-action in"
          onClick={() => setModal('inward')}>
          <span className="ba-icon"><ArrowDownToLine size={26} /></span>
          <span className="ba-body">
            <b>Stock In</b>
            <small>Record what came in — supplier + items</small>
          </span>
          <ChevronRight size={20} />
        </button>
        <button data-testid="dashboard-stock-out-action" className="big-action out"
          onClick={() => setModal('outward')}>
          <span className="ba-icon"><ArrowUpFromLine size={26} /></span>
          <span className="ba-body">
            <b>Stock Out</b>
            <small>Record what went out — dealer + items</small>
          </span>
          <ChevronRight size={20} />
        </button>
      </section>

      {/* Analytics — clickable */}
      <section className="analytics-row">
        <AnalyticCard testId="analytics-available" label="Total units available"
          value={(dash.available || 0).toLocaleString()} icon={Boxes} tone="blue"
          onClick={() => openStockList(s => s.available > 0, 'All available stock')} />
        <AnalyticCard testId="analytics-in-stock" label="Models in stock"
          value={dash.in_stock_models || 0} sub={`of ${dash.total_models || 0} models`}
          icon={CheckCircle2} tone="green"
          onClick={() => openStockList(s => s.available > 0, 'Models in stock')} />
        <AnalyticCard testId="analytics-low-stock" label="Low stock"
          value={dash.low_stock_models || 0} sub="reorder recommended"
          icon={AlertTriangle} tone="amber"
          onClick={() => openStockList(s => s.available > 0 && s.available <= s.reorder_level, 'Low stock — reorder soon')} />
        <AnalyticCard testId="analytics-out-of-stock" label="Out of stock"
          value={dash.out_of_stock_models || 0} sub="tap to see what's out"
          icon={XCircle} tone="red"
          onClick={() => openStockList(s => s.available <= 0, 'Out of stock — order now')} />
      </section>

      {/* Order next + Top movers */}
      <section className="insight-split">
        <div className="insight-card order-next" data-testid="order-next-panel">
          <div className="insight-head">
            <div className="insight-title">
              <div className="insight-icon amber"><ShoppingCart size={17} /></div>
              <div>
                <div className="eyebrow">WHAT TO ORDER NEXT</div>
                <h3>Reorder recommendations</h3>
              </div>
            </div>
            <span className="pill">{reorderList.length}</span>
          </div>
          {reorderList.length === 0 ? (
            <div className="all-good">
              <CheckCircle2 size={30} />
              <b>All stocks healthy</b>
              <small>Nothing needs reordering right now.</small>
            </div>
          ) : (
            <div className="reorder-list">
              {reorderList.slice(0, 6).map(r => {
                const M = typeMeta[r.product_type] || typeMeta.battery;
                const IconX = M.icon;
                return (
                  <div className="reorder-row" key={r.product_id}
                    data-testid={`reorder-row-${r.product_id}`}>
                    <span className={`type-icon ${M.tone}`}><IconX size={15} /></span>
                    <div className="reorder-body">
                      <b>{r.brand} · {r.product}</b>
                      <small>Have {r.available} · reorder at {r.reorder_level}</small>
                    </div>
                    <div className="reorder-cta">
                      <span className={`status ${r.available <= 0 ? 'red' : 'warn'}`}>
                        {r.available <= 0 ? 'ORDER NOW' : 'ORDER SOON'}
                      </span>
                      <b>+{r.suggested}</b>
                      <em>suggested</em>
                    </div>
                  </div>
                );
              })}
              {reorderList.length > 6 && (
                <button className="text-btn"
                  onClick={() => openStockList(s => s.available <= s.reorder_level, 'All reorder items')}>
                  See all {reorderList.length} <ChevronRight size={13} />
                </button>
              )}
            </div>
          )}
        </div>

        <div className="insight-card top-movers" data-testid="top-movers-panel">
          <div className="insight-head">
            <div className="insight-title">
              <div className="insight-icon violet"><Flame size={17} /></div>
              <div>
                <div className="eyebrow">FAST MOVING</div>
                <h3>Top movers</h3>
              </div>
            </div>
          </div>
          {topMovers.length === 0 ? (
            <div className="empty">No movement yet. Record a stock out to see leaders.</div>
          ) : (
            <div className="mover-list">
              {topMovers.map((m, i) => {
                const M = typeMeta[m.product_type] || typeMeta.battery;
                const IconX = M.icon;
                const max = topMovers[0].outward || 1;
                return (
                  <div className="mover-row" key={m.product_id}>
                    <span className="mover-rank">{i + 1}</span>
                    <span className={`type-icon ${M.tone}`}><IconX size={14} /></span>
                    <div className="mover-body">
                      <b>{m.brand} · {m.product}</b>
                      <div className="bar"><i style={{ width: `${(m.outward / max) * 100}%` }} /></div>
                    </div>
                    <div className="mover-qty"><strong>{m.outward}</strong><small>sold</small></div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* Brand cards */}
      <div className="section-head">
        <div>
          <div className="eyebrow">STOCK BY BRAND</div>
          <h3>Tap a brand to expand</h3>
        </div>
        <button className="text-btn" onClick={() => setTab('stock')}>
          Full stock view <ChevronRight size={14} />
        </button>
      </div>

      <section className="brand-grid">
        {brandData.map(b => {
          const expanded = expandedBrand === b.id;
          return (
            <div key={b.id} className={`brand-card ${expanded ? 'expanded' : ''}`}>
              <button className="brand-head" onClick={() => setExpandedBrand(expanded ? null : b.id)}
                data-testid={`brand-toggle-${b.id}`}>
                <div className="brand-avatar big">{b.name[0]}</div>
                <div className="brand-title">
                  <b>{b.name}</b>
                  <small>{b.rows.length} models · {b.total} units</small>
                </div>
                <div className="brand-badges">
                  {b.low > 0 && <span className="chip amber">{b.low} low</span>}
                  {b.out > 0 && <span className="chip red">{b.out} out</span>}
                </div>
                <ChevronDown size={18} className={`chev ${expanded ? 'rot' : ''}`} />
              </button>
              {expanded && (
                <div className="brand-body">
                  {b.rows.length === 0 && <div className="empty">No products yet. Add one from Brands.</div>}
                  {b.rows.map(r => {
                    const M = typeMeta[r.product_type] || typeMeta.battery;
                    const IconX = M.icon;
                    return (
                      <div className="brand-item" key={r.product_id}>
                        <span className={`type-icon ${M.tone}`}><IconX size={15} /></span>
                        <div className="brand-item-name">
                          <b>{r.product}</b>
                          <small>{M.label} · {r.capacity || r.model || '—'}</small>
                        </div>
                        <div className="qty-block">
                          <strong>{r.available}</strong><span>available</span>
                        </div>
                        <span className={`status ${r.available <= 0 ? 'red' : r.low ? 'warn' : 'ok'}`}>
                          {r.available <= 0 ? 'OUT' : r.low ? 'LOW' : 'OK'}
                        </span>
                      </div>
                    );
                  })}
                  <button className="text-btn brand-open"
                    onClick={() => openBrand(b.id)}
                    data-testid={`open-brand-catalog-${b.id}`}>
                    Manage {b.name} products <ChevronRight size={14} />
                  </button>
                </div>
              )}
            </div>
          );
        })}
        {brandData.length === 0 && (
          <div className="empty">No brands yet. Head to <b>Brands</b> to add your first one.</div>
        )}
      </section>

      {/* Recent activity */}
      <div className="section-head">
        <div><div className="eyebrow">RECENT ACTIVITY</div><h3>Latest movements</h3></div>
        <button className="text-btn" onClick={() => setTab('history')}>
          Full history <ChevronRight size={14} />
        </button>
      </div>
      <section className="recent-list">
        {(dash.transactions || []).slice(0, 5).map(t => (
          <div className="activity-row" key={t.id}>
            <span className={`activity-icon ${t.kind}`}>
              {t.kind === 'inward' ? <ArrowDownToLine size={15} /> : <ArrowUpFromLine size={15} />}
            </span>
            <div>
              <b>{t.kind === 'inward' ? 'Stock in' : 'Stock out'} · {t.transaction_id}</b>
              <small>{t.total_quantity} units</small>
            </div>
            <time>{new Date(t.created_at).toLocaleString()}</time>
          </div>
        ))}
        {(dash.transactions || []).length === 0 && (
          <div className="empty">No movements yet. Record a stock in or out to get started.</div>
        )}
      </section>
    </div>
  );
}

function AnalyticCard({ label, value, sub, icon: Icon, tone, testId, onClick }) {
  return (
    <button className={`analytic ${tone}`} data-testid={testId} onClick={onClick}
      type="button">
      <div className="analytic-icon"><Icon size={19} /></div>
      <div className="analytic-body">
        <small>{label}</small>
        <strong>{value}</strong>
        {sub && <span>{sub}</span>}
      </div>
      <ChevronRight size={15} className="analytic-arrow" />
    </button>
  );
}

/* ================== DRILL DRAWER (analytics detail) ================== */
function DrillDrawer({ title, items, onClose }) {
  return (
    <div className="drawer-backdrop" onMouseDown={onClose}>
      <aside className="drawer" onMouseDown={e => e.stopPropagation()}
        data-testid="drill-drawer">
        <button className="close-btn" onClick={onClose}><X /></button>
        <div className="drawer-hero">
          <div className="eyebrow blue">DETAIL VIEW</div>
          <h2>{title}</h2>
          <p>{items.length} {items.length === 1 ? 'item' : 'items'}</p>
        </div>
        <div className="drill-list">
          {items.length === 0 && <div className="empty">Nothing here right now.</div>}
          {items.map(r => {
            const M = typeMeta[r.product_type] || typeMeta.battery;
            const IconX = M.icon;
            return (
              <div className="drill-row" key={r.product_id}>
                <span className={`type-icon ${M.tone}`}><IconX size={15} /></span>
                <div className="drill-body">
                  <b>{r.brand} · {r.product}</b>
                  <small>{M.label} · {r.capacity || r.model || '—'} · reorder at {r.reorder_level}</small>
                </div>
                <div className="drill-qty">
                  <strong className={r.available <= 0 ? 'red' : ''}>{r.available}</strong>
                  <small>available</small>
                </div>
              </div>
            );
          })}
        </div>
      </aside>
    </div>
  );
}

/* ================== SEARCH SELECT ================== */
function SearchSelect({ items, value, onChange, placeholder, testId, label, renderMeta }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const selected = items.find(x => x.id === value);
  const matches = items
    .filter(x => x.name.toLowerCase().includes(q.toLowerCase()))
    .slice(0, 8);
  return (
    <div className="search-select">
      <input data-testid={testId}
        value={open ? q : (selected?.name || '')}
        placeholder={placeholder}
        onFocus={() => { setOpen(true); setQ(''); }}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onChange={e => { setQ(e.target.value); setOpen(true); }} />
      <Search size={15} />
      {open && (
        <div className="suggestions">
          {matches.map(x => (
            <button type="button" data-testid={`${testId}-${x.id}`} key={x.id}
              onMouseDown={() => { onChange(x.id); setOpen(false); setQ(''); }}>
              <b>{x.name}</b>
              <small>{renderMeta ? renderMeta(x) : (x.city || x.model || x.capacity || label)}</small>
            </button>
          ))}
          {!matches.length && <span className="suggestion-empty">No matches</span>}
        </div>
      )}
    </div>
  );
}

/* ================== CURRENT STOCK ================== */
function Stock({ stock, data }) {
  const [q, setQ] = useState('');
  const [brand, setBrand] = useState('All');
  const [type, setType] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const rows = stock.filter(x =>
    (brand === 'All' || x.brand === brand) &&
    (type === 'All' || x.product_type === type) &&
    (statusFilter === 'All'
      || (statusFilter === 'out' && x.available <= 0)
      || (statusFilter === 'low' && x.available > 0 && x.available <= x.reorder_level)
      || (statusFilter === 'ok' && x.available > x.reorder_level)) &&
    [x.brand, x.product, x.model, x.capacity].join(' ').toLowerCase().includes(q.toLowerCase())
  );
  return (
    <div className="content">
      <div className="toolbar">
        <div className="searchbox">
          <Search size={17} />
          <input data-testid="stock-search-input" value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="Search brand, model or capacity..." />
        </div>
      </div>
      <div className="toolbar wraps">
        <div className="filter-pills" data-testid="stock-brand-filter">
          <button className={brand === 'All' ? 'selected' : ''} onClick={() => setBrand('All')}>All brands</button>
          {data.brands.map(b => (
            <button key={b.id} className={brand === b.name ? 'selected' : ''}
              onClick={() => setBrand(b.name)}>{b.name}</button>
          ))}
        </div>
        <div className="filter-pills" data-testid="stock-type-filter">
          {['All', 'battery', 'inverter', 'trolley'].map(t => (
            <button key={t} className={type === t ? 'selected' : ''} onClick={() => setType(t)}>
              {t === 'All' ? 'All types' : (typeMeta[t]?.label || t)}
            </button>
          ))}
        </div>
        <div className="filter-pills" data-testid="stock-status-filter">
          {[['All', 'All'], ['ok', 'Healthy'], ['low', 'Low'], ['out', 'Out']].map(([k, l]) => (
            <button key={k} className={statusFilter === k ? 'selected' : ''}
              onClick={() => setStatusFilter(k)}>{l}</button>
          ))}
        </div>
      </div>

      <div className="table-panel">
        <div className="panel-head">
          <div>
            <div className="eyebrow">LIVE QUANTITY VIEW</div>
            <h3>{rows.length} stock positions</h3>
          </div>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Product</th><th>Type</th><th>In</th><th>Out</th><th>Available</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(r => {
                const M = typeMeta[r.product_type] || typeMeta.battery;
                const IconX = M.icon;
                return (
                  <tr key={r.id}>
                    <td>
                      <div className="product-cell">
                        <span className={`type-icon ${M.tone}`}><IconX size={15} /></span>
                        <div>
                          <b>{r.brand} — {r.product}</b>
                          <small>{r.capacity || r.model || '—'}</small>
                        </div>
                      </div>
                    </td>
                    <td><span className={`chip ${M.tone}`}>{M.label}</span></td>
                    <td className="green-text">+{r.inward}</td>
                    <td className="blue-text">-{r.outward}</td>
                    <td><strong className="qty">{r.available}</strong></td>
                    <td>
                      <span className={`status ${r.available <= 0 ? 'red' : r.low ? 'warn' : 'ok'}`}>
                        {r.available <= 0 ? 'OUT' : r.low ? 'REORDER' : 'HEALTHY'}
                      </span>
                    </td>
                  </tr>
                );
              })}
              {rows.length === 0 && (
                <tr><td colSpan="6" className="empty">Nothing matches these filters.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ================== HISTORY ================== */
function History({ rows, onEdit }) {
  const [q, setQ] = useState('');
  const [kind, setKind] = useState('All');
  const filtered = rows.filter(r =>
    (kind === 'All' || r.kind === kind) &&
    [r.transaction_id, r.party_name, r.reference,
      ...(r.items_display || []).map(i => `${i.brand} ${i.product}`)]
      .join(' ').toLowerCase().includes(q.toLowerCase())
  );
  return (
    <div className="content">
      <div className="directory-head">
        <div>
          <div className="eyebrow blue">MOVEMENT HISTORY</div>
          <h2>Every movement, clear</h2>
          <p>Newest activity first. Open any row to correct quantity or items.</p>
        </div>
      </div>
      <div className="toolbar">
        <div className="searchbox">
          <Search size={17} />
          <input data-testid="history-search-input" value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="Search reference, dealer, product..." />
        </div>
        <div className="filter-pills" data-testid="history-kind-filter">
          {[['All', 'All'], ['inward', 'Stock In'], ['outward', 'Stock Out']].map(([k, l]) => (
            <button key={k} className={kind === k ? 'selected' : ''}
              onClick={() => setKind(k)}>{l}</button>
          ))}
        </div>
      </div>
      <div className="history-table table-panel">
        <table>
          <thead>
            <tr>
              <th>Date &amp; time</th><th>Movement</th><th>Dealer / supplier</th>
              <th>Items</th><th>Qty</th><th></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(r => (
              <tr key={r.id} data-testid={`history-row-${r.transaction_id}`}>
                <td>
                  <b>{new Date(r.created_at).toLocaleDateString()}</b>
                  <small>{new Date(r.created_at).toLocaleTimeString()}</small>
                </td>
                <td><span className={`type ${r.kind}`}>
                  {r.kind === 'inward' ? 'IN' : 'OUT'} · {r.transaction_id}
                </span></td>
                <td>{r.party_name}</td>
                <td>
                  {(r.items_display || []).map((i, idx) => {
                    const M = typeMeta[i.product_type] || typeMeta.battery;
                    return (
                      <div className="item-line" key={idx}>
                        <span className={`chip ${M.tone} tiny`}>{M.label}</span>
                        <span>{i.brand} · {i.product} × <b>{i.quantity}</b></span>
                      </div>
                    );
                  })}
                </td>
                <td><strong>{r.total_quantity}</strong></td>
                <td>
                  <button data-testid={`edit-history-${r.transaction_id}`}
                    className="icon-action" onClick={() => onEdit(r)} title="Edit movement">
                    <Edit3 size={15} />
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan="6" className="empty">No movements match.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ================== BRAND CATALOG ================== */
function Catalog({ data, stock, setQuick, selectedBrand, setSelectedBrand, onReload }) {
  const [q, setQ] = useState('');
  const brand = data.brands.find(b => b.id === selectedBrand);

  if (brand) {
    const products = data.products.filter(p => p.brand_id === brand.id && (p.active !== false));
    const remove = async (p) => {
      if (!window.confirm(`Remove ${p.name}? If it has history it will be archived instead.`)) return;
      await axios.delete(`${API}/products/${p.id}`);
      onReload();
    };
    return (
      <div className="content">
        <div className="directory-head">
          <div>
            <button className="text-btn back-btn" onClick={() => setSelectedBrand(null)}
              data-testid="back-to-brands">
              <ChevronLeft size={14} /> All brands
            </button>
            <h2 data-testid="brand-detail-name">{brand.name}</h2>
            <p>{products.length} products. Add batteries, inverters or trolleys below.</p>
          </div>
          <button className="primary-btn" onClick={() => setQuick('product')}
            data-testid="add-product-to-brand">
            <Plus size={16} /> Add product
          </button>
        </div>

        <div className="product-grid">
          {products.map(p => {
            const M = typeMeta[p.product_type] || typeMeta.battery;
            const IconX = M.icon;
            const inv = stock.find(s => s.product_id === p.id);
            return (
              <div className="product-card" key={p.id} data-testid={`product-card-${p.id}`}>
                <div className="product-card-head">
                  <span className={`type-icon ${M.tone}`}><IconX size={17} /></span>
                  <span className={`chip ${M.tone}`}>{M.label}</span>
                  <button className="icon-remove" data-testid={`delete-product-${p.id}`}
                    title="Remove" onClick={() => remove(p)}>
                    <Trash2 size={14} />
                  </button>
                </div>
                <b>{p.name}</b>
                <small>{p.capacity || '—'} · {p.model || '—'}</small>
                <div className="product-card-foot">
                  <span>Available</span>
                  <strong>{inv?.available ?? 0}</strong>
                </div>
              </div>
            );
          })}
          {products.length === 0 && (
            <div className="empty product-empty">
              No products for {brand.name} yet. Click <b>Add product</b> above.
            </div>
          )}
        </div>
      </div>
    );
  }

  const filtered = data.brands.filter(b =>
    b.name.toLowerCase().includes(q.toLowerCase()));

  return (
    <div className="content">
      <div className="directory-head">
        <div>
          <div className="eyebrow blue">BRANDS</div>
          <h2>Your brand catalog</h2>
          <p>Tap a brand to add or remove its products.</p>
        </div>
        <button data-testid="add-brand-button" className="primary-btn"
          onClick={() => setQuick('brand')}>
          <Plus size={16} /> Add brand
        </button>
      </div>

      <div className="toolbar">
        <div className="searchbox">
          <Search size={17} />
          <input data-testid="brand-search-input" value={q}
            onChange={e => setQ(e.target.value)} placeholder="Search brand..." />
        </div>
      </div>

      <div className="brand-tiles">
        {filtered.map(b => {
          const count = data.products.filter(p => p.brand_id === b.id && p.active !== false).length;
          const units = stock.filter(s => s.brand_id === b.id).reduce((a, x) => a + x.available, 0);
          return (
            <button className="brand-tile" key={b.id}
              data-testid={`brand-tile-${b.id}`}
              onClick={() => setSelectedBrand(b.id)}>
              <div className="brand-avatar big">{b.name[0]}</div>
              <div className="brand-tile-body">
                <b>{b.name}</b>
                <small>{count} products · {units} units</small>
              </div>
              <ChevronRight size={17} />
            </button>
          );
        })}
        {filtered.length === 0 && data.brands.length > 0 && (
          <div className="empty">No brand matches "{q}".</div>
        )}
        {data.brands.length === 0 && (
          <div className="empty product-empty">
            No brands yet. Click <b>Add brand</b> above to start your catalog.
          </div>
        )}
      </div>
    </div>
  );
}

/* ================== MASTER MODAL ================== */
function MasterModal({ kind, presetBrandId, onClose, onSaved }) {
  const [f, setF] = useState({
    name: '', code: '', city: '', phone: '',
    brand_id: presetBrandId || '', model: '', capacity: '',
    product_type: 'battery', reorder_level: 10,
  });
  const submit = async (e) => {
    e.preventDefault();
    try {
      if (kind === 'product') {
        await axios.post(`${API}/products`, {
          name: f.name, brand_id: f.brand_id, model: f.model, capacity: f.capacity,
          product_type: f.product_type, reorder_level: Number(f.reorder_level) || 10,
        });
      } else {
        const details = kind === 'dealer' ? { city: f.city, phone: f.phone }
          : kind === 'supplier' ? { city: f.city, phone: f.phone } : {};
        await axios.post(`${API}/masters/${kind}s`,
          { name: f.name, code: f.code, details });
      }
      onSaved();
    } catch (err) {
      alert(err.response?.data?.detail || 'Could not save');
    }
  };

  const title = kind === 'product' ? 'Add product'
    : kind === 'brand' ? 'Add brand'
    : kind === 'dealer' ? 'Add dealer' : 'Add supplier';

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <div className="modal" onMouseDown={e => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <div className="eyebrow blue">QUICK ADD</div>
            <h3>{title}</h3>
          </div>
          <button data-testid="close-master-modal" className="close-btn" onClick={onClose}><X /></button>
        </div>
        <form onSubmit={submit}>
          {kind === 'product' ? (
            <>
              <label>Brand
                <select data-testid="catalog-product-brand" required
                  value={f.brand_id}
                  onChange={e => setF({ ...f, brand_id: e.target.value })}>
                  <option value="">Select brand</option>
                  {window.__pscData?.brands?.map(x => (
                    <option key={x.id} value={x.id}>{x.name}</option>
                  ))}
                </select>
              </label>
              <label>Product type
                <div className="type-toggle" data-testid="product-type-toggle">
                  {['battery', 'inverter', 'trolley'].map(t => {
                    const M = typeMeta[t]; const IconX = M.icon;
                    return (
                      <button type="button" key={t}
                        className={`type-opt ${f.product_type === t ? 'sel ' + M.tone : ''}`}
                        data-testid={`product-type-${t}`}
                        onClick={() => setF({ ...f, product_type: t })}>
                        <IconX size={16} /> {M.label}
                      </button>
                    );
                  })}
                </div>
              </label>
              <label>Product name
                <input data-testid="quick-add-product-name" required
                  value={f.name} onChange={e => setF({ ...f, name: e.target.value })}
                  placeholder="Exide 180Ah Tubular" />
              </label>
              <div className="form-row">
                <label>Model
                  <input value={f.model} onChange={e => setF({ ...f, model: e.target.value })} />
                </label>
                <label>{f.product_type === 'inverter' ? 'Capacity (VA)' : 'Capacity'}
                  <input value={f.capacity}
                    onChange={e => setF({ ...f, capacity: e.target.value })}
                    placeholder={f.product_type === 'inverter' ? '850VA' : '150Ah'} />
                </label>
              </div>
              <label>Reorder level
                <input type="number" min="0" value={f.reorder_level}
                  onChange={e => setF({ ...f, reorder_level: e.target.value })} />
              </label>
            </>
          ) : (
            <>
              <label>{kind} name
                <input data-testid={`quick-add-${kind}-name`} required autoFocus
                  value={f.name} onChange={e => setF({ ...f, name: e.target.value })} />
              </label>
              {(kind === 'dealer' || kind === 'supplier') && (
                <div className="form-row">
                  <label>Phone
                    <input value={f.phone} onChange={e => setF({ ...f, phone: e.target.value })} />
                  </label>
                  <label>City
                    <input value={f.city} onChange={e => setF({ ...f, city: e.target.value })} />
                  </label>
                </div>
              )}
            </>
          )}
          <button data-testid={`save-quick-add-${kind}`} className="primary-btn full">
            Save {kind === 'product' ? 'product' : kind} <ChevronRight size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}

/* ================== TRANSACTION MODAL (cart) ================== */
function TransactionModal({ type, data, editing, onClose, onSaved }) {
  const [f, setF] = useState({
    party_id: editing?.party_id || '',
    reference: editing?.reference || '',
    notes: editing?.notes || '',
  });
  const initial = editing?.items?.map(x => ({ product_id: x.product_id, quantity: x.quantity }))
    || [];
  const [items, setItems] = useState(initial);
  const [pickerProduct, setPickerProduct] = useState('');
  const [pickerQty, setPickerQty] = useState(1);
  const partyKey = type === 'inward' ? 'suppliers' : 'dealers';

  const addToCart = () => {
    if (!pickerProduct) return;
    const existing = items.findIndex(i => i.product_id === pickerProduct);
    if (existing >= 0) {
      const copy = [...items];
      copy[existing] = { ...copy[existing], quantity: copy[existing].quantity + Number(pickerQty || 1) };
      setItems(copy);
    } else {
      setItems([...items, { product_id: pickerProduct, quantity: Number(pickerQty || 1) }]);
    }
    setPickerProduct(''); setPickerQty(1);
  };

  const updateQty = (idx, delta) => {
    const copy = [...items];
    copy[idx] = { ...copy[idx], quantity: Math.max(1, copy[idx].quantity + delta) };
    setItems(copy);
  };
  const setQty = (idx, v) => {
    const copy = [...items];
    copy[idx] = { ...copy[idx], quantity: Math.max(1, Number(v) || 1) };
    setItems(copy);
  };
  const removeItem = (idx) => setItems(items.filter((_, n) => n !== idx));

  const total = items.reduce((a, x) => a + x.quantity, 0);

  const submit = async (e) => {
    e.preventDefault();
    if (items.length === 0) {
      alert('Add at least one item to the cart');
      return;
    }
    const payload = {
      kind: type,
      party_id: f.party_id || null,
      reference: f.reference,
      notes: f.notes,
      items,
    };
    try {
      if (editing) await axios.put(`${API}/transactions/${editing.transaction_id}`, payload);
      else await axios.post(`${API}/transactions`, payload);
      onSaved();
    } catch (err) {
      alert(err.response?.data?.detail || 'Could not save movement');
    }
  };

  const productMeta = (id) => data.products.find(p => p.id === id) || {};
  const brandOf = (p) => data.brands.find(b => b.id === p.brand_id)?.name || '';

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <div className="modal wide" onMouseDown={e => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <div className="eyebrow blue">{editing ? 'CORRECT MOVEMENT' : (type === 'inward' ? 'STOCK IN' : 'STOCK OUT')}</div>
            <h3>{editing ? 'Edit movement' : (type === 'inward' ? 'Record stock in' : 'Record stock out')}</h3>
            <p>Pick a product, choose quantity, hit Add. Repeat for as many items as you like.</p>
          </div>
          <button data-testid="close-transaction-modal" className="close-btn" onClick={onClose}><X /></button>
        </div>

        <form onSubmit={submit}>
          <div className="quick-select">
            <label>{type === 'inward' ? 'Supplier' : 'Dealer'}
              <SearchSelect items={data[partyKey]} value={f.party_id}
                onChange={id => setF({ ...f, party_id: id })}
                placeholder={`Search ${type === 'inward' ? 'supplier' : 'dealer'}`}
                testId="transaction-party-search" label={partyKey} />
            </label>
            <label>Reference / invoice
              <input value={f.reference}
                onChange={e => setF({ ...f, reference: e.target.value })}
                placeholder="Optional" />
            </label>
          </div>

          <div className="cart-builder">
            <div className="cart-add-row">
              <SearchSelect items={data.products.filter(p => p.active !== false)}
                value={pickerProduct}
                onChange={id => setPickerProduct(id)}
                placeholder="Search battery, inverter or trolley"
                testId="cart-product-search" label="product"
                renderMeta={p => `${brandOf(p)} · ${typeMeta[p.product_type]?.label || 'Item'} · ${p.capacity || p.model || ''}`} />
              <div className="qty-input">
                <button type="button" className="qty-btn"
                  onClick={() => setPickerQty(Math.max(1, Number(pickerQty) - 1))}
                  data-testid="picker-qty-minus"><Minus size={14} /></button>
                <input data-testid="picker-qty-input" type="number" min="1"
                  value={pickerQty} onChange={e => setPickerQty(e.target.value)} />
                <button type="button" className="qty-btn"
                  onClick={() => setPickerQty(Number(pickerQty) + 1)}
                  data-testid="picker-qty-plus"><Plus size={14} /></button>
              </div>
              <button type="button" data-testid="add-to-cart-button"
                className="add-cart-btn" onClick={addToCart}
                disabled={!pickerProduct}>
                <Plus size={14} /> Add
              </button>
            </div>

            <div className="cart-list" data-testid="cart-list">
              {items.length === 0 && (
                <div className="cart-empty">
                  No items yet. Pick a product above and hit <b>Add</b>.
                </div>
              )}
              {items.map((it, i) => {
                const p = productMeta(it.product_id);
                const M = typeMeta[p.product_type] || typeMeta.battery;
                const IconX = M.icon;
                return (
                  <div className="cart-item" key={i} data-testid={`cart-item-${i}`}>
                    <span className={`type-icon ${M.tone}`}><IconX size={16} /></span>
                    <div className="cart-item-body">
                      <b>{p.name || 'Product'}</b>
                      <small>{brandOf(p)} · {M.label} · {p.capacity || p.model || '—'}</small>
                    </div>
                    <div className="qty-input">
                      <button type="button" className="qty-btn"
                        onClick={() => updateQty(i, -1)}
                        data-testid={`cart-qty-minus-${i}`}><Minus size={14} /></button>
                      <input type="number" min="1" value={it.quantity}
                        data-testid={`cart-qty-input-${i}`}
                        onChange={e => setQty(i, e.target.value)} />
                      <button type="button" className="qty-btn"
                        onClick={() => updateQty(i, +1)}
                        data-testid={`cart-qty-plus-${i}`}><Plus size={14} /></button>
                    </div>
                    <button type="button" className="remove-btn"
                      data-testid={`cart-remove-${i}`}
                      onClick={() => removeItem(i)}><Trash2 size={15} /></button>
                  </div>
                );
              })}
            </div>

            {items.length > 0 && (
              <div className="cart-footer">
                <span>{items.length} product{items.length !== 1 ? 's' : ''}</span>
                <strong data-testid="cart-total-qty">{total} units</strong>
              </div>
            )}
          </div>

          <label>Notes
            <input value={f.notes} onChange={e => setF({ ...f, notes: e.target.value })}
              placeholder="Optional" />
          </label>

          <button data-testid="save-transaction-button" className="primary-btn full"
            disabled={items.length === 0}>
            {editing ? 'Save correction' : (type === 'inward' ? 'Post Stock In' : 'Post Stock Out')}
            <ChevronRight size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}

/* ================== DIRECTORY (Dealers / Suppliers) ================== */
function Directory({ kind, items, onSelect, setQuick }) {
  const [q, setQ] = useState('');
  const label = kind === 'dealer' ? 'Dealer' : 'Supplier';
  const filtered = items.filter(d =>
    [d.name, d.city || '', d.phone || ''].join(' ').toLowerCase().includes(q.toLowerCase())
  );
  return (
    <div className="content">
      <div className="directory-head">
        <div>
          <div className="eyebrow blue">{label.toUpperCase()}S</div>
          <h2>{label} directory</h2>
          <p>Open any {label.toLowerCase()} for complete history and totals.</p>
        </div>
        <button className="primary-btn" onClick={() => setQuick(kind)}
          data-testid={`new-${kind}-button`}>
          <Plus size={16} /> New {kind}
        </button>
      </div>

      <div className="toolbar">
        <div className="searchbox">
          <Search size={17} />
          <input data-testid={`${kind}-search-input`} value={q}
            onChange={e => setQ(e.target.value)}
            placeholder={`Search ${kind} by name, city or phone...`} />
        </div>
      </div>

      <div className="dealer-grid">
        {filtered.map(d => (
          <button className="dealer-card" key={d.id}
            data-testid={`${kind}-card-${d.id}`}
            onClick={() => onSelect(d.id)}>
            <span className="dealer-avatar">{d.name[0]}</span>
            <span>
              <b>{d.name}</b>
              <small>{d.city || 'No city'} · {d.phone || 'No phone'}</small>
              <em>Open history <ChevronRight size={13} /></em>
            </span>
          </button>
        ))}
        {filtered.length === 0 && items.length > 0 && (
          <div className="empty">No {kind} matches "{q}".</div>
        )}
        {items.length === 0 && (
          <div className="empty product-empty">
            No {kind}s yet. Click <b>New {kind}</b> to add one.
          </div>
        )}
      </div>
    </div>
  );
}

/* ================== PARTY PROFILE (Dealer or Supplier) ================== */
function PartyProfile({ id, kind, onClose }) {
  const [p, setP] = useState(null);
  useEffect(() => {
    const path = kind === 'dealer' ? 'dealers' : 'suppliers';
    axios.get(`${API}/${path}/${id}/profile`).then(r => setP(r.data));
  }, [id, kind]);
  if (!p) return <div className="drawer-backdrop"><aside className="drawer">Loading…</aside></div>;
  const s = p.summary;
  const heading = kind === 'dealer' ? 'DEALER' : 'SUPPLIER';
  return (
    <div className="drawer-backdrop" onMouseDown={onClose}>
      <aside className="drawer" onMouseDown={e => e.stopPropagation()}
        data-testid={`${kind}-profile`}>
        <button className="close-btn" onClick={onClose}><X /></button>
        <div className="dealer-hero">
          <span className="dealer-avatar big">{p.party.name[0]}</span>
          <div>
            <div className="eyebrow blue">{heading}</div>
            <h2>{p.party.name}</h2>
            <p>{p.party.city || '—'} · {p.party.phone || '—'}</p>
          </div>
        </div>
        <div className="profile-grid">
          <div><small>UNITS {p.key_label}</small><strong>{s.total_units}</strong><span>all time</span></div>
          <div><small>MOVEMENTS</small><strong>{s.total_orders}</strong><span>orders</span></div>
          <div><small>TOP BRAND</small><strong className="small-strong">{s.top_brand}</strong><span>most sent</span></div>
          <div><small>LAST MOVEMENT</small>
            <strong className="small-strong">
              {s.last_transaction ? new Date(s.last_transaction).toLocaleDateString() : '—'}
            </strong>
            <span>most recent</span>
          </div>
        </div>
        <div className="panel-head">
          <div><div className="eyebrow">HISTORY</div><h3>What went where</h3></div>
        </div>
        {p.history.length === 0 && <div className="empty">No movements yet for this {kind}.</div>}
        {p.history.map((h, i) => {
          const M = typeMeta[h.product_type] || typeMeta.battery;
          const IconX = M.icon;
          return (
            <div className="history-row" key={`${h.transaction_id}-${i}`}>
              <span className={`type-icon ${M.tone}`}><IconX size={15} /></span>
              <div>
                <b>{h.transaction_id}</b>
                <small>{new Date(h.date).toLocaleString()} · {h.brand} · {h.model}</small>
              </div>
              <strong>{h.quantity} units</strong>
            </div>
          );
        })}
      </aside>
    </div>
  );
}

/* ================== SETTINGS ================== */
function SettingsPage({ onReset }) {
  const [busy, setBusy] = useState(false);
  const doReset = async () => {
    const ok = window.confirm(
      'This will permanently wipe ALL data: brands, products, dealers, suppliers, stock and history.\n\nType YES in the next prompt to confirm.'
    );
    if (!ok) return;
    const typed = window.prompt('Type YES to confirm reset');
    if (typed !== 'YES') return;
    setBusy(true);
    try {
      await axios.post(`${API}/admin/reset`);
      onReset();
      alert('All data cleared. You have a fresh canvas.');
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="content">
      <div className="directory-head">
        <div>
          <div className="eyebrow blue">SETTINGS</div>
          <h2>Workspace controls</h2>
          <p>Administrative actions. Use with care.</p>
        </div>
      </div>
      <div className="settings-card danger">
        <div className="settings-icon"><RefreshCcw size={22} /></div>
        <div className="settings-body">
          <b>Reset everything</b>
          <p>Erase all brands, products, dealers, suppliers, stock and history. This cannot be undone.</p>
        </div>
        <button data-testid="reset-all-button" className="danger-btn"
          disabled={busy} onClick={doReset}>
          {busy ? 'Resetting…' : 'Reset all data'}
        </button>
      </div>
    </div>
  );
}
