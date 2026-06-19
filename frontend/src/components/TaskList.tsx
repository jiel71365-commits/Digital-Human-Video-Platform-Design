import type { VideoTask } from "../types";
import { StatusPill } from "./StatusPill";

interface TaskListProps {
  tasks: VideoTask[];
  selectedTaskId: number | null;
  onSelect: (taskId: number) => void;
}

export function TaskList({ tasks, selectedTaskId, onSelect }: TaskListProps) {
  return (
    <section className="panel" id="tasks">
      <div className="panel-header">
        <div>
          <h2>成片记录</h2>
          <p>{tasks.length} 条任务</p>
        </div>
      </div>

      {tasks.length === 0 ? (
        <p className="empty-state">暂无成片记录</p>
      ) : (
        <div className="task-list">
          {tasks.map((task) => (
            <button
              aria-pressed={task.id === selectedTaskId}
              className={task.id === selectedTaskId ? "task-row active" : "task-row"}
              key={task.id}
              type="button"
              onClick={() => onSelect(task.id)}
            >
              <span className="task-title">{task.raw_input}</span>
              <StatusPill state={task.current_state} />
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
