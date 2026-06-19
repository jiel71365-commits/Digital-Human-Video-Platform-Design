import { ClipboardList, PlusCircle, UserRound, Video, Volume2 } from "lucide-react";
import type { ReactNode } from "react";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="主导航">
        <div className="brand">
          <Video aria-hidden="true" />
          <span>数字人口播</span>
        </div>
        <nav>
          <a href="#create-task">
            <PlusCircle aria-hidden="true" />
            新建任务
          </a>
          <a href="#tasks">
            <ClipboardList aria-hidden="true" />
            成片记录
          </a>
          <a href="#humans">
            <UserRound aria-hidden="true" />
            数字人形象
          </a>
          <a href="#voices">
            <Volume2 aria-hidden="true" />
            声音
          </a>
        </nav>
      </aside>
      <section className="workspace">{children}</section>
    </main>
  );
}
