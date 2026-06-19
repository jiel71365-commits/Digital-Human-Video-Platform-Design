import type { DigitalHumanProfile } from "../types";

export function ProfileList({ humans }: { humans: DigitalHumanProfile[] }) {
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
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
