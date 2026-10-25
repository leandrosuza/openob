import { useState, useEffect } from 'react';
import api from '../services/api';
import { authService } from '../services/auth';
import { Play, Square, TrendingUp, DollarSign, Activity, Target } from 'lucide-react';

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

interface Strategy {
  name: string;
  class_name: string;
  description: string;
  required_parameters: string[];
}

export default function Autotrade() {
  const [config, setConfig] = useState<AutotradeConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [userId, setUserId] = useState<number | null>(null);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('');
  const [selectedAmount, setSelectedAmount] = useState<number>(5.0);

  // Buscar usuário, config e estratégias
  useEffect(() => {
    fetchUserAndConfig();
    fetchStrategies();
  }, []);

  const fetchUserAndConfig = async () => {
    try {
      const user = await authService.getCurrentUser();
      setUserId(user.id);

      const response = await api.get(`/autotrade/configs/${user.id}`);
      setConfig(response.data);
      setSelectedStrategy(response.data.strategy_name);
      setSelectedAmount(response.data.amount);
    } catch (error) {
      console.error('Erro ao buscar usuário, usando localStorage:', error);
      const localUserId = localStorage.getItem('user_id');
      if (localUserId) {
        setUserId(parseInt(localUserId));
        try {
          const response = await api.get(`/autotrade/configs/${localUserId}`);
          setConfig(response.data);
          setSelectedStrategy(response.data.strategy_name);
          setSelectedAmount(response.data.amount);
        } catch (configError) {
          console.error('Erro ao buscar config:', configError);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchStrategies = async () => {
    try {
      const response = await api.get('/autotrade/strategies');
      setStrategies(response.data);
    } catch (error) {
      console.error('Erro ao buscar estratégias:', error);
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

  const updateConfig = async () => {
    if (!config || !userId) return;

    setUpdating(true);
    try {
      const response = await api.put(`/autotrade/configs/${userId}`, {
        ...config,
        strategy_name: selectedStrategy,
        amount: selectedAmount
      });
      setConfig(response.data);
      alert('Configuração atualizada com sucesso!');
    } catch (error) {
      console.error('Erro ao atualizar config:', error);
      alert('Erro ao atualizar configuração');
    } finally {
      setUpdating(false);
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
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Autotrade</h1>
        <p className="text-gray-600 dark:text-gray-400">Configure o trading automatizado</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Configuração Atual</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">Status</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                config.is_active
                  ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                  : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
              }`}>
                {config.is_active ? 'Ativo' : 'Inativo'}
              </span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">Estratégia</span>
              <span className="font-medium text-gray-900 dark:text-gray-100 capitalize">
                {config.strategy_name.replace(/([A-Z])/g, ' $1').trim()}
              </span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">Amount</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">${config.amount.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between py-3">
              <span className="text-gray-600 dark:text-gray-400">Ativos</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">Automático</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Controles</h2>
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
              {config.is_active ? <Square className="w-5 h-5" /> : <Play className="w-5 h-5" />}
              {toggling ? 'Processando...' : config.is_active ? 'Parar Autotrade' : 'Iniciar Autotrade'}
            </button>
            <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
              {config.is_active
                ? 'Ao parar, a conexão com a corretora será encerrada'
                : 'Ao iniciar, o sistema conectará automaticamente à corretora'}
            </p>
          </div>
        </div>
      </div>

      <div className="card mt-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Selecionar Estratégia</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Estratégia</label>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              disabled={config.is_active}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            >
              {strategies.map((strategy) => (
                <option key={strategy.name} value={strategy.name}>
                  {strategy.name} - {strategy.description}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Amount ($)</label>
            <input
              type="number"
              step="0.01"
              min="1"
              value={selectedAmount}
              onChange={(e) => setSelectedAmount(parseFloat(e.target.value))}
              disabled={config.is_active}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            />
          </div>

          <button
            onClick={updateConfig}
            disabled={updating || config.is_active}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {updating ? 'Atualizando...' : 'Selecionar'}
          </button>

          {config.is_active && (
            <p className="text-sm text-orange-600 dark:text-orange-400 text-center">
              Pare o autotrade antes de alterar a configuração
            </p>
          )}
        </div>
      </div>

      <div className="card mt-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Estatísticas</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Activity className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <p className="text-sm text-gray-600 dark:text-gray-400">Trades Hoje</p>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">0</p>
          </div>
          <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <DollarSign className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <p className="text-sm text-gray-600 dark:text-gray-400">Lucro Hoje</p>
            </div>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">$0.00</p>
          </div>
          <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Target className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <p className="text-sm text-gray-600 dark:text-gray-400">Win Rate</p>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">0%</p>
          </div>
          <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <p className="text-sm text-gray-600 dark:text-gray-400">Trades Totais</p>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">0</p>
          </div>
        </div>
      </div>
    </div>
  );
}
