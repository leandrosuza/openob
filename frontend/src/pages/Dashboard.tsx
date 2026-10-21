import { useEffect, useState } from 'react';
import { authService } from '../services/auth';
import type { User } from '../types/auth';

export default function Dashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userData = await authService.getCurrentUser();
        setUser(userData);
      } catch (err) {
        console.error('Erro ao carregar usuário:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, []);

  if (loading) {
    return <div className="p-8">Carregando...</div>;
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-dark mb-2">Dashboard</h1>
        <p className="text-secondary">Visão geral da sua conta</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-dark">Saldo</h3>
            <span className="text-2xl">💰</span>
          </div>
          <p className="text-3xl font-bold text-primary">${user?.balance?.toFixed(2) || '0.00'}</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-dark">Plano</h3>
            <span className="text-2xl">📦</span>
          </div>
          <p className="text-xl font-medium text-secondary">{user?.plan_id || 'Free'}</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-dark">Status</h3>
            <span className="text-2xl">{user?.is_active ? '✅' : '❌'}</span>
          </div>
          <p className={`text-xl font-medium ${user?.is_active ? 'text-green-600' : 'text-red-600'}`}>
            {user?.is_active ? 'Ativo' : 'Inativo'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-bold text-dark mb-4">Informações da Conta</h2>
          <div className="space-y-3">
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-secondary">Usuário</span>
              <span className="font-medium text-dark">{user?.username}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-secondary">Email</span>
              <span className="font-medium text-dark">{user?.email}</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-secondary">Subscription ID</span>
              <span className="font-medium text-dark">{user?.current_subscription_id || 'N/A'}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="text-xl font-bold text-dark mb-4">Ações Rápidas</h2>
          <div className="space-y-3">
            <button className="w-full btn-primary flex items-center justify-center gap-2">
              <span>🤖</span>
              Configurar Autotrade
            </button>
            <button className="w-full btn-secondary flex items-center justify-center gap-2">
              <span>📈</span>
              Ver Estratégias
            </button>
            <button className="w-full btn-secondary flex items-center justify-center gap-2">
              <span>⚙️</span>
              Configurações
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
