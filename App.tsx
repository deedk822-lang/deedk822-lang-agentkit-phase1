
import React, { useState, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { DashboardView } from './components/DashboardView';
import { ActionLedgerView } from './components/ActionLedgerView';
// FIX: Changed to a default import to match the export in CommandCenterView.tsx
import CommandCenterView from './components/CommandCenterView';
import { RunbookView } from './components/RunbookView';
import { AssistantWidget } from './components/AssistantWidget';
import { View } from './types';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>(View.Dashboard);

  const renderView = useCallback(() => {
    switch (currentView) {
      case View.Dashboard:
        return <DashboardView />;
      case View.ActionLedger:
        return <ActionLedgerView />;
      case View.CommandCenter:
        return <CommandCenterView />;
      case View.Runbook:
        return <RunbookView />;
      default:
        return <DashboardView />;
    }
  }, [currentView]);

  return (
    <div className="flex h-screen bg-pcp-dark font-sans">
      <Sidebar currentView={currentView} setCurrentView={setCurrentView} />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header currentView={currentView} />
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          {renderView()}
        </main>
      </div>
      <AssistantWidget />
    </div>
  );
};

export default App;