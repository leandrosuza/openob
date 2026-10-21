export default function Strategies() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-dark mb-2">Estratégias</h1>
        <p className="text-secondary">Gerencie suas estratégias de trading</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-dark">Scalping 5s</h3>
            <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
              Ativo
            </span>
          </div>
          <p className="text-sm text-secondary mb-4">
            Estratégia de scalping com timeframe de 5 segundos, usando indicadores de tendência e momentum.
          </p>
          <div className="space-y-2 mb-4">
            <div className="flex items-center gap-2 text-sm">
              <span>📊</span>
              <span className="text-secondary">MA Curto Prazo</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span>📈</span>
              <span className="text-secondary">RSI</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span>🎯</span>
              <span className="text-secondary">Confluência</span>
            </div>
          </div>
          <button className="w-full btn-secondary">Configurar</button>
        </div>

        <div className="card opacity-60">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-dark">Trend Following</h3>
            <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium">
              Em Breve
            </span>
          </div>
          <p className="text-sm text-secondary mb-4">
            Estratégia de acompanhamento de tendência com médias móveis e confirmação de volume.
          </p>
          <div className="space-y-2 mb-4">
            <div className="flex items-center gap-2 text-sm">
              <span>📊</span>
              <span className="text-secondary">EMA 20/50</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span>📈</span>
              <span className="text-secondary">MACD</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span>🎯</span>
              <span className="text-secondary">Volume</span>
            </div>
          </div>
          <button className="w-full btn-secondary" disabled>Em Breve</button>
        </div>

        <div className="card opacity-60">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-dark">Mean Reversion</h3>
            <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium">
              Em Breve
            </span>
          </div>
          <p className="text-sm text-secondary mb-4">
            Estratégia de reversão à média usando Bollinger Bands e RSI.
          </p>
          <div className="space-y-2 mb-4">
            <div className="flex items-center gap-2 text-sm">
              <span>📊</span>
              <span className="text-secondary">Bollinger Bands</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span>📈</span>
              <span className="text-secondary">RSI</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span>🎯</span>
              <span className="text-secondary">Z-Score</span>
            </div>
          </div>
          <button className="w-full btn-secondary" disabled>Em Breve</button>
        </div>
      </div>

      <div className="card mt-6">
        <h2 className="text-xl font-bold text-dark mb-4">Adicionar Nova Estratégia</h2>
        <button className="btn-primary flex items-center gap-2">
          <span>➕</span>
          Criar Estratégia Personalizada
        </button>
      </div>
    </div>
  );
}
