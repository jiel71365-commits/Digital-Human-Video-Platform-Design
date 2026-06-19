import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import {
  createTask,
  getTask,
  listDigitalHumans,
  listTasks,
  listTemplates,
  listVoices
} from "../src/api";
import type {
  DigitalHumanProfile,
  GenerationStepLog,
  MediaAsset,
  PostProcessTemplate,
  ScriptDraft,
  TaskDetail,
  VideoTask,
  VoiceProfile
} from "../src/types";

vi.mock("../src/api", () => ({
  createTask: vi.fn(),
  getTask: vi.fn(),
  listDigitalHumans: vi.fn(),
  listTasks: vi.fn(),
  listTemplates: vi.fn(),
  listVoices: vi.fn()
}));

vi.mock("lucide-react", () => {
  const icon =
    (name: string) =>
    ({ "aria-hidden": ariaHidden }: { "aria-hidden"?: boolean }) => (
      <svg aria-hidden={ariaHidden} data-testid={`icon-${name}`} />
    );

  return {
    Clapperboard: icon("Clapperboard"),
    ClipboardList: icon("ClipboardList"),
    MonitorPlay: icon("MonitorPlay"),
    PlusCircle: icon("PlusCircle"),
    UserRound: icon("UserRound"),
    Video: icon("Video"),
    Volume2: icon("Volume2")
  };
});

const humans: DigitalHumanProfile[] = [
  {
    id: 1,
    name: "Default Presenter",
    preview_image_path: "/static/default-presenter.png",
    source_media_path: "/static/default-presenter.mp4",
    default_aspect_ratio: "9:16",
    renderer_adapter_key: "mock-avatar",
    status: "active"
  }
];

const voices: VoiceProfile[] = [
  {
    id: 1,
    name: "Default Voice",
    provider_key: "mock-tts",
    voice_key: "default",
    style_tags: ["neutral", "mandarin"],
    preview_audio_path: null,
    is_default: true,
    status: "active"
  }
];

const templates: PostProcessTemplate[] = [
  {
    id: 1,
    name: "Default Vertical Video",
    subtitle_style: { font_size: 42, position: "bottom" },
    bgm_path: null,
    intro_media_path: null,
    outro_media_path: null,
    cover_strategy: "first_frame"
  }
];

const tasks: VideoTask[] = [
  {
    id: 21,
    input_mode: "existing_script",
    raw_input: "A sample task",
    digital_human_profile_id: 1,
    voice_profile_id: 1,
    post_process_template_id: 1,
    current_state: "completed",
    failed_step: null,
    final_video_path: "/storage/tasks/21/final/final.mp4",
    cover_path: "/storage/tasks/21/final/cover.jpg"
  }
];

const script: ScriptDraft = {
  id: 1,
  task_id: 21,
  version: 1,
  script_text: "生成的口播脚本",
  structured_segments: [],
  estimated_duration_seconds: 12,
  source_mode: "existing_script"
};

const assets: MediaAsset[] = [
  {
    id: 1,
    task_id: 21,
    asset_type: "final_video",
    file_path: "/storage/tasks/21/final/final.mp4",
    duration_seconds: 12,
    asset_metadata: {}
  }
];

const logs: GenerationStepLog[] = [
  {
    id: 1,
    task_id: 21,
    step_name: "post_process",
    status: "succeeded",
    started_at: "2026-06-19T00:00:00Z",
    finished_at: "2026-06-19T00:00:01Z",
    duration_seconds: 1,
    error_code: null,
    user_message: null,
    technical_log: null
  }
];

const detail: TaskDetail = {
  task: tasks[0],
  script,
  assets,
  logs
};

const mockedListDigitalHumans = vi.mocked(listDigitalHumans);
const mockedListVoices = vi.mocked(listVoices);
const mockedListTemplates = vi.mocked(listTemplates);
const mockedListTasks = vi.mocked(listTasks);
const mockedGetTask = vi.mocked(getTask);
const mockedCreateTask = vi.mocked(createTask);

