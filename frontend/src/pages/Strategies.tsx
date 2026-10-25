import { useState, useEffect } from 'react';
import api from '../services/api';

interface Strategy {
  name: string;
  class_name: string;
  description: string;
  required_parameters: string[];
}

export default function Strategies() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      const response = await api.get('/autotrade/strategies');
      setStrategies(response.data);
    } catch (error) {
      console.error('Erro ao buscar estratégias:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-secondary">Carregando estratégias...</p>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-dark mb-2">Estratégias</h1>
        <p className="text-secondary">Gerencie suas estratégias de trading</p>
      </div>

      {strategies.length === 0 ? (
        <div className="card">
          <p className="text-secondary">Nenhuma estratégia disponível no momento.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {strategies.map((strategy) => (
            <div key={strategy.name} className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-dark capitalize">
                  {strategy.name.replace(/([A-Z])/g, ' $1').trim()}
                </h3>
                <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                  Ativo
                </span>
              </div>
              <p className="text-sm text-secondary mb-4">
                {strategy.description}
              </p>
              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2 text-sm">
                  <span>📊</span>
                  <span className="text-secondary">{strategy.required_parameters.length} parâmetros</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <span>📈</span>
                  <span className="text-secondary">
                    {strategy.required_parameters.slice(0, 3).join(', ')}
                    {strategy.required_parameters.length > 3 && '...'}
                  </span>
                </div>
              </div>
              <button className="w-full btn-secondary">Selecionar</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
