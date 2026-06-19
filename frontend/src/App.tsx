export function App() {
  return (
    <main className="app-shell">
      <section className="hero" aria-labelledby="dashboard-title">
        <p className="eyebrow">工作台</p>
        <h1 id="dashboard-title">数字人口播视频工作台</h1>
        <p>
          管理数字人、声音、模板和视频生成任务。当前前端仅提供 MVP
          工作台骨架，后续任务会接入完整交互。
        </p>
      </section>

      <section className="workspace" aria-labelledby="workspace-title">
        <div>
          <p className="section-kicker">工作台</p>
          <h2 id="workspace-title">任务概览</h2>
        </div>
        <div className="dashboard-grid">
          <article>
            <span>数字人</span>
            <strong>待接入</strong>
          </article>
          <article>
            <span>声音</span>
            <strong>待接入</strong>
          </article>
          <article>
            <span>生成任务</span>
            <strong>待接入</strong>
          </article>
        </div>
      </section>
    </main>
  );
}
