import type { TaskDetail as TaskDetailType } from "../types";
import { StatusPill } from "./StatusPill";

export function TaskDetail({ detail }: { detail: TaskDetailType | null }) {
  if (!detail) {
    return (
      <section className="panel detail-panel">
        <h2>任务详情</h2>
        <p className="empty-state">选择一条成片记录查看文案、产物和日志。</p>
      </section>
    );
  }

  const finalVideo = detail.assets.find((asset) => asset.asset_type === "final_video");
  const cover = detail.assets.find((asset) => asset.asset_type === "cover");
  const audio = detail.assets.find((asset) => asset.asset_type === "audio");

  return (
    <section className="panel detail-panel">
      <div className="panel-header">
        <div>
          <h2>任务详情 #{detail.task.id}</h2>
          <p>{detail.task.input_mode}</p>
        </div>
        <StatusPill state={detail.task.current_state} />
      </div>

      <section className="detail-section" aria-labelledby="generated-script-title">
        <h3 id="generated-script-title">生成文案</h3>
        <p className="script-box">{detail.script?.script_text ?? "暂无文案"}</p>
      </section>

      {finalVideo?.public_url ? (
        <section className="detail-section" aria-labelledby="preview-title">
          <h3 id="preview-title">成片预览</h3>
          <video
            aria-label="成片视频预览"
            className="video-preview"
            controls
            poster={cover?.public_url ?? undefined}
            src={finalVideo.public_url}
          />
          <div className="asset-actions">
            <a href={finalVideo.public_url} download>
              下载视频
            </a>
            {cover?.public_url ? (
              <a href={cover.public_url} download>
                下载封面
              </a>
            ) : null}
            {audio?.public_url ? (
              <a href={audio.public_url} download>
                下载音频
              </a>
            ) : null}
          </div>
        </section>
      ) : null}

      <section className="detail-section" aria-labelledby="assets-title">
        <h3 id="assets-title">产物</h3>
        {detail.assets.length === 0 ? (
          <p className="empty-state">暂无产物</p>
        ) : (
          <div className="compact-list">
            {detail.assets.map((asset) => (
              <div key={asset.id} className="compact-item">
                <strong>{asset.asset_type}</strong>
                <span>{asset.file_path}</span>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="detail-section" aria-labelledby="logs-title">
        <h3 id="logs-title">日志</h3>
        {detail.logs.length === 0 ? (
          <p className="empty-state">暂无日志</p>
        ) : (
          <div className="compact-list">
            {detail.logs.map((log) => (
              <div key={log.id} className="compact-item">
                <strong>{log.step_name}</strong>
                <span>{log.status}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </section>
  );
}
