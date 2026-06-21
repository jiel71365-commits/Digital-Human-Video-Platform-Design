import type { RendererRuntimeStatus, RendererRuntimeStatuses } from "../types";

const READY_MESSAGE = "\u771f\u5b9e\u53e3\u578b\u540c\u6b65\u5df2\u5c31\u7eea";
const HIGH_QUALITY_READY_MESSAGE = "\u9ad8\u8d28\u91cf\u53e3\u578b\u540c\u6b65\u5df2\u5c31\u7eea";
const FALLBACK_MESSAGE = "\u5f53\u524d\u4f7f\u7528\u672c\u5730\u9884\u89c8\u6e32\u67d3";

export function RuntimeStatus({ status }: { status: RendererRuntimeStatuses | null }) {
  if (!status) {
    return null;
  }

  const activeRenderer = status.renderers[status.active_renderer];
  const musetalk = status.renderers.musetalk;
  const wav2lip = status.renderers.wav2lip;
  const title = getRendererTitle(status.active_renderer, activeRenderer);
  const message = getRendererMessage(status.active_renderer, activeRenderer);
  const missingRequirements = collectMissingRequirements(musetalk, wav2lip);
  const setupCommand =
    musetalk?.setup_command || wav2lip?.setup_command || activeRenderer?.setup_command || "";

  return (
    <section className="runtime-status" aria-label="renderer runtime status">
      <div>
        <strong>{title}</strong>
        <span>{message}</span>
      </div>
      {activeRenderer?.available ? null : (
        <div className="runtime-status-details">
          {missingRequirements.slice(0, 4).map((item) => (
            <span key={item}>{item}</span>
          ))}
          {setupCommand ? <code>{setupCommand}</code> : null}
        </div>
      )}
    </section>
  );
}

function getRendererTitle(activeRendererKey: string, activeRenderer?: RendererRuntimeStatus) {
  if (activeRendererKey === "musetalk" && activeRenderer?.available) {
    return "MuseTalk";
  }
  if (activeRendererKey === "wav2lip" && activeRenderer?.available) {
    return "Wav2Lip";
  }
  return "Fallback";
}

function getRendererMessage(activeRendererKey: string, activeRenderer?: RendererRuntimeStatus) {
  if (activeRendererKey === "musetalk" && activeRenderer?.available) {
    return HIGH_QUALITY_READY_MESSAGE;
  }
  if (activeRendererKey === "wav2lip" && activeRenderer?.available) {
    return READY_MESSAGE;
  }
  return FALLBACK_MESSAGE;
}

function collectMissingRequirements(
  musetalk?: RendererRuntimeStatus,
  wav2lip?: RendererRuntimeStatus
) {
  return [
    ...(musetalk?.missing_requirements ?? []),
    ...(wav2lip?.missing_requirements ?? [])
  ];
}
