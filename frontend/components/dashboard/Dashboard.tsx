
import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import TaskList from '../tasks/TaskList';
import TaskDetail from '../tasks/TaskDetail';
import apiService from '../../services/apiService';
import { Task, SharedTask, TaskStats } from '../../types';
import { PlusIcon } from '../ui/icons';
import Modal from '../ui/Modal';
import CreateTaskForm from '../tasks/CreateTaskForm';

type ViewType = 'my_tasks' | 'shared_tasks' | 'stats';

const Dashboard: React.FC = () => {
  const [view, setView] = useState<ViewType>('my_tasks');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [sharedTasks, setSharedTasks] = useState<SharedTask[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | SharedTask | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);
  const [stats, setStats] = useState<TaskStats | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      if (view === 'my_tasks') {
        const response = await apiService<{tasks: Task[]}>('/tasks/');
        setTasks(response.tasks);
        if(response.tasks.length > 0 && !selectedTask) {
            setSelectedTask(response.tasks[0])
        }
      } else if (view === 'shared_tasks') {
        const response = await apiService<SharedTask[]>('/sharing/shared-tasks');
        setSharedTasks(response);
         if(response.length > 0 && !selectedTask) {
            setSelectedTask(response[0])
        }
      } else if (view === 'stats') {
        const response = await apiService<TaskStats>('/stats');
        setStats(response);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [view, selectedTask]);

  useEffect(() => {
    fetchData();
  }, [view, fetchData]);
  
  const handleTaskSelect = (task: Task | SharedTask) => {
    setSelectedTask(task);
  }
  
  const handleTaskUpdated = () => {
     setSelectedTask(null);
     fetchData();
  }

  const handleTaskCreated = (newTask: Task) => {
    setCreateModalOpen(false);
    fetchData();
    setSelectedTask(newTask);
  }

  return (
    <div className="flex h-screen bg-dark text-light">
      <Sidebar currentView={view} setView={setView} />
      <div className="flex flex-col flex-1">
        <Header />
        <main className="flex flex-1 overflow-hidden p-4 gap-4">
          <div className="w-1/3 flex flex-col bg-primary rounded-lg p-4">
             <div className="flex justify-between items-center mb-4">
               <h2 className="text-xl font-bold">{view === 'my_tasks' ? 'My Tasks' : 'Shared With Me'}</h2>
               {view === 'my_tasks' && (
                <button onClick={() => setCreateModalOpen(true)} className="p-2 rounded-full bg-secondary hover:bg-accent">
                    <PlusIcon className="w-5 h-5" />
                </button>
               )}
             </div>
             {view !== 'stats' && (
              <TaskList 
                tasks={view === 'my_tasks' ? tasks : sharedTasks} 
                onSelectTask={handleTaskSelect}
                selectedTaskId={selectedTask?.id}
                isLoading={isLoading}
              />
             )}
              {view === 'stats' && stats && (
                <div className="space-y-4 p-4 bg-secondary rounded-lg">
                    <h2 className="text-2xl font-bold border-b border-gray-600 pb-2">Task Statistics</h2>
                    <div className="grid grid-cols-2 gap-4 text-center">
                        <div className="bg-primary p-4 rounded-lg">
                            <p className="text-3xl font-bold">{stats.total_tasks}</p>
                            <p className="text-gray-400">Total Tasks</p>
                        </div>
                        <div className="bg-primary p-4 rounded-lg">
                            <p className="text-3xl font-bold text-green-400">{stats.completed_tasks}</p>
                            <p className="text-gray-400">Completed</p>
                        </div>
                        <div className="bg-primary p-4 rounded-lg">
                            <p className="text-3xl font-bold text-yellow-400">{stats.uncompleted_tasks}</p>
                            <p className="text-gray-400">Incomplete</p>
                        </div>
                         <div className="bg-primary p-4 rounded-lg">
                            <p className="text-3xl font-bold text-accent">{stats.completion_percentage.toFixed(1)}%</p>
                            <p className="text-gray-400">Completion</p>
                        </div>
                    </div>
                </div>
            )}
          </div>
          <div className="w-2/3 bg-primary rounded-lg p-4 overflow-y-auto">
            {selectedTask ? (
                <TaskDetail key={selectedTask.id} task={selectedTask} onTaskUpdate={handleTaskUpdated}/>
            ) : (
                <div className="flex items-center justify-center h-full text-gray-500">Select a task to see details</div>
            )}
          </div>
        </main>
      </div>
      <Modal isOpen={isCreateModalOpen} onClose={() => setCreateModalOpen(false)} title="Create New Task">
        <CreateTaskForm onTaskCreated={handleTaskCreated} />
      </Modal>
    </div>
  );
};

export default Dashboard;
