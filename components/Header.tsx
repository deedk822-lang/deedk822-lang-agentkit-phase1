
import React from 'react';
import { View } from '../types';

interface HeaderProps {
  currentView: View;
}

const StatusIndicator: React.FC<{ status: 'healthy' | 'degraded' | 'unhealthy' }> = ({ status }) => {
  const colorClass = {
    healthy: 'bg-pcp-green',
    degraded: 'bg-pcp-yellow',
    unhealthy: 'bg-pcp-red',
  }[status];

  return <div className={`w-3 h-3 rounded-full ${colorClass}`}></div>;
};

export const Header: React.FC<HeaderProps> = ({ currentView }) => {
  return (
    <header className="flex-shrink-0 bg-pcp-light-dark border-b border-pcp-border p-4 flex items-center justify-between">
      <h1 className="text-xl font-semibold text-pcp-text">{currentView}</h1>
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 text-sm text-pcp-text-dim">
          <StatusIndicator status="degraded" />
          <span>System Status: Degraded</span>
        </div>
        <div className="w-px h-6 bg-pcp-border"></div>
        <span className="text-sm text-pcp-text-dim font-mono">user: ops_user</span>
      </div>
    </header>
  );
};
