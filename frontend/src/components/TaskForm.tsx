import { useState } from "react";
import type { FormEvent } from "react";

import type {
  DigitalHumanProfile,
  PostProcessTemplate,
  TaskCreatePayload,
  TaskInputMode,
  VideoTask,
  VoiceProfile
} from "../types";

interface TaskFormProps {
  humans: DigitalHumanProfile[];
  voices: VoiceProfile[];
  templates: PostProcessTemplate[];
  onCreate: (payload: TaskCreatePayload) => Promise<VideoTask>;
}

const inputModeLabels: Record<TaskInputMode, string> = {
  existing_script: "已有文案",
  topic: "主题/商品资料",
  reference_video: "对标视频资料"
};

export function TaskForm({ humans, voices, templates, onCreate }: TaskFormProps) {
  const [inputMode, setInputMode] = useState<TaskInputMode>("existing_script");
  const [rawInput, setRawInput] = useState("这是一条用于验证 MVP 流水线的口播文案。");
  const [submitting, setSubmitting] = useState(false);

  const hasRequiredDefaults = humans.length > 0 && voices.length > 0 && templates.length > 0;
  const canSubmit = hasRequiredDefaults && rawInput.trim().length > 0 && !submitting;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }

    setSubmitting(true);
    try {
      await onCreate({
        input_mode: inputMode,
        raw_input: rawInput.trim(),
        digital_human_profile_id: humans[0].id,
        voice_profile_id: voices[0].id,
        post_process_template_id: templates[0].id
      });
    } catch {
      // App displays the API error banner.
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="panel task-form" id="create-task" onSubmit={submit}>
      <div className="panel-header">
        <div>
          <h2>新建视频任务</h2>
          <p>使用当前默认配置创建一条串行生成任务</p>
        </div>
      </div>

      <label htmlFor="input-mode">输入类型</label>
      <select
        id="input-mode"
        value={inputMode}
        onChange={(event) => setInputMode(event.target.value as TaskInputMode)}
      >
        {Object.entries(inputModeLabels).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>

      <label htmlFor="raw-input">输入内容</label>
      <textarea
        id="raw-input"
        value={rawInput}
        onChange={(event) => setRawInput(event.target.value)}
        rows={6}
      />

      <div className="config-summary" aria-label="默认生成配置">
        <div>
          <strong>形象</strong>
          <span>{humans[0]?.name ?? "暂无可用形象"}</span>
        </div>
        <div>
          <strong>声音</strong>
          <span>{voices[0]?.name ?? "暂无可用声音"}</span>
        </div>
        <div>
          <strong>后期模板</strong>
          <span>{templates[0]?.name ?? "暂无可用模板"}</span>
        </div>
      </div>

      <button type="submit" disabled={!canSubmit}>
        {submitting ? "生成中" : "生成视频"}
      </button>
    </form>
  );
}
