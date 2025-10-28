
import React, { useState, useEffect } from 'react';
import { PcpComponentStatus, Metric } from '../types';
import { fetchPcpStatus, fetchMetrics } from '../services/mockPcpApi';

const MetricCard: React.FC<{ metric: Metric }> = ({ metric }) => {
  const changeColor = metric.changeType === 'increase' ? 'text-pcp-green' : 'text-pcp-red';
  return (
    <div className="bg-pcp-light-dark border border-pcp-border rounded-lg p-4">
      <p className="text-pcp-text-dim text-sm">{metric.label}</p>
      <div className="flex items-baseline space-x-2 mt-1">
        <p className="text-2xl font-semibold text-pcp-text">{metric.value}</p>
        {metric.change && <p className={`text-sm font-medium ${changeColor}`}>{metric.change}</p>}
      </div>
    </div>
  );
};

const StatusListItem: React.FC<{ component: PcpComponentStatus }> = ({ component }) => {
    const statusClasses = {
        healthy: { bg: 'bg-pcp-green/10', text: 'text-pcp-green', dot: 'bg-pcp-green' },
        degraded: { bg: 'bg-pcp-yellow/10', text: 'text-pcp-yellow', dot: 'bg-pcp-yellow' },
        unhealthy: { bg: 'bg-pcp-red/10', text: 'text-pcp-red', dot: 'bg-pcp-red' },
    };
    const currentStatus = statusClasses[component.status];
    return (
        <div className="flex items-center justify-between p-3 hover:bg-pcp-border/30 rounded-md">
            <div className="flex items-center space-x-3">
                <div className={`w-2.5 h-2.5 rounded-full ${currentStatus.dot}`}></div>
                <span className="font-medium text-pcp-text">{component.name}</span>
            </div>
            <div className="flex items-center space-x-4">
                <span className="text-sm text-pcp-text-dim">{component.details}</span>
                <span className={`text-xs font-semibold px-2 py-1 rounded-full ${currentStatus.bg} ${currentStatus.text}`}>
                    {component.status.toUpperCase()}
                </span>
            </div>
        </div>
    );
};

export const DashboardView: React.FC = () => {
    const [statuses, setStatuses] = useState<PcpComponentStatus[]>([]);
    const [metrics, setMetrics] = useState<Metric[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            const [statusData, metricsData] = await Promise.all([
                fetchPcpStatus(),
                fetchMetrics(),
            ]);
            setStatuses(statusData);
            setMetrics(metricsData);
            setLoading(false);
        };
        loadData();
    }, []);

    if (loading) {
        return <div className="text-center text-pcp-text-dim">Loading Dashboard...</div>;
    }

    return (
        <div className="space-y-8">
            <div>
                <h2 className="text-2xl font-bold mb-4 text-pcp-text">System Metrics</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {metrics.map(metric => <MetricCard key={metric.label} metric={metric} />)}
                </div>
            </div>
            <div>
                <h2 className="text-2xl font-bold mb-4 text-pcp-text">Component Status</h2>
                <div className="bg-pcp-light-dark border border-pcp-border rounded-lg">
                    <div className="divide-y divide-pcp-border">
                        {statuses.map(status => <StatusListItem key={status.name} component={status} />)}
                    </div>
                </div>
            </div>
        </div>
    );
};