function mockApiData(nextTasks = tasks) {
  mockedListDigitalHumans.mockResolvedValue(humans);
  mockedListVoices.mockResolvedValue(voices);
  mockedListTemplates.mockResolvedValue(templates);
  mockedListTasks.mockResolvedValue(nextTasks);
  mockedGetTask.mockResolvedValue(detail);
}

describe("App", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    mockApiData();
  });

  it("loads the management UI sections with default API data and task detail", async () => {
    render(<App />);

    expect(await screen.findByRole("heading", { name: "新建视频任务" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "成片记录" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /任务详情/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "数字人形象" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "声音" })).toBeInTheDocument();

    expect(screen.getAllByTestId("icon-MonitorPlay")).toHaveLength(2);
    expect(screen.getByTestId("icon-Clapperboard")).toBeInTheDocument();
    expect(screen.getByTestId("icon-UserRound")).toBeInTheDocument();
    expect(screen.getByTestId("icon-Volume2")).toBeInTheDocument();
    expect(screen.queryByTestId("icon-Video")).not.toBeInTheDocument();
    expect(screen.queryByTestId("icon-PlusCircle")).not.toBeInTheDocument();
    expect(screen.queryByTestId("icon-ClipboardList")).not.toBeInTheDocument();

    expect(screen.getAllByText("Default Presenter")).toHaveLength(2);
    expect(screen.getAllByText("Default Voice")).toHaveLength(2);
    expect(screen.getByText("Default Vertical Video")).toBeInTheDocument();
    expect(screen.getByText("A sample task")).toBeInTheDocument();
    expect(screen.getAllByText("完成")).toHaveLength(2);
    expect(await screen.findByText("生成的口播脚本")).toBeInTheDocument();
    expect(screen.getByText("/storage/tasks/21/final/final.mp4")).toBeInTheDocument();
    expect(screen.getByText("post_process")).toBeInTheDocument();
  });

  it("creates a task with the first available profile, voice, and template", async () => {
    const user = userEvent.setup();
    const createdTask: VideoTask = {
      ...tasks[0],
      id: 22,
      raw_input: "新任务文案"
    };
    mockedCreateTask.mockResolvedValue(createdTask);
    mockedListTasks.mockResolvedValueOnce(tasks).mockResolvedValueOnce([createdTask, ...tasks]);
    mockedGetTask.mockResolvedValue({
      ...detail,
      task: createdTask,
      script: { ...script, task_id: 22, script_text: "新任务生成脚本" },
      assets: [{ ...assets[0], task_id: 22, file_path: "/storage/tasks/22/final/final.mp4" }],
      logs: [{ ...logs[0], task_id: 22 }]
    });

    render(<App />);

    const input = await screen.findByLabelText("输入内容");
    await user.clear(input);
    await user.type(input, "新任务文案");
    await user.click(screen.getByRole("button", { name: "生成视频" }));

    await waitFor(() => {
      expect(mockedCreateTask).toHaveBeenCalledWith({
        input_mode: "existing_script",
        raw_input: "新任务文案",
        digital_human_profile_id: 1,
        voice_profile_id: 1,
        post_process_template_id: 1
      });
    });
    expect(await screen.findByText("新任务生成脚本")).toBeInTheDocument();
  });

  it("shows generation progress while creating a task", async () => {
    const user = userEvent.setup();
    let resolveCreate: (task: VideoTask) => void = () => {};
    mockedCreateTask.mockReturnValue(
      new Promise<VideoTask>((resolve) => {
        resolveCreate = resolve;
      })
    );

    render(<App />);

    await screen.findByLabelText("输入内容");
    await user.click(screen.getByRole("button", { name: "生成视频" }));

    expect(screen.getByRole("button", { name: "生成中" })).toBeDisabled();

    resolveCreate(tasks[0]);
  });
});
