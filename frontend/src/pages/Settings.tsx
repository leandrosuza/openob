import { useState } from 'react';
import { authService } from '../services/auth';

export default function Settings() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage('');
    setLoading(true);

    if (newPassword !== confirmPassword) {
      setMessage('As senhas não coincidem');
      setLoading(false);
      return;
    }

    try {
      await authService.changePassword(currentPassword, newPassword);
      setMessage('Senha alterada com sucesso');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Erro ao alterar senha');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-dark mb-2">Configurações</h1>
        <p className="text-secondary">Gerencie sua conta e preferências</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-bold text-dark mb-4">Alterar Senha</h2>
          <form onSubmit={handlePasswordChange} className="space-y-4">
            <div>
              <label htmlFor="currentPassword" className="block text-sm font-medium text-dark mb-2">
                Senha Atual
              </label>
              <input
                id="currentPassword"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="input-field"
                placeholder="Digite sua senha atual"
                required
              />
            </div>
            <div>
              <label htmlFor="newPassword" className="block text-sm font-medium text-dark mb-2">
                Nova Senha
              </label>
              <input
                id="newPassword"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="input-field"
                placeholder="Mínimo 6 caracteres"
                required
                minLength={6}
              />
            </div>
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-dark mb-2">
                Confirmar Nova Senha
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input-field"
                placeholder="Digite a nova senha novamente"
                required
                minLength={6}
              />
            </div>
            {message && (
              <div className={`px-4 py-3 rounded-lg text-sm ${
                message.includes('sucesso')
                  ? 'bg-green-50 text-green-600 border border-green-200'
                  : 'bg-red-50 text-red-600 border border-red-200'
              }`}>
                {message}
              </div>
            )}
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Alterando...' : 'Alterar Senha'}
            </button>
          </form>
        </div>

        <div className="card">
          <h2 className="text-xl font-bold text-dark mb-4">Informações da Conta</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <span className="text-secondary">Username</span>
              <span className="font-medium text-dark">teste123</span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <span className="text-secondary">Email</span>
              <span className="font-medium text-dark">teste@example.com</span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <span className="text-secondary">Plano</span>
              <span className="font-medium text-dark">Free</span>
            </div>
            <div className="flex items-center justify-between py-3">
              <span className="text-secondary">Status</span>
              <span className={`badge ${'bg-green-100 text-green-700'}`}>
                Ativo
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="card mt-6">
        <h2 className="text-xl font-bold text-dark mb-4">Configurações de Conexão</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dark mb-2">
              SSID Demo
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="SSID da conta demo"
              disabled
            />
            <p className="text-xs text-secondary mt-1">Configure na aba de conexão</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-dark mb-2">
              SSID Real
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="SSID da conta real"
              disabled
            />
            <p className="text-xs text-secondary mt-1">Configure na aba de conexão</p>
          </div>
        </div>
      </div>
    </div>
  );
}
