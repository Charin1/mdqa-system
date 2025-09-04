import { NavLink } from 'react-router-dom';
import { Upload, Library, MessageSquare, BarChart2, Settings } from 'lucide-react';
// CORRECTED: Import the new ChatHistory component
import { ChatHistory } from './ChatHistory';

const navItems = [
  { to: '/', icon: Upload, label: 'Upload' },
  { to: '/library', icon: Library, label: 'Library' },
  { to: '/chat', icon: MessageSquare, label: 'Chat' },
  { to: '/analytics', icon: BarChart2, label: 'Analytics' },
  { to: '/config', icon: Settings, label: 'Config' },
];

const Sidebar = () => {
  return (
    <aside className="w-64 bg-card border-r border-muted flex flex-col">
      <div className="p-6 flex items-center gap-3">
        <img src="/mdqa-logo.svg" alt="MDQA System Logo" className="h-8 w-8" />
        <h1 className="text-2xl font-bold">MDQA-System</h1>
      </div>
      <nav className="px-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2 my-1 rounded-md transition-colors ${
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted text-muted-foreground hover:text-foreground'
              }`
            }
          >
            <item.icon size={20} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      
      {/* CORRECTED: Render the ChatHistory component here */}
      <div className="flex-1 overflow-y-auto">
        <ChatHistory />
      </div>

      <div className="p-4 text-xs text-muted-foreground">
        Version 1.0.0
      </div>
    </aside>
  );
};

export default Sidebar;