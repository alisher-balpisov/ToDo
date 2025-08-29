
import React, { useState } from 'react';
import apiService from '../../services/apiService';
import { Task } from '../../types';

interface CreateTaskFormProps {
  onTaskCreated: (task: Task) => void;
}

const CreateTaskForm: React.FC<CreateTaskFormProps> = ({ onTaskCreated }) => {
  const [name, setName] = useState('');
  const [text, setText] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Task name is required.');
      return;
    }
    setError(null);

    try {
      const response = await apiService<{task_id: number, task_name: string}>('/tasks/', {
        method: 'POST',
        body: JSON.stringify({ name, text }),
      });
      
      // Fetch the full task object to pass back
      const newTask = await apiService<Task>(`/tasks/${response.task_id}`);
      onTaskCreated(newTask);
    } catch (err: any) {
      setError(err.message || 'Failed to create task.');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="task-name" className="block text-sm font-medium text-gray-300">Task Name</label>
        <input
          id="task-name"
          type="text"
          value={name}
          onChange={e => setName(e.target.value)}
          className="mt-1 block w-full bg-secondary border border-slate-600 rounded-md shadow-sm py-2 px-3 text-light focus:outline-none focus:ring-accent focus:border-accent"
          required
        />
      </div>
      <div>
        <label htmlFor="task-text" className="block text-sm font-medium text-gray-300">Description (Optional)</label>
        <textarea
          id="task-text"
          value={text}
          onChange={e => setText(e.target.value)}
          rows={4}
          className="mt-1 block w-full bg-secondary border border-slate-600 rounded-md shadow-sm py-2 px-3 text-light focus:outline-none focus:ring-accent focus:border-accent"
        />
      </div>
      {error && <p className="text-sm text-red-500">{error}</p>}
      <div className="flex justify-end">
        <button type="submit" className="px-4 py-2 bg-accent hover:bg-sky-500 text-white font-semibold rounded-md">
          Create Task
        </button>
      </div>
    </form>
  );
};

export default CreateTaskForm;
