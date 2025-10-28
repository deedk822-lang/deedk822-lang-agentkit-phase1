
import { LedgerEntry, LedgerStatus, PcpComponentStatus, Metric } from '../types';

const generateRandomId = () => `id_${Math.random().toString(36).substr(2, 9)}`;
const generateRandomProof = () => Math.random().toString(36).substr(2, 16);

const mockLedgerData: LedgerEntry[] = [
  { id: generateRandomId(), command: 'SCAN_SITE domain=example.com', status: LedgerStatus.SUCCESS, rationale: 'Scan completed, no vulnerabilities found.', timestamp: new Date(Date.now() - 3600000).toISOString(), latencyMs: 350, signedBy: 'command_poller', proof: generateRandomProof() },
  { id: generateRandomId(), command: 'START_CAMPAIGN channel=linkedin campaign_id=q4-push', status: LedgerStatus.SUCCESS, rationale: 'Judges voted 3/3 to approve. Campaign launched.', timestamp: new Date(Date.now() - 2 * 3600000).toISOString(), latencyMs: 12500, signedBy: 'command_poller', proof: generateRandomProof() },
  { id: generateRandomId(), command: 'PUBLISH_REPORT client=acme dataset=q3_perf', status: LedgerStatus.BLOCKED, rationale: 'Validation failed: client "acme" not found in active clients list.', timestamp: new Date(Date.now() - 3 * 3600000).toISOString(), latencyMs: 120, signedBy: 'command_poller', proof: 'error' },
  { id: generateRandomId(), command: 'SCAN_SITE domain=rogue-site.io', status: LedgerStatus.FAILED, rationale: 'Execution error: DNS lookup failed for domain.', timestamp: new Date(Date.now() - 4 * 3600000).toISOString(), latencyMs: 5000, signedBy: 'command_poller', proof: generateRandomProof() },
  { id: generateRandomId(), command: 'REVERT_ACTION action_id=id_xyz123 reason=Emergency', status: LedgerStatus.SUCCESS, rationale: 'Action successfully rolled back.', timestamp: new Date(Date.now() - 5 * 3600000).toISOString(), latencyMs: 850, signedBy: 'ops_user', proof: generateRandomProof() },
  { id: generateRandomId(), command: 'SCAN_SITE domain=test-site.com', status: LedgerStatus.SUCCESS, rationale: 'Scan completed, no vulnerabilities found.', timestamp: new Date(Date.now() - 6 * 3600000).toISOString(), latencyMs: 410, signedBy: 'command_poller', proof: generateRandomProof() },
];

const mockComponentStatus: PcpComponentStatus[] = [
    { name: 'MCP Orchestrator', status: 'healthy', details: '2/2 replicas running' },
    { name: 'Command Poller', status: 'healthy', details: 'Last poll 15s ago' },
    { name: 'Redis Cache', status: 'healthy', details: 'Memory usage at 65%' },
    { name: 'Notion API', status: 'degraded', details: 'P95 latency > 800ms' },
    { name: 'Ledger Verifier', status: 'healthy', details: 'Last verification passed' },
];

const mockMetrics: Metric[] = [
    { label: 'Action Success Rate', value: '96.8%', change: '+0.2%', changeType: 'increase' },
    { label: 'P95 Response Time', value: '482ms', change: '-15ms', changeType: 'decrease' },
    { label: 'Actions / Hour', value: '128' },
    { label: 'Circuit Breakers', value: '0 Tripped' },
];

export const fetchLedgerEntries = async (): Promise<LedgerEntry[]> => {
    return new Promise(resolve => setTimeout(() => resolve([...mockLedgerData]), 500));
};

export const fetchPcpStatus = async (): Promise<PcpComponentStatus[]> => {
    return new Promise(resolve => setTimeout(() => resolve(mockComponentStatus), 300));
};

export const fetchMetrics = async (): Promise<Metric[]> => {
    return new Promise(resolve => setTimeout(() => resolve(mockMetrics), 400));
};

export const submitCommand = async (command: { command_type: string, params: Record<string, string>, severity: string }): Promise<LedgerEntry> => {
    const newEntry: LedgerEntry = {
        id: generateRandomId(),
        command: `${command.command_type} ${Object.entries(command.params).map(([k, v]) => `${k}=${v}`).join(' ')}`,
        status: LedgerStatus.SUCCESS,
        rationale: 'Action submitted via dashboard and completed successfully.',
        timestamp: new Date().toISOString(),
        latencyMs: Math.floor(Math.random() * 500) + 100,
        signedBy: 'dashboard_user',
        proof: generateRandomProof()
    };
    mockLedgerData.unshift(newEntry);
    return new Promise(resolve => setTimeout(() => resolve(newEntry), 1000));
};
