import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/', label: 'Budget', icon: '📊' },
  { to: '/import', label: 'Import CSV', icon: '📥' },
];

export default function Sidebar() {
  return (
    <aside className="w-56 shrink-0 h-screen bg-bg-sidebar border-r border-border-card flex flex-col sticky top-0">
      <div className="px-5 py-6">
        <h1 className="text-lg font-bold text-accent tracking-wide">Finance Manager</h1>
      </div>
      <nav className="flex-1 px-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-accent/15 text-accent font-medium'
                  : 'text-text-secondary hover:text-text-primary hover:bg-white/5'
              }`
            }
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
