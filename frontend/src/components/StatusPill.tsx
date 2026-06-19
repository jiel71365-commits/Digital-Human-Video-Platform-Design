import type { TaskState } from "../types";

const labels: Record<TaskState, string> = {
  draft: "草稿",
  queued: "等待",
  script_ready: "文案完成",
  audio_ready: "音频完成",
  rendered: "渲染完成",
  post_processed: "后期完成",
  completed: "完成",
  failed: "失败"
};

export function StatusPill({ state }: { state: TaskState }) {
  return <span className={`status status-${state}`}>{labels[state]}</span>;
}
