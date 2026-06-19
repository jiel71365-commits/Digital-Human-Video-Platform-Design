import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "../src/App";

describe("App", () => {
  it("renders the dashboard heading", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "数字人口播视频工作台" })).toBeTruthy();
  });
});
