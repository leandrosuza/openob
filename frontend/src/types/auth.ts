export interface User {
  id: number;
  username: string;
  email: string;
  plan_id: number | null;
  current_subscription_id: number | null;
  plan_expires_at: string | null;
  is_active: boolean;
  balance: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  ssid_demo: string;
  ssid_real?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
}

export interface ErrorResponse {
  detail: string;
}
