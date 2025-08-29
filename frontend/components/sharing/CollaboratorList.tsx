
import React from 'react';
import { Collaborator, PermissionLevel } from '../../types';
import apiService from '../../services/apiService';
import { TrashIcon, UserIcon } from '../ui/icons';

interface CollaboratorListProps {
  collaborators: Collaborator[];
  taskId: number;
  onUpdate: () => void;
}

const CollaboratorList: React.FC<CollaboratorListProps> = ({ collaborators, taskId, onUpdate }) => {

  const handlePermissionChange = async (username: string, newPermission: PermissionLevel) => {
    try {
        await apiService(`/sharing/tasks/${taskId}/shares/${username}?new_permission=${newPermission}`, {
            method: 'PUT'
        });
        onUpdate();
    } catch(error) {
        console.error("Failed to update permission", error);
    }
  }

  const handleUnshare = async (username: string) => {
    if (window.confirm(`Are you sure you want to unshare this task with ${username}?`)) {
        try {
            await apiService(`/sharing/tasks/${taskId}/shares/${username}`, {
                method: 'DELETE'
            });
            onUpdate();
        } catch(error) {
            console.error("Failed to unshare task", error);
        }
    }
  }

  if (collaborators.length === 0) {
    return <p className="text-gray-500">Not shared with anyone.</p>;
  }
  
  return (
    <div className="space-y-3">
      {collaborators.map(c => (
        <div key={c.user_id} className="flex items-center justify-between bg-secondary p-3 rounded-lg">
          <div className="flex items-center gap-3">
            <UserIcon className="w-6 h-6 text-gray-400" />
            <div>
              <p className="font-semibold">{c.username}</p>
              <p className="text-xs text-gray-400">{c.role}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {c.role === 'collaborator' ? (
                <>
                 <select
                    value={c.permission_level}
                    onChange={(e) => handlePermissionChange(c.username, e.target.value as PermissionLevel)}
                    className="bg-primary border border-slate-600 rounded-md py-1 px-2 text-sm"
                  >
                    <option value="view">View</option>
                    <option value="edit">Edit</option>
                  </select>
                  <button onClick={() => handleUnshare(c.username)} className="p-2 text-red-500 hover:bg-primary rounded-full">
                    <TrashIcon className="w-5 h-5"/>
                  </button>
                </>
            ) : (
                <span className="text-sm text-accent font-semibold">Owner</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default CollaboratorList;
