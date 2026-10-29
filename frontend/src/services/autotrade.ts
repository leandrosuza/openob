import axios from 'axios';
import type { AutotradeConfig } from '../types/auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const autotradeService = {
  async getConfig(userId: number): Promise<AutotradeConfig> {
    const token = localStorage.getItem('access_token');
    const response = await axios.get(`${API_URL}/api/autotrade/configs/${userId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  async createConfig(config: AutotradeConfig): Promise<AutotradeConfig> {
    const token = localStorage.getItem('access_token');
    const response = await axios.post(`${API_URL}/api/autotrade/configs`, config, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  async updateConfig(userId: number, config: AutotradeConfig): Promise<AutotradeConfig> {
    const token = localStorage.getItem('access_token');
    const response = await axios.put(`${API_URL}/api/autotrade/configs/${userId}`, config, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  async toggleConfig(userId: number): Promise<AutotradeConfig> {
    const token = localStorage.getItem('access_token');
    const response = await axios.patch(`${API_URL}/api/autotrade/configs/${userId}/toggle`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  async deleteConfig(userId: number): Promise<{ message: string; user_id: number }> {
    const token = localStorage.getItem('access_token');
    const response = await axios.delete(`${API_URL}/api/autotrade/configs/${userId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  async getStrategies(): Promise<string[]> {
    const response = await axios.get(`${API_URL}/api/autotrade/strategies`);
    return response.data;
  }
};
