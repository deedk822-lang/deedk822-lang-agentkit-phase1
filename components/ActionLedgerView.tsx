
import React, { useState, useEffect, useMemo } from 'react';
import { LedgerEntry, LedgerStatus } from '../types';
import { fetchLedgerEntries } from '../services/mockPcpApi';
import { generateText } from '../services/geminiService';

const statusColors: Record<LedgerStatus, string> = {
  [LedgerStatus.SUCCESS]: 'bg-pcp-green/10 text-pcp-green',
  [LedgerStatus.FAILED]: 'bg-pcp-red/10 text-pcp-red',
  [LedgerStatus.BLOCKED]: 'bg-pcp-yellow/10 text-pcp-yellow',
  [LedgerStatus.PENDING]: 'bg-pcp-blue/10 text-pcp-blue',
};

const LedgerRow: React.FC<{ entry: LedgerEntry; onAnalyze: (entry: LedgerEntry) => void }> = ({ entry, onAnalyze }) => {
  return (
    <tr className="border-b border-pcp-border hover:bg-pcp-light-dark/50">
      <td className="p-3 font-mono text-sm">{entry.id.slice(0, 12)}...</td>
      <td className="p-3 font-mono text-sm">{entry.command}</td>
      <td className="p-3">
        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${statusColors[entry.status]}`}>
          {entry.status}
        </span>
      </td>
      <td className="p-3 text-sm text-pcp-text-dim truncate max-w-xs">{entry.rationale}</td>
      <td className="p-3 text-sm text-pcp-text-dim">{new Date(entry.timestamp).toLocaleString()}</td>
      <td className="p-3 text-right">
        <button onClick={() => onAnalyze(entry)} className="text-pcp-blue hover:underline text-sm font-medium">Analyze</button>
      </td>
    </tr>
  );
};

const AnalysisModal: React.FC<{ entry: LedgerEntry | null; summary: string; loading: boolean; onClose: () => void }> = ({ entry, summary, loading, onClose }) => {
  if (!entry) return null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-pcp-light-dark border border-pcp-border rounded-lg shadow-xl w-full max-w-2xl p-6" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-pcp-text">Analysis for Action: <span className="font-mono">{entry.id}</span></h3>
        <div className="mt-4 space-y-2 text-sm text-pcp-text-dim">
          <p><strong>Command:</strong> <span className="font-mono">{entry.command}</span></p>
          <p><strong>Status:</strong> {entry.status}</p>
          <p><strong>Timestamp:</strong> {new Date(entry.timestamp).toLocaleString()}</p>
          <p><strong>Rationale:</strong> {entry.rationale}</p>
        </div>
        <div className="mt-4 pt-4 border-t border-pcp-border">
            <h4 className="font-semibold text-pcp-text mb-2">Gemini AI Summary</h4>
            {loading ? <div className="animate-pulse h-20 bg-pcp-border/50 rounded-md"></div> : <p className="text-pcp-text whitespace-pre-wrap">{summary}</p>}
        </div>
        <button onClick={onClose} className="mt-6 bg-pcp-blue text-white px-4 py-2 rounded-md font-semibold hover:bg-pcp-blue/80">Close</button>
      </div>
    </div>
  );
};

export const ActionLedgerView: React.FC = () => {
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [selectedEntry, setSelectedEntry] = useState<LedgerEntry | null>(null);
  const [summary, setSummary] = useState('');
  const [summaryLoading, setSummaryLoading] = useState(false);

  useEffect(() => {
    fetchLedgerEntries().then(data => {
      setEntries(data);
      setLoading(false);
    });
  }, []);
  
  const handleAnalyze = async (entry: LedgerEntry) => {
    setSelectedEntry(entry);
    setSummaryLoading(true);
    setSummary('');
    const prompt = `Provide a concise, one-paragraph summary for the following system action log entry. Explain what happened and why in simple terms.\n\nLog Entry:\n${JSON.stringify(entry, null, 2)}`;
    const result = await generateText(prompt);
    setSummary(result);
    setSummaryLoading(false);
  };

  const filteredEntries = useMemo(() =>
    entries.filter(entry =>
      entry.command.toLowerCase().includes(filter.toLowerCase()) ||
      entry.id.toLowerCase().includes(filter.toLowerCase()) ||
      entry.rationale.toLowerCase().includes(filter.toLowerCase())
    ), [entries, filter]);

  if (loading) return <div className="text-center text-pcp-text-dim">Loading Action Ledger...</div>;

  return (
    <div>
      <div className="mb-4">
        <input
          type="text"
          value={filter}
          onChange={e => setFilter(e.target.value)}
          placeholder="Filter by command, ID, or rationale..."
          className="w-full bg-pcp-light-dark border border-pcp-border rounded-md px-3 py-2 placeholder-pcp-text-dim focus:outline-none focus:ring-2 focus:ring-pcp-blue"
        />
      </div>
      <div className="bg-pcp-light-dark border border-pcp-border rounded-lg overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-pcp-border/30">
            <tr>
              <th className="p-3 text-sm font-semibold">Action ID</th>
              <th className="p-3 text-sm font-semibold">Command</th>
              <th className="p-3 text-sm font-semibold">Status</th>
              <th className="p-3 text-sm font-semibold">Rationale</th>
              <th className="p-3 text-sm font-semibold">Timestamp</th>
              <th className="p-3 text-sm font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredEntries.map(entry => <LedgerRow key={entry.id} entry={entry} onAnalyze={handleAnalyze} />)}
          </tbody>
        </table>
      </div>
      <AnalysisModal entry={selectedEntry} summary={summary} loading={summaryLoading} onClose={() => setSelectedEntry(null)} />
    </div>
  );
};
