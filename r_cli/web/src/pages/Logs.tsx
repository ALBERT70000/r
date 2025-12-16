import { useEffect, useState } from 'react';
import api from '../api/client';
import type { AuditEvent } from '../types';

const severityColors: Record<string, string> = {
  debug: 'text-slate-400',
  info: 'text-blue-400',
  warning: 'text-yellow-400',
  error: 'text-red-400',
  critical: 'text-red-500 font-bold',
};

const actionIcons: Record<string, string> = {
  'auth.login': '🔑',
  'auth.logout': '🚪',
  'auth.failed': '❌',
  'chat.request': '💬',
  'chat.response': '✅',
  'skill.called': '🛠️',
  'skill.completed': '✅',
  'skill.error': '❌',
  'rate_limit.exceeded': '⚠️',
  default: '📝',
};

function LogEntry({ event }: { event: AuditEvent }) {
  const icon = actionIcons[event.action] || actionIcons.default;
  const severityClass = severityColors[event.severity] || 'text-slate-400';

  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 hover:border-slate-600 transition-colors">
      <div className="flex items-start gap-3">
        <span className="text-xl">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-white">{event.action}</span>
            <span className={`text-xs ${severityClass}`}>
              [{event.severity}]
            </span>
            {event.success ? (
              <span className="text-xs text-green-400">✓ Success</span>
            ) : (
              <span className="text-xs text-red-400">✗ Failed</span>
            )}
          </div>

          <div className="text-sm text-slate-400 mt-1 space-y-1">
            {event.username && (
              <p>User: {event.username}</p>
            )}
            {event.resource && (
              <p>Resource: {event.resource}</p>
            )}
            {event.error_message && (
              <p className="text-red-400">Error: {event.error_message}</p>
            )}
            {event.duration_ms && (
              <p>Duration: {event.duration_ms.toFixed(2)}ms</p>
            )}
          </div>

          <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
            <span>{new Date(event.timestamp).toLocaleString()}</span>
            {event.client_ip && <span>IP: {event.client_ip}</span>}
            {event.auth_type && <span>Auth: {event.auth_type}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Logs() {
  const [logs, setLogs] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [limit, setLimit] = useState(50);
  const [actionFilter, setActionFilter] = useState<string>('');
  const [successFilter, setSuccessFilter] = useState<string>('');

  useEffect(() => {
    async function fetchLogs() {
      setLoading(true);
      try {
        const params: { limit: number; action?: string; success?: boolean } = { limit };
        if (actionFilter) params.action = actionFilter;
        if (successFilter !== '') params.success = successFilter === 'true';

        const data = await api.getAuditLogs(params);
        setLogs(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch logs');
      } finally {
        setLoading(false);
      }
    }

    fetchLogs();
  }, [limit, actionFilter, successFilter]);

  const actions = [...new Set(logs.map((l) => l.action))].sort();

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Audit Logs</h1>
        <span className="text-slate-400">{logs.length} entries</span>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
        >
          <option value="">All Actions</option>
          {actions.map((action) => (
            <option key={action} value={action}>
              {action}
            </option>
          ))}
        </select>

        <select
          value={successFilter}
          onChange={(e) => setSuccessFilter(e.target.value)}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
        >
          <option value="">All Results</option>
          <option value="true">Success</option>
          <option value="false">Failed</option>
        </select>

        <select
          value={limit}
          onChange={(e) => setLimit(Number(e.target.value))}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
        >
          <option value={25}>Last 25</option>
          <option value={50}>Last 50</option>
          <option value={100}>Last 100</option>
          <option value={200}>Last 200</option>
        </select>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-4 mb-6">
          <p className="text-red-400">{error}</p>
          <p className="text-slate-400 text-sm mt-1">
            Note: Audit logs require admin authentication.
          </p>
        </div>
      )}

      {/* Loading */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-slate-400">Loading logs...</div>
        </div>
      ) : (
        /* Logs List */
        <div className="space-y-3">
          {logs.map((event, index) => (
            <LogEntry key={`${event.timestamp}-${index}`} event={event} />
          ))}

          {logs.length === 0 && !error && (
            <div className="text-center py-12 text-slate-400">
              No audit logs found.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
