import React, { useState, useCallback, useEffect } from 'react';
import { Task, SharedTask, Collaborator, PermissionLevel } from '../../types';
import apiService from '../../services/apiService';
import { TrashIcon, ShareIcon, FileIcon } from '../ui/icons';
import Modal from '../ui/Modal';
import ShareModal from '../sharing/ShareModal';
import CollaboratorList from '../sharing/CollaboratorList';

interface TaskDetailProps {
  task: Task | SharedTask;
  onTaskUpdate: () => void;
}

const TaskDetail: React.FC<TaskDetailProps> = ({ task: initialTask, onTaskUpdate }) => {
  const [task, setTask] = useState(initialTask);
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState(task.task_name);
  const [editedText, setEditedText] = useState(task.text || '');
  const [isShareModalOpen, setShareModalOpen] = useState(false);
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  
  const isShared = 'owner_username' in task;
  const isOwner = !isShared;
  const canEdit = isOwner || (isShared && (task as SharedTask).permission_level === 'edit');

  const fetchCollaborators = useCallback(async () => {
    if (isOwner) {
      try {
        const response = await apiService<{ collaborators: Collaborator[] }>(`/sharing/tasks/${task.id}/collaborators`);
        setCollaborators(response.collaborators);
      } catch (error) {
        console.error("Failed to fetch collaborators", error);
        setCollaborators([]);
      }
    }
  }, [task.id, isOwner]);

  useEffect(() => {
    setTask(initialTask);
    setEditedName(initialTask.task_name);
    setEditedText(initialTask.text || '');
    fetchCollaborators();
  }, [initialTask, fetchCollaborators]);

  const handleUpdate = async () => {
    const endpoint = isShared ? `/sharing/shared-tasks/${task.id}` : `/tasks/${task.id}`;
    try {
      await apiService(endpoint, {
        method: 'PUT',
        body: JSON.stringify({ name: editedName, text: editedText }),
      });
      onTaskUpdate();
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update task', error);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        await apiService(`/tasks/${task.id}`, { method: 'DELETE' });
        onTaskUpdate();
      } catch (error) {
        console.error('Failed to delete task', error);
      }
    }
  };

  const handleToggleStatus = async () => {
     const endpoint = isShared ? `/sharing/shared-tasks/${task.id}` : `/tasks/${task.id}`;
     try {
       await apiService(endpoint, { method: 'PATCH' });
       onTaskUpdate();
     } catch (error) {
       console.error('Failed to toggle status', error);
     }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('uploaded_file', file);
    
    const endpoint = isShared ? `/sharing/shared-tasks/${task.id}/file` : `/tasks/${task.id}/file`;

    try {
        await apiService(endpoint, {
            method: 'POST',
            body: formData,
        });
        onTaskUpdate();
    } catch (error) {
        console.error("Failed to upload file", error);
    }
  };
  
  const handleFileDownload = async () => {
    const endpoint = isShared ? `/sharing/shared-tasks/${task.id}/file` : `/tasks/${task.id}/file`;
    try {
        const blob = await apiService<Blob>(endpoint, {
            responseType: 'blob',
        });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = task.file_name || 'download';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error("Failed to download file", error);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        {isEditing ? (
          <input 
            type="text" 
            value={editedName} 
            onChange={e => setEditedName(e.target.value)}
            className="text-2xl font-bold bg-secondary p-2 rounded-md w-full"
          />
        ) : (
          <h1 className="text-3xl font-bold">{task.task_name}</h1>
        )}
        <div className="flex items-center space-x-2">
            {canEdit && (
              <button onClick={handleToggleStatus} className={`px-3 py-1 text-sm rounded-full ${task.completion_status ? 'bg-green-500' : 'bg-yellow-500'}`}>
                {task.completion_status ? 'Completed' : 'Incomplete'}
              </button>
            )}
            {isOwner && (
                <>
                <button onClick={() => setShareModalOpen(true)} className="p-2 rounded-full hover:bg-secondary"><ShareIcon/></button>
                <button onClick={handleDelete} className="p-2 rounded-full hover:bg-secondary text-red-500"><TrashIcon/></button>
                </>
            )}
        </div>
      </div>
      
      <div>
        <h2 className="font-semibold text-gray-400">Description</h2>
        {isEditing ? (
          <textarea 
            value={editedText}
            onChange={e => setEditedText(e.target.value)}
            className="w-full h-32 bg-secondary p-2 mt-2 rounded-md"
          />
        ) : (
            <p className="mt-2 text-gray-300 whitespace-pre-wrap">{task.text || 'No description.'}</p>
        )}
      </div>

       {canEdit && (
            isEditing ? (
            <div className="flex space-x-2">
                <button onClick={handleUpdate} className="px-4 py-2 bg-accent rounded-md">Save</button>
                <button onClick={() => setIsEditing(false)} className="px-4 py-2 bg-secondary rounded-md">Cancel</button>
            </div>
            ) : (
            <button onClick={() => setIsEditing(true)} className="px-4 py-2 bg-secondary rounded-md">Edit</button>
            )
       )}
       
       <div className="border-t border-secondary pt-4 space-y-2">
          <h2 className="font-semibold text-gray-400">File Attachment</h2>
          {task.file_name ? (
            <div className="flex items-center justify-between bg-secondary p-3 rounded-lg">
                <div className="flex items-center gap-2">
                    <FileIcon className="w-5 h-5"/>
                    <span>{task.file_name}</span>
                </div>
                <button onClick={handleFileDownload} className="text-accent text-sm hover:underline">Download</button>
            </div>
          ) : <p className="text-gray-500">No file attached.</p>}
          {canEdit && (
            <div>
                <label htmlFor="file-upload" className="cursor-pointer mt-2 inline-block px-4 py-2 bg-secondary hover:bg-accent rounded-md text-sm">
                    Upload File
                </label>
                <input id="file-upload" type="file" className="hidden" onChange={handleFileUpload} />
            </div>
          )}
       </div>


      {isOwner && (
         <div className="border-t border-secondary pt-4 space-y-2">
             <h2 className="font-semibold text-gray-400">Collaborators</h2>
             <CollaboratorList collaborators={collaborators} taskId={task.id} onUpdate={fetchCollaborators} />
         </div>
      )}

      <Modal isOpen={isShareModalOpen} onClose={() => setShareModalOpen(false)} title="Share Task">
        <ShareModal taskId={task.id} onShared={() => { setShareModalOpen(false); fetchCollaborators(); }} />
      </Modal>
    </div>
  );
};

export default TaskDetail;
