
export enum View {
  Dashboard = 'Dashboard',
  ActionLedger = 'Action Ledger',
  CommandCenter = 'Command Center',
  Runbook = 'Runbook',
}

export enum LedgerStatus {
  SUCCESS = 'SUCCESS',
  FAILED = 'FAILED',
  BLOCKED = 'BLOCKED',
  PENDING = 'PENDING',
}

export interface LedgerEntry {
  id: string;
  command: string;
  status: LedgerStatus;
  rationale: string;
  timestamp: string;
  latencyMs: number;
  signedBy: string;
  proof: string;
}

export interface PcpComponentStatus {
  name: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  details: string;
}

export interface Metric {
  label: string;
  value: string;
  change?: string;
  changeType?: 'increase' | 'decrease';
}

export interface ChatMessage {
  role: 'user' | 'model';
  text: string;
}
