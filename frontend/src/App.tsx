import { useEffect, useRef, useState } from "react";

import {
  createTask,
  getWav2LipRuntimeStatus,
  getTask,
  listDigitalHumans,
  listTasks,
  listTemplates,
  listVoices,
  uploadDigitalHumanSourceMedia
} from "./api";
import { Layout } from "./components/Layout";
import { ProfileList } from "./components/ProfileList";
import { RuntimeStatus } from "./components/RuntimeStatus";
import { TaskDetail } from "./components/TaskDetail";
import { TaskForm } from "./components/TaskForm";
import { TaskList } from "./components/TaskList";
import { VoiceList } from "./components/VoiceList";
import type {
  DigitalHumanProfile,
  PostProcessTemplate,
  TaskCreatePayload,
  TaskDetail as TaskDetailType,
  VideoTask,
  Wav2LipRuntimeStatus,
  VoiceProfile
} from "./types";

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : "未知错误";
}

export function App() {
  const [humans, setHumans] = useState<DigitalHumanProfile[]>([]);
  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [templates, setTemplates] = useState<PostProcessTemplate[]>([]);
  const [tasks, setTasks] = useState<VideoTask[]>([]);
  const [runtimeStatus, setRuntimeStatus] = useState<Wav2LipRuntimeStatus | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);
  const [detail, setDetail] = useState<TaskDetailType | null>(null);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const detailRequestIdRef = useRef(0);

  async function loadTaskDetail(taskId: number) {
    const requestId = detailRequestIdRef.current + 1;
    detailRequestIdRef.current = requestId;

    try {
      setDetail(null);
      const nextDetail = await getTask(taskId);
      if (requestId !== detailRequestIdRef.current) {
        return;
      }
      setDetail(nextDetail);
      setError(null);
    } catch (err) {
      if (requestId !== detailRequestIdRef.current) {
        return;
      }
      setDetail(null);
      setError(`任务详情加载失败：${getErrorMessage(err)}`);
    }
  }

  async function loadData(preferredTaskId?: number) {
    try {
      const [nextHumans, nextVoices, nextTemplates, nextTasks, nextRuntimeStatus] =
        await Promise.all([
          listDigitalHumans(),
          listVoices(),
          listTemplates(),
          listTasks(),
          getWav2LipRuntimeStatus()
        ]);
      const taskIds = new Set(nextTasks.map((task) => task.id));
      const requestedTaskId =
        preferredTaskId !== undefined && taskIds.has(preferredTaskId)
          ? preferredTaskId
          : selectedTaskId !== null && taskIds.has(selectedTaskId)
            ? selectedTaskId
            : (nextTasks[0]?.id ?? null);

      setHumans(nextHumans);
      setVoices(nextVoices);
      setTemplates(nextTemplates);
      setTasks(nextTasks);
      setRuntimeStatus(nextRuntimeStatus);
      setSelectedTaskId(requestedTaskId);
      setError(null);

      if (requestedTaskId !== null) {
        await loadTaskDetail(requestedTaskId);
      } else {
        detailRequestIdRef.current += 1;
        setDetail(null);
      }
    } catch (err) {
      setError(`数据加载失败：${getErrorMessage(err)}`);
    } finally {
      setHasLoaded(true);
    }
  }

  async function handleCreate(payload: TaskCreatePayload) {
    try {
      setError(null);
      const created = await createTask(payload);
      await loadData(created.id);
      return created;
    } catch (err) {
      setError(`任务创建失败：${getErrorMessage(err)}`);
      throw err;
    }
  }

  async function handleUploadHumanSourceMedia(profileId: number, file: File) {
    try {
      setError(null);
      await uploadDigitalHumanSourceMedia(profileId, file);
      await loadData(selectedTaskId ?? undefined);
    } catch (err) {
      setError(`素材上传失败：${getErrorMessage(err)}`);
      throw err;
    }
  }

  function handleSelectTask(taskId: number) {
    setSelectedTaskId(taskId);
    void loadTaskDetail(taskId);
  }

  useEffect(() => {
    void loadData();
  }, []);

  return (
    <Layout>
      <header className="workspace-header">
        <div>
          <p className="section-kicker">MVP 工作台</p>
          <h1>数字人口播视频管理台</h1>
        </div>
        <p>使用默认数字人、声音和后期模板创建任务，查看成片记录、产物和生成日志。</p>
      </header>

      <RuntimeStatus status={runtimeStatus} />

      {error ? (
        <div className="error-banner" role="alert">
          {error}
        </div>
      ) : null}

      {!hasLoaded ? (
        <section className="loading-panel" aria-live="polite">
          正在加载工作台...
        </section>
      ) : (
        <div className="dashboard-grid">
          <TaskForm
            humans={humans}
            voices={voices}
            templates={templates}
            onCreate={handleCreate}
          />
          <TaskList tasks={tasks} selectedTaskId={selectedTaskId} onSelect={handleSelectTask} />
          <TaskDetail detail={detail} />
          <ProfileList humans={humans} onUploadSourceMedia={handleUploadHumanSourceMedia} />
          <VoiceList voices={voices} />
        </div>
      )}
    </Layout>
  );
}
