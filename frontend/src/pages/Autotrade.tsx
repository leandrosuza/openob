export default function Autotrade() {
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
              <span className="px-3 py-1 bg-gray-100 rounded-full text-sm font-medium text-secondary">
                Inativo
              </span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <span className="text-secondary">Estratégia</span>
              <span className="font-medium text-dark">Scalping 5s</span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <span className="text-secondary">Amount</span>
              <span className="font-medium text-dark">$5.00</span>
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
            <button className="w-full btn-primary flex items-center justify-center gap-2">
              <span>▶️</span>
              Iniciar Autotrade
            </button>
            <button className="w-full btn-secondary flex items-center justify-center gap-2">
              <span>⏸️</span>
              Pausar Autotrade
            </button>
            <button className="w-full btn-secondary flex items-center justify-center gap-2">
              <span>⏹️</span>
              Parar Autotrade
            </button>
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
