import type { Wav2LipRuntimeStatus } from "../types";

const READY_MESSAGE = "\u771f\u5b9e\u53e3\u578b\u540c\u6b65\u5df2\u5c31\u7eea";
const FALLBACK_MESSAGE = "\u5f53\u524d\u4f7f\u7528\u672c\u5730\u9884\u89c8\u6e32\u67d3";

export function RuntimeStatus({ status }: { status: Wav2LipRuntimeStatus | null }) {
  if (!status) {
    return null;
  }

  const title = status.available ? "Wav2Lip" : "Fallback";
  const message = status.available ? READY_MESSAGE : FALLBACK_MESSAGE;

  return (
    <section className="runtime-status" aria-label="Wav2Lip runtime status">
      <div>
        <strong>{title}</strong>
        <span>{message}</span>
      </div>
      {status.available ? null : (
        <div className="runtime-status-details">
          {status.missing_requirements.slice(0, 3).map((item) => (
            <span key={item}>{item}</span>
          ))}
          <code>{status.setup_command}</code>
        </div>
      )}
    </section>
  );
}
