
import React from 'react';
import { View } from '../types';

// FIX: Moved SVG Icon declarations to the top to avoid block-scoped variable errors.
// They were being used in `iconMap` before they were declared.
const IconLayoutDashboard = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>;
const IconListDetails = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3h7a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-7m0-18H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h7m0-18v18"></path><path d="M16 8h-4"></path><path d="M16 12h-4"></path><path d="M16 16h-4"></path></svg>;
const IconTerminal2 = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M8 9l3 3-3 3"></path><path d="M13 15h3"></path><path d="M3 3v18h18"></path></svg>;
const IconBook = () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>;
const IconShieldCheck = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="m9 12 2 2 4-4"></path></svg>;

interface SidebarProps {
  currentView: View;
  setCurrentView: (view: View) => void;
}

const iconMap: Record<View, React.ReactNode> = {
  [View.Dashboard]: <IconLayoutDashboard />,
  [View.ActionLedger]: <IconListDetails />,
  [View.CommandCenter]: <IconTerminal2 />,
  [View.Runbook]: <IconBook />,
};

const NavItem: React.FC<{
  view: View;
  currentView: View;
  onClick: () => void;
}> = ({ view, currentView, onClick }) => {
  const isActive = view === currentView;
  return (
    <button
      onClick={onClick}
      className={`flex items-center space-x-3 w-full px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
        isActive ? 'bg-pcp-blue/10 text-pcp-blue' : 'text-pcp-text-dim hover:bg-pcp-border/50'
      }`}
    >
      {iconMap[view]}
      <span className="truncate">{view}</span>
    </button>
  );
};

export const Sidebar: React.FC<SidebarProps> = ({ currentView, setCurrentView }) => {
  return (
    <nav className="flex flex-col bg-pcp-light-dark border-r border-pcp-border w-64 p-4 space-y-2">
      <div className="flex items-center space-x-2 px-2 pb-4">
        <IconShieldCheck className="w-8 h-8 text-pcp-blue" />
        <h2 className="text-lg font-bold text-pcp-text">PCP Dashboard</h2>
      </div>
      {(Object.values(View) as View[]).map((view) => (
        <NavItem key={view} view={view} currentView={currentView} onClick={() => setCurrentView(view)} />
      ))}
    </nav>
  );
};
