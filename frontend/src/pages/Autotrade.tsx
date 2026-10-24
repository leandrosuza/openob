import { useState, useEffect } from 'react';
import api from '../services/api';
import { authService } from '../services/auth';

interface AutotradeConfig {
  id?: number;
  user_id: number;
  strategy_name: string;
  parameters: Record<string, any>;
  amount: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export default function Autotrade() {
  const [config, setConfig] = useState<AutotradeConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [userId, setUserId] = useState<number | null>(null);

  // Buscar usuário atual e config
  useEffect(() => {
    fetchUserAndConfig();
  }, []);

  const fetchUserAndConfig = async () => {
    try {
      const user = await authService.getCurrentUser();
      setUserId(user.id);

      const response = await api.get(`/autotrade/configs/${user.id}`);
      setConfig(response.data);
    } catch (error) {
      console.error('Erro ao buscar usuário, usando localStorage:', error);
      // Fallback para localStorage
      const localUserId = localStorage.getItem('user_id');
      if (localUserId) {
        setUserId(parseInt(localUserId));
        try {
          const response = await api.get(`/autotrade/configs/${localUserId}`);
          setConfig(response.data);
        } catch (configError) {
          console.error('Erro ao buscar config:', configError);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleAutotrade = async () => {
    if (!config || !userId) return;

    setToggling(true);
    try {
      const response = await api.patch(`/autotrade/configs/${userId}/toggle`);
      setConfig(response.data);
    } catch (error) {
      console.error('Erro ao alternar autotrade:', error);
      alert('Erro ao alternar autotrade');
    } finally {
      setToggling(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-secondary">Carregando...</p>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-dark mb-2">Autotrade</h1>
          <p className="text-secondary">Configure o trading automatizado</p>
        </div>
        <div className="card">
          <p className="text-secondary mb-4">Nenhuma configuração encontrada. Configure o autotrade primeiro.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-dark mb-2">Autotrade</h1>
        <p className="text-secondary">Configure o trading automatizado</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-bold text-dark mb-4">Configuração Atual</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <span className="text-secondary">Status</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                config.is_active 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-gray-100 text-secondary'
              }`}>
                {config.is_active ? 'Ativo' : 'Inativo'}
              </span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <span className="text-secondary">Estratégia</span>
              <span className="font-medium text-dark capitalize">
                {config.strategy_name.replace(/([A-Z])/g, ' $1').trim()}
              </span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <span className="text-secondary">Amount</span>
              <span className="font-medium text-dark">${config.amount.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between py-3">
              <span className="text-secondary">Ativos</span>
              <span className="font-medium text-dark">Automático</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="text-xl font-bold text-dark mb-4">Controles</h2>
          <div className="space-y-4">
            <button
              onClick={toggleAutotrade}
              disabled={toggling}
              className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors ${
                config.is_active
                  ? 'bg-red-500 hover:bg-red-600 text-white'
                  : 'bg-green-500 hover:bg-green-600 text-white'
              } ${toggling ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span>{config.is_active ? '⏹️' : '▶️'}</span>
              {toggling ? 'Processando...' : config.is_active ? 'Parar Autotrade' : 'Iniciar Autotrade'}
            </button>
            <p className="text-sm text-secondary text-center">
              {config.is_active 
                ? 'Ao parar, a conexão com a corretora será encerrada'
                : 'Ao iniciar, o sistema conectará automaticamente à corretora'}
            </p>
          </div>
        </div>
      </div>

      <div className="card mt-6">
        <h2 className="text-xl font-bold text-dark mb-4">Estatísticas</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-light p-4 rounded-lg">
            <p className="text-sm text-secondary mb-1">Trades Hoje</p>
            <p className="text-2xl font-bold text-dark">0</p>
          </div>
          <div className="bg-light p-4 rounded-lg">
            <p className="text-sm text-secondary mb-1">Lucro Hoje</p>
            <p className="text-2xl font-bold text-green-600">$0.00</p>
          </div>
          <div className="bg-light p-4 rounded-lg">
            <p className="text-sm text-secondary mb-1">Win Rate</p>
            <p className="text-2xl font-bold text-dark">0%</p>
          </div>
          <div className="bg-light p-4 rounded-lg">
            <p className="text-sm text-secondary mb-1">Trades Totais</p>
            <p className="text-2xl font-bold text-dark">0</p>
          </div>
        </div>
      </div>
    </div>
  );
}
