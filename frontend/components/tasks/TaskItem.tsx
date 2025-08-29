
import React from 'react';
import { Task, SharedTask } from '../../types';

interface TaskItemProps {
  task: Task | SharedTask;
  onSelect: () => void;
  isSelected: boolean;
}

const TaskItem: React.FC<TaskItemProps> = ({ task, onSelect, isSelected }) => {
  const isShared = 'owner_username' in task;

  return (
    <div
      onClick={onSelect}
      className={`p-3 rounded-lg cursor-pointer transition-all ${
        isSelected ? 'bg-accent text-white shadow-lg' : 'bg-secondary hover:bg-slate-600'
      } ${task.completion_status ? 'opacity-60' : ''}`}
    >
      <div className="flex justify-between items-center">
        <h3 className={`font-semibold truncate ${task.completion_status ? 'line-through' : ''}`}>
            {task.task_name}
        </h3>
        {isShared && (
            <span className="text-xs bg-primary px-2 py-1 rounded-full">
                { (task as SharedTask).owner_username }
            </span>
        )}
      </div>
      <p className="text-xs text-gray-400 mt-1">
        {new Date(task.date_time).toLocaleDateString()}
      </p>
    </div>
  );
};

export default TaskItem;
