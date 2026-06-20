import type {
  ApiErrorBody,
  ApiErrorDetail,
  ApiValidationIssue,
  DigitalHumanProfile,
  PostProcessTemplate,
  TaskCreatePayload,
  TaskDetail,
  VideoTask,
  Wav2LipRuntimeStatus,
  VoiceProfile
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;
  readonly detail: string | ApiErrorDetail | ApiValidationIssue[] | undefined;

  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
    this.detail = getErrorDetail(body);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...init.headers
    }
  });

  const body = await readResponseBody(response);
  if (!response.ok) {
    throw new ApiError(response.status, getErrorMessage(response.status, body), body);
  }
  return body as T;
}

async function readResponseBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text) as ApiErrorBody | unknown;
  } catch {
    return { detail: text };
  }
}

function getErrorMessage(status: number, body: unknown): string {
  const detail = getErrorDetail(body);
  if (typeof detail === "string") {
    return detail;
  }
  if (isApiErrorDetail(detail)) {
    return detail.message ?? detail.error ?? `API request failed with status ${status}`;
  }
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((issue) => issue.msg).join("; ");
  }
  return `API request failed with status ${status}`;
}

function getErrorDetail(
  body: unknown
): string | ApiErrorDetail | ApiValidationIssue[] | undefined {
  if (!isApiErrorBody(body)) {
    return undefined;
  }
  return body.detail;
}

function isApiErrorBody(value: unknown): value is ApiErrorBody {
  return typeof value === "object" && value !== null;
}

function isApiErrorDetail(value: unknown): value is ApiErrorDetail {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function listDigitalHumans(): Promise<DigitalHumanProfile[]> {
  return request<DigitalHumanProfile[]>("/api/digital-humans");
}

export function listVoices(): Promise<VoiceProfile[]> {
  return request<VoiceProfile[]>("/api/voices");
}

export function listTemplates(): Promise<PostProcessTemplate[]> {
  return request<PostProcessTemplate[]>("/api/post-process-templates");
}

export function listTasks(): Promise<VideoTask[]> {
  return request<VideoTask[]>("/api/tasks");
}

export function getTask(taskId: number): Promise<TaskDetail> {
  return request<TaskDetail>(`/api/tasks/${taskId}`);
}

export function getWav2LipRuntimeStatus(): Promise<Wav2LipRuntimeStatus> {
  return request<Wav2LipRuntimeStatus>("/api/runtime/wav2lip");
}

export function createTask(payload: TaskCreatePayload): Promise<VideoTask> {
  return request<VideoTask>("/api/tasks", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
