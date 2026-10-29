export interface User {
  id: number;
  username: string;
  email: string;
  plan_id: number | null;
  current_subscription_id: number | null;
  plan_expires_at: string | null;
  is_active: boolean;
  balance: number;
  ssid_demo: string | null;
  ssid_real: string | null;
  mode: 'demo' | 'real';
  is_connected: boolean;
  connection_status: string | null;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user_id?: number;
}

export interface ErrorResponse {
  detail: string;
}

export interface AutotradeConfig {
  id?: number;
  user_id: number;
  strategy_name: string;
  parameters: Record<string, any>;
  amount: number;
  is_active: boolean;
  soros_enabled: boolean;
  soros_target_amount: number;
  created_at?: string;
  updated_at?: string;
}
