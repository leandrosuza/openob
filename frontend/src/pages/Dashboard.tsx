import { useEffect, useState } from 'react';
import { authService } from '../services/auth';
import { autotradeService } from '../services/autotrade';
import { userService } from '../services/user';
import type { User } from '../types/auth';
import type { AutotradeConfig } from '../types/auth';

export default function Dashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [autotradeConfig, setAutotradeConfig] = useState<AutotradeConfig | null>(null);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [showSSID, setShowSSID] = useState(false);

  // Form states
  const [ssidDemo, setSsidDemo] = useState('');
  const [ssidReal, setSsidReal] = useState('');
  const [mode, setMode] = useState<'demo' | 'real'>('demo');
  const [strategyName, setStrategyName] = useState('');
  const [amount, setAmount] = useState(5);
  const [autotradeActive, setAutotradeActive] = useState(false);
  const [sorosEnabled, setSorosEnabled] = useState(false);
  const [sorosTargetAmount, setSorosTargetAmount] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const userData = await authService.getCurrentUser();
        setUser(userData);

        // Preencher campos SSID e modo
        setSsidDemo(userData.ssid_demo || '');
        setSsidReal(userData.ssid_real || '');
        setMode(userData.mode || 'demo');

        // Carregar estratégias
        const strategiesData = await autotradeService.getStrategies();
        setStrategies(strategiesData);

        // Carregar config de autotrade se existir
        try {
          const config = await autotradeService.getConfig(userData.id);
          setAutotradeConfig(config);
          setStrategyName(config.strategy_name);
          setAmount(config.amount);
          setAutotradeActive(config.is_active);
          setSorosEnabled(config.soros_enabled);
          setSorosTargetAmount(config.soros_target_amount);
        } catch (err) {
          // Config não existe ainda - usar valores padrão
          setStrategyName('');
          setAmount(5);
          setAutotradeActive(false);
          setSorosEnabled(false);
          setSorosTargetAmount(0);
        }
      } catch (err) {
        console.error('Erro ao carregar dados:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleSaveSSID = async () => {
    try {
      await userService.updateSSID(user!.id, ssidDemo || null, ssidReal || null);
      await userService.updateMode(user!.id, mode);

      // Recarregar dados do usuário
      const userData = await authService.getCurrentUser();
      setUser(userData);
      setSsidDemo(userData.ssid_demo || '');
      setSsidReal(userData.ssid_real || '');
      setMode(userData.mode || 'demo');

      alert('SSID atualizado com sucesso!');
    } catch (err: any) {
      alert('Erro ao atualizar SSID: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleSaveAutotrade = async () => {
    try {
      if (autotradeConfig) {
        await autotradeService.updateConfig(user!.id, {
          ...autotradeConfig,
          strategy_name: strategyName,
          amount,
          is_active: autotradeActive,
          soros_enabled: sorosEnabled,
          soros_target_amount: sorosTargetAmount
        });
      } else {
        await autotradeService.createConfig({
          user_id: user!.id,
          strategy_name: strategyName,
          parameters: {},
          amount,
          is_active: autotradeActive,
          soros_enabled: sorosEnabled,
          soros_target_amount: sorosTargetAmount
        });
      }
      alert('Configuração de autotrade salva!');
    } catch (err: any) {
      alert('Erro ao salvar autotrade: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleToggleAutotrade = async () => {
    try {
      const updated = await autotradeService.toggleConfig(user!.id);
      setAutotradeConfig(updated);
      setAutotradeActive(updated.is_active);
    } catch (err: any) {
      alert('Erro ao alternar autotrade: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) {
    return <div className="text-gray-600">Carregando...</div>;
  }

  return (
    <div className="space-y-8">
      {/* Seção de Informações do Usuário */}
      <section>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Minha Conta</h2>
        <div className="bg-white border border-gray-200 rounded-lg">
          <div className="divide-y divide-gray-200">
            <div className="flex justify-between items-center px-6 py-4">
              <span className="text-sm text-gray-600">Usuário</span>
              <span className="text-sm font-medium text-gray-900">{user?.username}</span>
            </div>
            <div className="flex justify-between items-center px-6 py-4">
              <span className="text-sm text-gray-600">Email</span>
              <span className="text-sm font-medium text-gray-900">{user?.email}</span>
            </div>
            <div className="flex justify-between items-center px-6 py-4">
              <span className="text-sm text-gray-600">Plano</span>
              <span className="text-sm font-medium text-gray-900">{user?.plan_id || 'Free'}</span>
            </div>
            <div className="flex justify-between items-center px-6 py-4">
              <span className="text-sm text-gray-600">Status</span>
              <span className={`text-sm font-medium ${user?.is_active ? 'text-green-600' : 'text-red-600'}`}>
                {user?.is_active ? 'Ativo' : 'Inativo'}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Seção de SSID */}
      <section>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Configuração de Trading</h2>
        <div className="bg-white border border-gray-200 rounded-lg">
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm text-gray-600 mb-2">SSID Demo</label>
              <input
                type={showSSID ? 'text' : 'password'}
                value={ssidDemo}
                onChange={(e) => setSsidDemo(e.target.value)}
                className="input-field"
                placeholder="SSID da conta demo"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-2">SSID Real</label>
              <input
                type={showSSID ? 'text' : 'password'}
                value={ssidReal}
                onChange={(e) => setSsidReal(e.target.value)}
                className="input-field"
                placeholder="SSID da conta real"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="showSSID"
                checked={showSSID}
                onChange={(e) => setShowSSID(e.target.checked)}
                className="w-4 h-4"
              />
              <label htmlFor="showSSID" className="text-sm text-gray-600">Mostrar SSID</label>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-2">Modo de Trading</label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value as 'demo' | 'real')}
                className="input-field"
              >
                <option value="demo">Demo</option>
                <option value="real">Real</option>
              </select>
            </div>
            <button
              onClick={handleSaveSSID}
              className="btn-primary"
            >
              Salvar Configuração
            </button>
          </div>
        </div>
      </section>

      {/* Seção de Autotrade */}
      <section>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Autotrade</h2>
        <div className="bg-white border border-gray-200 rounded-lg">
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm text-gray-600 mb-2">Estratégia</label>
              <select
                value={strategyName}
                onChange={(e) => setStrategyName(e.target.value)}
                className="input-field"
              >
                <option value="">Selecione uma estratégia</option>
                {strategies.map((strategy: any) => (
                  <option key={strategy.name} value={strategy.name}>{strategy.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-2">Valor por Trade ($)</label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(parseFloat(e.target.value))}
                className="input-field"
                min="1"
                step="0.5"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="sorosEnabled"
                checked={sorosEnabled}
                onChange={(e) => setSorosEnabled(e.target.checked)}
                className="w-4 h-4"
              />
              <label htmlFor="sorosEnabled" className="text-sm text-gray-600">Habilitar Soros</label>
            </div>
            {sorosEnabled && (
              <div>
                <label className="block text-sm text-gray-600 mb-2">Valor Alvo Soros ($)</label>
                <input
                  type="number"
                  value={sorosTargetAmount}
                  onChange={(e) => setSorosTargetAmount(parseFloat(e.target.value))}
                  className="input-field"
                  min="0"
                  step="0.5"
                  placeholder="0 = lucro contínuo"
                />
                <p className="text-xs text-gray-500 mt-1">Ao atingir este valor, volta ao valor original</p>
              </div>
            )}
            <div className="flex items-center gap-4">
              <button
                onClick={handleSaveAutotrade}
                className="btn-primary"
              >
                Salvar Configuração
              </button>
              {autotradeConfig && (
                <button
                  onClick={handleToggleAutotrade}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    autotradeActive
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-green-600 hover:bg-green-700 text-white'
                  }`}
                >
                  {autotradeActive ? 'Parar Autotrade' : 'Iniciar Autotrade'}
                </button>
              )}
            </div>
            {autotradeConfig && (
              <div className="text-sm text-gray-600">
                Status: <span className={autotradeActive ? 'text-green-600' : 'text-red-600'}>
                  {autotradeActive ? 'Ativo' : 'Inativo'}
                </span>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
