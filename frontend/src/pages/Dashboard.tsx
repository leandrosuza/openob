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
            <span className="text-xl">$</span>
          </div>
          <p className="text-3xl font-bold text-primary">${user?.balance?.toFixed(2) || '0.00'}</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-dark">Plano</h3>
          </div>
          <p className="text-xl font-medium text-secondary">{user?.plan_id || 'Free'}</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-dark">Status</h3>
          </div>
          <span className={`badge ${user?.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {user?.is_active ? 'Ativo' : 'Inativo'}
          </span>
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
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-secondary">Plano</span>
              <span className="font-medium text-dark">{user?.plan_id || 'Free'}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-secondary">Status</span>
              <span className={`badge ${user?.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                {user?.is_active ? 'Ativo' : 'Inativo'}
              </span>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="text-xl font-bold text-dark mb-4">Ações Rápidas</h2>
          <div className="space-y-3">
            <button className="btn-primary w-full flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Configurar Autotrade
            </button>
            <button className="btn-secondary w-full flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              Ver Estratégias
            </button>
            <button className="btn-secondary w-full flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c0 .37-.032.74-.103 1.105a1.724 1.724 0 001.066 2.573c1.465-1.543 2.37-2.37 2.37-2.37a1.724 1.724 0 002.573-1.066c.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.572c0-.37.032-.74.103-1.105a1.724 1.724 0 00-1.065-2.573c-1.465 1.543-2.37 2.37-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.065z" />
              </svg>
              Configurações
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
