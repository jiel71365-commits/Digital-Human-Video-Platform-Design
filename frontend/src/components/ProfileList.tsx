import type { DigitalHumanProfile } from "../types";

type ProfileListProps = {
  humans: DigitalHumanProfile[];
  onUploadSourceMedia?: (profileId: number, file: File) => Promise<void>;
};

export function ProfileList({ humans, onUploadSourceMedia }: ProfileListProps) {
  async function handleSourceMediaChange(
    profileId: number,
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    const file = event.target.files?.[0];
    if (!file || !onUploadSourceMedia) {
      return;
    }

    await onUploadSourceMedia(profileId, file);
    event.target.value = "";
  }

  return (
    <section className="panel" id="humans">
      <div className="panel-header">
        <div>
          <h2>数字人形象</h2>
          <p>{humans.length} 个形象</p>
        </div>
      </div>

      {humans.length === 0 ? (
        <p className="empty-state">暂无数字人形象</p>
      ) : (
        <div className="compact-list">
          {humans.map((human) => (
            <div key={human.id} className="compact-item">
              <strong>{human.name}</strong>
              <span>
                {human.renderer_adapter_key} · {human.default_aspect_ratio}
              </span>
              {human.source_media_path ? (
                <span>源素材：{human.source_media_path}</span>
              ) : (
                <span>源素材：未上传</span>
              )}
              {onUploadSourceMedia ? (
                <label className="file-upload-control">
                  上传素材
                  <input
                    aria-label="上传素材"
                    accept="video/mp4,video/quicktime,image/png,image/jpeg"
                    type="file"
                    onChange={(event) => void handleSourceMediaChange(human.id, event)}
                  />
                </label>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
