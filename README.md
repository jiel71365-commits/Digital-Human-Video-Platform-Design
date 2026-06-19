# Digital Human Video Platform

This repository contains the design and implementation for a digital human video generation platform.

The first runnable MVP focuses on:

- FastAPI backend.
- SQLite persistence.
- Serial video task pipeline.
- Mock LLM, TTS, avatar rendering, and post-processing providers.
- React Web management UI.

The current implementation phase does not include real livestreaming, real digital human rendering, real cloud LLM calls, or real TTS. Those integrations are designed as provider replacements.

## Documentation

- Design spec: `docs/superpowers/specs/2026-06-19-digital-human-video-platform-design.md`
- MVP plan: `docs/superpowers/plans/2026-06-19-digital-human-video-platform-mvp.md`
