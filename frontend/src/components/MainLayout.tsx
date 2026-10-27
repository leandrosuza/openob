import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { authService } from '../services/auth';
import { LayoutDashboard, Bot, Settings, LogOut } from 'lucide-react';

export default function MainLayout() {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  const menuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/autotrade', label: 'Autotrade', icon: Bot },
    { path: '/settings', label: 'Configurações', icon: Settings },
  ];

  return (
    <div className="min-h-screen flex bg-light-50 dark:bg-dark-900">
      <aside className="w-64 bg-white dark:bg-dark-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h1 className="text-2xl font-bold text-primary-600 dark:text-primary-400">OpenOB</h1>
          <p className="text-xs text-secondary-500 dark:text-secondary-400 mt-1">Trading Algorítmico</p>
        </div>

        <nav className="flex-1 p-4">
          <ul className="space-y-1">
            {menuItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-primary-600 text-white dark:bg-primary-700'
                        : 'text-secondary-600 dark:text-secondary-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="font-medium text-sm">{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-secondary-600 dark:text-secondary-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-sm"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Sair</span>
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
