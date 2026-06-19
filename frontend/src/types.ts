export type ProfileStatus = "active" | "disabled";

export type TaskInputMode = "topic" | "existing_script" | "reference_video";

export type TaskState =
  | "draft"
  | "queued"
  | "script_ready"
  | "audio_ready"
  | "rendered"
  | "post_processed"
  | "completed"
  | "failed";

export type StepStatus = "running" | "succeeded" | "failed";

export interface ApiValidationIssue {
  loc?: Array<string | number>;
  msg: string;
  type?: string;
}

export interface ApiErrorDetail {
  message?: string;
  fields?: string[];
  task_id?: number;
  current_state?: TaskState;
  failed_step?: string | null;
  error?: string;
}

export interface ApiErrorBody {
  detail?: string | ApiErrorDetail | ApiValidationIssue[];
  [key: string]: unknown;
}

export interface TaskCreatePayload {
  input_mode: TaskInputMode;
  raw_input: string;
  digital_human_profile_id: number;
  voice_profile_id: number;
  post_process_template_id: number;
}

export interface DigitalHumanProfile {
  id: number;
  name: string;
  preview_image_path: string | null;
  source_media_path: string | null;
  default_aspect_ratio: string;
  renderer_adapter_key: string;
  status: ProfileStatus;
}

export interface VoiceProfile {
  id: number;
  name: string;
  provider_key: string;
  voice_key: string;
  style_tags: string[];
  preview_audio_path: string | null;
  is_default: boolean;
  status: ProfileStatus;
}

export interface PostProcessTemplate {
  id: number;
  name: string;
  subtitle_style: Record<string, unknown>;
  bgm_path: string | null;
  intro_media_path: string | null;
  outro_media_path: string | null;
  cover_strategy: string;
}

export interface VideoTask {
  id: number;
  input_mode: TaskInputMode;
  raw_input: string;
  digital_human_profile_id: number;
  voice_profile_id: number;
  post_process_template_id: number;
  current_state: TaskState;
  failed_step: string | null;
  final_video_path: string | null;
  cover_path: string | null;
}

export interface ScriptDraft {
  id: number;
  task_id: number;
  version: number;
  script_text: string;
  structured_segments: Array<Record<string, unknown>>;
  estimated_duration_seconds: number;
  source_mode: string;
}

export interface MediaAsset {
  id: number;
  task_id: number;
  asset_type: string;
  file_path: string;
  duration_seconds: number | null;
  asset_metadata: Record<string, unknown>;
}

export interface GenerationStepLog {
  id: number;
  task_id: number;
  step_name: string;
  status: StepStatus;
  started_at: string;
  finished_at: string | null;
  duration_seconds: number | null;
  error_code: string | null;
  user_message: string | null;
  technical_log: string | null;
}

export interface TaskDetail {
  task: VideoTask;
  script: ScriptDraft | null;
  assets: MediaAsset[];
  logs: GenerationStepLog[];
}
