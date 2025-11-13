import axios from 'axios';
import type { QueryResponse, Module } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  async createSession(): Promise<{ session_id: string; created_at: string }> {
    const response = await apiClient.post('/sessions');
    return response.data;
  },

  async sendQuery(query: string, sessionId?: string): Promise<QueryResponse> {
    const response = await apiClient.post('/chat', {
      query,
      session_id: sessionId,
    });
    return response.data;
  },

  async getSessionHistory(sessionId: string): Promise<{
    session_id: string;
    messages: Array<{
      role: string;
      content: string;
      timestamp: string;
      metadata?: Record<string, unknown>;
    }>;
  }> {
    const response = await apiClient.get(`/sessions/${sessionId}`);
    return response.data;
  },

  async getModules(): Promise<{ modules: Module[] }> {
    const response = await apiClient.get('/modules');
    return response.data;
  },

  async healthCheck(): Promise<{
    status: string;
    version: string;
    llm_mode: string;
  }> {
    const response = await apiClient.get('/health');
    return response.data;
  },

  async uploadAnomalyDataset(params: {
    file: File;
    sessionId?: string;
    latCol?: string;
    lonCol?: string;
    valueCol?: string;
    topK?: number;
  }): Promise<{ geojson: string; anomalies: string; map: string }> {
    const form = new FormData();
    form.append('file', params.file);
    if (params.latCol) form.append('lat_col', params.latCol);
    if (params.lonCol) form.append('lon_col', params.lonCol);
    if (params.valueCol) form.append('value_col', params.valueCol);
    if (params.topK !== undefined) form.append('top_k', String(params.topK));
    if (params.sessionId) form.append('session_id', params.sessionId);
    const response = await axios.post(`${API_BASE_URL}/anomaly/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

