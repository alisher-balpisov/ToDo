
import React from 'react';
import { UserIcon, ShareIcon } from '../ui/icons';

type ViewType = 'my_tasks' | 'shared_tasks' | 'stats';

interface SidebarProps {
  currentView: ViewType;
  setView: (view: ViewType) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentView, setView }) => {
    const navItems = [
        { id: 'my_tasks', label: 'My Tasks', icon: <UserIcon className="w-6 h-6" /> },
        { id: 'shared_tasks', label: 'Shared With Me', icon: <ShareIcon className="w-6 h-6" /> },
        { id: 'stats', label: 'Statistics', icon: <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
  <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75c0 .621-.504 1.125-1.125 1.125h-2.25A1.125 1.125 0 013 20.25v-7.125zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
</svg>
 },
    ];
    
  return (
    <nav className="w-64 bg-primary p-4 flex flex-col border-r border-secondary">
      <div className="mb-8 text-2xl font-bold text-center text-accent">
        TodoApp
      </div>
      <ul className="space-y-2">
        {navItems.map(item => (
            <li key={item.id}>
                 <button
                    onClick={() => setView(item.id as ViewType)}
                    className={`w-full flex items-center p-3 rounded-lg transition-colors ${
                        currentView === item.id 
                        ? 'bg-accent text-white' 
                        : 'text-gray-300 hover:bg-secondary hover:text-white'
                    }`}
                >
                    {item.icon}
                    <span className="ml-4">{item.label}</span>
                </button>
            </li>
        ))}
      </ul>
    </nav>
  );
};

export default Sidebar;
