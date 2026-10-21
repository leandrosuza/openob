import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/auth';
import type { User } from '../types/auth';

export default function Dashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userData = await authService.getCurrentUser();
        setUser(userData);
      } catch (err) {
        navigate('/login');
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [navigate]);

  const handleLogout = async () => {
    await authService.logout();
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-light">
        <div className="text-secondary">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-light">
      <nav className="bg-white border-b border-gray-100 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <h1 className="text-xl font-bold text-dark">OpenOB</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-secondary">{user?.username}</span>
            <button
              onClick={handleLogout}
              className="text-sm text-primary hover:underline"
            >
              Sair
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="card mb-6">
          <h2 className="text-2xl font-bold text-dark mb-4">Bem-vindo, {user?.username}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-light p-4 rounded-lg">
              <p className="text-sm text-secondary mb-1">Saldo</p>
              <p className="text-2xl font-bold text-dark">${user?.balance.toFixed(2)}</p>
            </div>
            <div className="bg-light p-4 rounded-lg">
              <p className="text-sm text-secondary mb-1">Status</p>
              <p className="text-2xl font-bold text-dark">
                {user?.is_active ? 'Ativo' : 'Inativo'}
              </p>
            </div>
            <div className="bg-light p-4 rounded-lg">
              <p className="text-sm text-secondary mb-1">Plano</p>
              <p className="text-2xl font-bold text-dark">
                {user?.plan_id ? 'Premium' : 'Free'}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-dark mb-4">Funcionalidades</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button className="btn-secondary text-left">
              Gerenciar Conexão
            </button>
            <button className="btn-secondary text-left">
              Configurar Autotrade
            </button>
            <button className="btn-secondary text-left">
              Monitorar Ativos
            </button>
            <button className="btn-secondary text-left">
              Histórico de Trades
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
