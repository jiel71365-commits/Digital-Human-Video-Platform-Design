import type { VoiceProfile } from "../types";

export function VoiceList({ voices }: { voices: VoiceProfile[] }) {
  return (
    <section className="panel" id="voices">
      <div className="panel-header">
        <div>
          <h2>声音</h2>
          <p>{voices.length} 个声音</p>
        </div>
      </div>

      {voices.length === 0 ? (
        <p className="empty-state">暂无声音</p>
      ) : (
        <div className="compact-list">
          {voices.map((voice) => (
            <div key={voice.id} className="compact-item">
              <strong>{voice.name}</strong>
              <span>
                {voice.provider_key} · {voice.voice_key}
                {voice.is_default ? " · 默认" : ""}
              </span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
