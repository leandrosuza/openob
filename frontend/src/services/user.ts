import axios from 'axios';
import type { User } from '../types/auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const userService = {
  async updateSSID(userId: number, ssidDemo: string | null, ssidReal: string | null): Promise<void> {
    const token = localStorage.getItem('access_token');
    await axios.put(`${API_URL}/users/${userId}/ssid`, {
      ssid_demo: ssidDemo,
      ssid_real: ssidReal
    }, {
      headers: { Authorization: `Bearer ${token}` }
    });
  },

  async updateMode(userId: number, mode: 'demo' | 'real'): Promise<void> {
    const token = localStorage.getItem('access_token');
    await axios.put(`${API_URL}/users/${userId}/mode`, null, {
      params: { mode },
      headers: { Authorization: `Bearer ${token}` }
    });
  }
};
