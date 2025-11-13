import { create } from 'zustand';
import type { Message, TraceInfo, Module } from '../types';

interface AppState {
  sessionId: string | null;
  messages: Message[];
  traces: TraceInfo[];
  modules: Module[];
  activeModule: string | null;
  isLoading: boolean;
  showTraces: boolean;
  llmMode: 'cloud' | 'local' | null;
  geojson: any | null;
  anomalies: any | null;
  anomalyMode: 'live' | 'dataset';
  shap: any[] | null;
  activeTab: 'chat' | 'anomaly';
  pipelineSteps: Map<string, any[]>;
  
  setSessionId: (id: string) => void;
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  addTraces: (traces: TraceInfo[]) => void;
  clearTraces: () => void;
  setModules: (modules: Module[]) => void;
  setActiveModule: (module: string | null) => void;
  setIsLoading: (loading: boolean) => void;
  toggleTraces: () => void;
  reset: () => void;
  setLlmMode: (mode: 'cloud' | 'local') => void;
  setGeoData: (geojson: any | null, anomalies: any | null) => void;
  setAnomalyMode: (mode: 'live' | 'dataset') => void;
  setShap: (values: any[] | null) => void;
  setActiveTab: (tab: 'chat' | 'anomaly') => void;
  updatePipelineStep: (messageId: string, step: any) => void;
  clearPipelineSteps: (messageId: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sessionId: null,
  messages: [],
  traces: [],
  modules: [],
  activeModule: null,
  isLoading: false,
  showTraces: false,
  llmMode: null,
  geojson: null,
  anomalies: null,
  anomalyMode: 'live',
  shap: null,
  activeTab: 'chat',
  pipelineSteps: new Map(),
  
  setSessionId: (id) => set({ sessionId: id }),
  
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  
  setMessages: (messages) => set({ messages }),
  
  addTraces: (traces) =>
    set((state) => ({ traces: [...state.traces, ...traces] })),
  
  clearTraces: () => set({ traces: [] }),
  
  setModules: (modules) => set({ modules }),
  
  setActiveModule: (module) => set({ activeModule: module }),
  
  setIsLoading: (loading) => set({ isLoading: loading }),
  
  toggleTraces: () => set((state) => ({ showTraces: !state.showTraces })),
  
  reset: () =>
    set({
      sessionId: null,
      messages: [],
      traces: [],
      activeModule: null,
      isLoading: false,
    }),
  setLlmMode: (mode) => set({ llmMode: mode }),
  setGeoData: (geojson, anomalies) => set({ geojson, anomalies }),
  setAnomalyMode: (mode) => set({ anomalyMode: mode }),
  setShap: (values) => set({ shap: values }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  
  updatePipelineStep: (messageId, step) =>
    set((state) => {
      const newMap = new Map(state.pipelineSteps);
      const existing = newMap.get(messageId) || [];
      const idx = existing.findIndex((s) => s.step === step.step);
      if (idx >= 0) {
        existing[idx] = { ...existing[idx], ...step };
      } else {
        existing.push(step);
      }
      newMap.set(messageId, existing);
      return { pipelineSteps: newMap };
    }),
  
  clearPipelineSteps: (messageId) =>
    set((state) => {
      const newMap = new Map(state.pipelineSteps);
      newMap.delete(messageId);
      return { pipelineSteps: newMap };
    }),
}));

