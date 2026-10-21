import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/auth';
import type { RegisterRequest } from '../types/auth';

export default function Register() {
  const [formData, setFormData] = useState<RegisterRequest>({
    username: '',
    email: '',
    password: '',
    ssid_demo: '',
    ssid_real: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authService.register(formData);
      navigate('/login');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao criar conta');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-light px-4 py-8">
      <div className="card w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-dark mb-2">OpenOB</h1>
          <p className="text-secondary text-sm">Crie sua conta</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg mb-6 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-dark mb-2">
              Usuário
            </label>
            <input
              id="username"
              type="text"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              className="input-field"
              placeholder="Seu usuário"
              required
              minLength={3}
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-dark mb-2">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="input-field"
              placeholder="seu@email.com"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-dark mb-2">
              Senha
            </label>
            <input
              id="password"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="input-field"
              placeholder="Sua senha"
              required
              minLength={6}
            />
          </div>

          <div>
            <label htmlFor="ssid_demo" className="block text-sm font-medium text-dark mb-2">
              SSID Demo (PocketOption)
            </label>
            <input
              id="ssid_demo"
              type="text"
              value={formData.ssid_demo}
              onChange={(e) => setFormData({ ...formData, ssid_demo: e.target.value })}
              className="input-field"
              placeholder="42[\"auth\",{\"session\":\"...\"}]"
              required
            />
          </div>

          <div>
            <label htmlFor="ssid_real" className="block text-sm font-medium text-dark mb-2">
              SSID Real (opcional)
            </label>
            <input
              id="ssid_real"
              type="text"
              value={formData.ssid_real || ''}
              onChange={(e) => setFormData({ ...formData, ssid_real: e.target.value })}
              className="input-field"
              placeholder="42[\"auth\",{\"session\":\"...\"}]"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Criando conta...' : 'Criar conta'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-secondary">
            Já tem uma conta?{' '}
            <a href="/login" className="text-primary hover:underline font-medium">
              Faça login
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
