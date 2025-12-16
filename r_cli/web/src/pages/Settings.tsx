import { useEffect, useState } from 'react';
import api from '../api/client';
import type { AuthUser, APIKeyInfo } from '../types';

function LoginForm({ onLogin }: { onLogin: () => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await api.login(username, password);
      onLogin();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 max-w-md">
      <h2 className="text-lg font-bold text-white mb-4">Login</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-slate-400 mb-1">Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            required
          />
        </div>
        <div>
          <label className="block text-sm text-slate-400 mb-1">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            required
          />
        </div>
        {error && (
          <p className="text-red-400 text-sm">{error}</p>
        )}
        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded-lg transition-colors"
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
}

function APIKeyManager() {
  const [keys, setKeys] = useState<APIKeyInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyScopes, setNewKeyScopes] = useState<string[]>(['read']);
  const [createdKey, setCreatedKey] = useState<string | null>(null);

  useEffect(() => {
    fetchKeys();
  }, []);

  async function fetchKeys() {
    try {
      const data = await api.getAPIKeys();
      setKeys(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch API keys');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      const response = await api.createAPIKey(newKeyName, newKeyScopes);
      setCreatedKey(response.key);
      setShowCreate(false);
      setNewKeyName('');
      fetchKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create API key');
    }
  }

  async function handleDelete(keyId: string) {
    if (!confirm('Are you sure you want to delete this API key?')) return;

    try {
      await api.deleteAPIKey(keyId);
      fetchKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete API key');
    }
  }

  const availableScopes = ['read', 'write', 'execute', 'admin', 'chat'];

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-white">API Keys</h2>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
        >
          + New Key
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-900/20 border border-red-500 rounded text-red-400 text-sm">
          {error}
        </div>
      )}

      {createdKey && (
        <div className="mb-4 p-4 bg-green-900/20 border border-green-500 rounded">
          <p className="text-green-400 font-bold mb-2">API Key Created!</p>
          <p className="text-slate-300 text-sm mb-2">
            Copy this key now. You won't be able to see it again.
          </p>
          <code className="block p-2 bg-slate-900 rounded text-sm text-white break-all">
            {createdKey}
          </code>
          <button
            onClick={() => {
              navigator.clipboard.writeText(createdKey);
              setCreatedKey(null);
            }}
            className="mt-2 text-sm text-blue-400 hover:text-blue-300"
          >
            Copy & Close
          </button>
        </div>
      )}

      {showCreate && (
        <form onSubmit={handleCreate} className="mb-4 p-4 bg-slate-700/50 rounded-lg">
          <div className="mb-3">
            <label className="block text-sm text-slate-400 mb-1">Name</label>
            <input
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="My API Key"
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
              required
            />
          </div>
          <div className="mb-3">
            <label className="block text-sm text-slate-400 mb-1">Scopes</label>
            <div className="flex flex-wrap gap-2">
              {availableScopes.map((scope) => (
                <label key={scope} className="flex items-center gap-1 text-sm text-slate-300">
                  <input
                    type="checkbox"
                    checked={newKeyScopes.includes(scope)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setNewKeyScopes([...newKeyScopes, scope]);
                      } else {
                        setNewKeyScopes(newKeyScopes.filter((s) => s !== scope));
                      }
                    }}
                  />
                  {scope}
                </label>
              ))}
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm"
            >
              Create
            </button>
            <button
              type="button"
              onClick={() => setShowCreate(false)}
              className="px-3 py-1 bg-slate-600 hover:bg-slate-500 text-white rounded text-sm"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <p className="text-slate-400">Loading...</p>
      ) : keys.length === 0 ? (
        <p className="text-slate-400">No API keys created yet.</p>
      ) : (
        <div className="space-y-2">
          {keys.map((key) => (
            <div
              key={key.key_id}
              className="flex items-center justify-between p-3 bg-slate-700/50 rounded"
            >
              <div>
                <p className="text-white font-medium">{key.name}</p>
                <p className="text-xs text-slate-400">
                  {key.scopes.join(', ')} • Created: {new Date(key.created_at).toLocaleDateString()}
                  {key.last_used && ` • Last used: ${new Date(key.last_used).toLocaleDateString()}`}
                </p>
              </div>
              <button
                onClick={() => handleDelete(key.key_id)}
                className="text-red-400 hover:text-red-300 text-sm"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Settings() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    try {
      const userData = await api.getMe();
      setUser(userData);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    api.logout();
    setUser(null);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Loading...</div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Settings</h1>

      {/* Auth Section */}
      <div className="mb-6">
        <h2 className="text-lg font-bold text-white mb-4">Authentication</h2>

        {user ? (
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">{user.username}</p>
                <p className="text-sm text-slate-400">
                  Scopes: {user.scopes.join(', ')}
                </p>
                <p className="text-sm text-slate-400">
                  Auth type: {user.auth_type}
                </p>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        ) : (
          <LoginForm onLogin={checkAuth} />
        )}
      </div>

      {/* API Keys Section */}
      {user && (
        <div className="mb-6">
          <APIKeyManager />
        </div>
      )}

      {/* Server Info */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h2 className="text-lg font-bold text-white mb-4">Server Configuration</h2>
        <div className="space-y-2 text-sm">
          <p className="text-slate-400">
            API URL: <span className="text-white">{import.meta.env.VITE_API_URL || 'http://localhost:8000'}</span>
          </p>
          <p className="text-slate-400">
            To change the API URL, set the <code className="bg-slate-700 px-1 rounded">VITE_API_URL</code> environment variable.
          </p>
        </div>
      </div>
    </div>
  );
}
