import React, { useState } from 'react';
import apiService from '../../services/apiService';
import { PermissionLevel } from '../../types';

interface ShareModalProps {
  taskId: number;
  onShared: () => void;
}

const ShareModal: React.FC<ShareModalProps> = ({ taskId, onShared }) => {
  const [targetUsername, setTargetUsername] = useState('');
  const [permissionLevel, setPermissionLevel] = useState<PermissionLevel>('view');
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    if (!targetUsername.trim()) {
      setError("Username is required.");
      return;
    }
    
    try {
      // FIX: Explicitly type the response for the apiService call.
      const response = await apiService<{ msg: string }>(`/sharing/tasks/${taskId}/shares`, {
        method: 'POST',
        body: JSON.stringify({ target_username: targetUsername, permission_level: permissionLevel }),
      });
      setMessage(response.msg || "Task shared successfully!");
      setTargetUsername('');
      onShared();
    } catch (err: any) {
      setError(err.message || 'Failed to share task.');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="username" className="block text-sm font-medium text-gray-300">Username</label>
        <input
          id="username"
          type="text"
          value={targetUsername}
          onChange={e => setTargetUsername(e.target.value)}
          className="mt-1 block w-full bg-secondary border border-slate-600 rounded-md shadow-sm py-2 px-3 text-light focus:outline-none focus:ring-accent focus:border-accent"
          placeholder="Enter username to share with"
          required
        />
      </div>
      <div>
        <label htmlFor="permission" className="block text-sm font-medium text-gray-300">Permission</label>
        <select
          id="permission"
          value={permissionLevel}
          onChange={e => setPermissionLevel(e.target.value as PermissionLevel)}
          className="mt-1 block w-full bg-secondary border border-slate-600 rounded-md shadow-sm py-2 px-3 text-light focus:outline-none focus:ring-accent focus:border-accent"
        >
          <option value="view">View</option>
          <option value="edit">Edit</option>
        </select>
      </div>
      {error && <p className="text-sm text-red-500">{error}</p>}
      {message && <p className="text-sm text-green-500">{message}</p>}
      <div className="flex justify-end">
        <button type="submit" className="px-4 py-2 bg-accent hover:bg-sky-500 text-white font-semibold rounded-md">
          Share
        </button>
      </div>
    </form>
  );
};

export default ShareModal;