
export interface Task {
  id: number;
  task_name: string;
  completion_status: boolean;
  date_time: string;
  text: string | null;
  file_name: string | null;
}

export interface SharedTask extends Task {
  owner_username: string;
  permission_level: PermissionLevel;
}

export type PermissionLevel = 'view' | 'edit';

export interface Collaborator {
  user_id: number;
  username: string;
  role: 'owner' | 'collaborator';
  permission_level: PermissionLevel | 'full_access';
  shared_date?: string;
  can_revoke: boolean;
}

export interface TaskStats {
  total_tasks: number;
  completed_tasks: number;
  uncompleted_tasks: number;
  completion_percentage: number;
}


