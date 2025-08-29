
import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { LogoutIcon, UserIcon } from '../ui/icons';

const Header: React.FC = () => {
  const { logout } = useAuth();

  return (
    <header className="bg-primary p-4 flex justify-end items-center border-b border-secondary">
      <div className="flex items-center space-x-4">
        <div className="p-2 bg-secondary rounded-full">
            <UserIcon className="w-6 h-6 text-light" />
        </div>
        <button onClick={logout} className="p-2 rounded-full bg-secondary hover:bg-red-500 transition-colors">
          <LogoutIcon className="w-6 h-6 text-light" />
        </button>
      </div>
    </header>
  );
};

export default Header;
