import { useEffect, useState } from 'react';
import api from '../api/client';
import type { StatusResponse } from '../types';

function StatusCard({ title, value, status, icon }: {
  title: string;
  value: string | number;
  status?: 'success' | 'warning' | 'error';
  icon: string;
}) {
  const statusColors = {
    success: 'text-green-400',
    warning: 'text-yellow-400',
    error: 'text-red-400',
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-slate-400 text-sm">{title}</p>
          <p className={`text-2xl font-bold mt-1 ${status ? statusColors[status] : 'text-white'}`}>
            {value}
          </p>
        </div>
        <span className="text-3xl">{icon}</span>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const data = await api.getStatus();
        setStatus(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch status');
      } finally {
        setLoading(false);
      }
    }

    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  function formatUptime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500 rounded-lg p-6">
        <h2 className="text-red-400 font-bold mb-2">Connection Error</h2>
        <p className="text-slate-300">{error}</p>
        <p className="text-slate-400 text-sm mt-2">
          Make sure the R CLI API server is running on port 8000.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Dashboard</h1>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatusCard
          title="Server Status"
          value={status?.status === 'healthy' ? 'Healthy' : status?.status || 'Unknown'}
          status={status?.status === 'healthy' ? 'success' : status?.status === 'degraded' ? 'warning' : 'error'}
          icon="🖥️"
        />
        <StatusCard
          title="LLM Connection"
          value={status?.llm.connected ? 'Connected' : 'Disconnected'}
          status={status?.llm.connected ? 'success' : 'error'}
          icon="🧠"
        />
        <StatusCard
          title="Skills Loaded"
          value={status?.skills_loaded || 0}
          icon="🛠️"
        />
        <StatusCard
          title="Uptime"
          value={status ? formatUptime(status.uptime_seconds) : '-'}
          icon="⏱️"
        />
      </div>

      {/* LLM Details */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 mb-6">
        <h2 className="text-lg font-bold text-white mb-4">LLM Configuration</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-slate-400 text-sm">Backend</p>
            <p className="text-white font-medium">{status?.llm.backend || '-'}</p>
          </div>
          <div>
            <p className="text-slate-400 text-sm">Model</p>
            <p className="text-white font-medium">{status?.llm.model || '-'}</p>
          </div>
          <div>
            <p className="text-slate-400 text-sm">Base URL</p>
            <p className="text-white font-medium text-sm truncate">{status?.llm.base_url || '-'}</p>
          </div>
          <div>
            <p className="text-slate-400 text-sm">Version</p>
            <p className="text-white font-medium">{status?.version || '-'}</p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h2 className="text-lg font-bold text-white mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <a
            href="/chat"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            💬 Start Chat
          </a>
          <a
            href="/skills"
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            🛠️ View Skills
          </a>
          <a
            href="/logs"
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            📋 View Logs
          </a>
        </div>
      </div>
    </div>
  );
}
