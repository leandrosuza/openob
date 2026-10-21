import api from './api';
import type { LoginRequest, RegisterRequest, AuthResponse, User } from '../types/auth';

export const authService = {
  async login(data: LoginRequest): Promise<AuthResponse> {
    const formData = new FormData();
    formData.append('username', data.username);
    formData.append('password', data.password);

    const response = await api.post<AuthResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    // Salvar tokens
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);

    return response.data;
  },

  async register(data: RegisterRequest): Promise<User> {
    const response = await api.post<User>('/auth/register', data);
    return response.data;
  },

  async logout(): Promise<void> {
    await api.post('/auth/logout');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });

    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);

    return response.data;
  },
};
