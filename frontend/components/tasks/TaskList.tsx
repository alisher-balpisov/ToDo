
import React from 'react';
import { Task, SharedTask } from '../../types';
import TaskItem from './TaskItem';

interface TaskListProps {
  tasks: (Task | SharedTask)[];
  onSelectTask: (task: Task | SharedTask) => void;
  selectedTaskId?: number | null;
  isLoading: boolean;
}

const TaskList: React.FC<TaskListProps> = ({ tasks, onSelectTask, selectedTaskId, isLoading }) => {
  if (isLoading) {
    return <div className="text-center text-gray-400">Loading tasks...</div>;
  }

  if (tasks.length === 0) {
    return <div className="text-center text-gray-500 mt-4">No tasks found.</div>;
  }

  return (
    <div className="space-y-2 overflow-y-auto">
      {tasks.map(task => (
        <TaskItem 
          key={task.id} 
          task={task} 
          onSelect={() => onSelectTask(task)}
          isSelected={task.id === selectedTaskId}
        />
      ))}
    </div>
  );
};

export default TaskList;
