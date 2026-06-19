# Digital Human Video Platform Design

## Background

This project will build a digital human production platform for batch口播 video generation. The first phase focuses on a stable video-generation workflow rather than livestreaming. The platform should integrate multiple AI capabilities, including script generation, script polishing, voice generation, digital human rendering, and automated post-processing.

Reference projects considered:

- `fa1314/KrLongAI`: batch口播 video automation, including script extraction, rewriting, voice cloning, digital human generation, subtitles, BGM, covers, and publishing.
- `lipku/LiveTalking`: real-time or near real-time digital human rendering foundation, including Wav2Lip/MuseTalk-style integrations, TTS, WebRTC, RTMP, and API usage.
- `l11223/digital-human-livestream`: livestream-focused digital human system built around interaction, personas, safety, memory, and a management UI.

These projects are references for product direction and integration targets. Direct code reuse requires later license and attribution review.

## First Phase Goal

Build a single-machine Web management platform that can generate digital human口播 videos through a serial task pipeline.

The first phase prioritizes:

- A usable Web backend for task creation and result review.
- Three input modes.
- Script generation or normalization.
- TTS audio generation.
- Digital human video rendering.
- Automated post-processing.
- Final MP4 and cover generation.
- Clear logs, task states, and retry support.

The first phase does not include livestreaming, knowledge bases, product libraries, team permissions, platform publishing, analytics, or concurrent GPU scheduling.

## Product Scope

### Included

- Input mode 1: topic or product material to generated script.
- Input mode 2: existing口播 script to video.
- Input mode 3: reference video upload or link to extracted/rewritten script.
- Digital human profiles based on built-in or uploaded fixed avatar material.
- Future custom digital human training or cloning capability reserved as an extension.
- General TTS voices as the default voice path.
- Voice cloning reserved as an advanced provider capability.
- Automated subtitles, BGM, intro/outro, cover generation, and MP4 export.
- Web pages for dashboard, task creation, digital human profile management, voice management, and task/result details.
- Single GPU server deployment with local model inference.
- Serial task execution, one active generation task at a time.
- Cloud LLM API for script generation and rewriting.

### Excluded From Phase One

- Product library.
- Knowledge base.
- Multi-account publishing.
- Multi-platform auto publishing.
- Team permissions.
- Analytics dashboard.
- Multi-task concurrent generation.
- Visual workflow builder.
- Digital human livestreaming.

## Recommended Approach

Use a lightweight Web platform plus a serial generation pipeline with plugin-style adapters.

This gives the system a durable platform structure without overbuilding a workflow engine. It also keeps the first implementation focused on the main value: generating complete digital human口播 videos reliably.

Alternative approaches considered:

- Full AI workflow platform: more flexible, but too much first-phase complexity in node editing and workflow state.
- Minimal video tool only: fastest for a demo, but would likely require restructuring when adding profiles, voices, logs, retries, and history.

## System Architecture

The first-phase system has four layers.

### Web Management UI

The Web UI handles:

- Task creation.
- Digital human profile management.
- Voice profile management.
- Task status review.
- Result preview and download.
- Failure reason and log review.

### Backend API And Orchestration

The backend handles:

- Persisting configuration and task records.
- Validating inputs.
- Calling the cloud LLM provider.
- Calling the TTS provider.
- Dispatching local avatar rendering.
- Running post-processing.
- Recording step logs and errors.
- Managing retry from failed steps.

### Local Model And Media Processing Layer

The local layer handles:

- Digital human rendering through the default avatar renderer.
- FFmpeg-based media operations.
- Subtitle rendering.
- BGM mixing.
- Intro/outro composition.
- Cover extraction or generation.

### External Services

The first phase depends on:

- Cloud LLM API for script generation, normalization, and rewriting.
- TTS provider for general voice synthesis.

Voice cloning providers and local LLMs are extension points, not required for the first usable version.

## Suggested Technical Stack

- Backend API: FastAPI.
- Database: SQLite for phase one, with a path to PostgreSQL later.
- Task execution: single local worker running tasks serially.
- File storage: local `storage/` directory, grouped by task ID.
- Frontend: React or Vue management UI.
- Media processing: FFmpeg.
- Digital human rendering: default `AvatarRenderer` adapter for LiveTalking/Wav2Lip-style execution.
- LLM: configurable cloud API provider.
- TTS: configurable general TTS provider.

## Provider And Adapter Interfaces

The backend should depend on stable provider interfaces rather than specific model repository internals.

### LLMProvider

Inputs:

- Task input type.
- Topic, product material, existing script, or extracted reference material.
- Style and duration targets.

Outputs:

- Structured口播 script.
- Suggested segment breaks.
- Tone or delivery notes.
- Optional title and cover copy suggestions.

Modes:

- Generate from topic or product material.
- Normalize an existing script.
- Rewrite from reference video material.

### TTSProvider

Inputs:

- Script text.
- Voice profile.
- Speaking style.

Outputs:

- Audio file path.
- Duration.
- Sentence-level or word-level timing if available.

If precise timing is unavailable in phase one, sentence-level timing or estimated timing is acceptable.

### AvatarRenderer

Inputs:

- Digital human profile.
- Audio file.
- Render configuration.

Outputs:

- Raw digital human口播 video.
- Render duration.
- Logs and error details.

The default adapter should target LiveTalking/Wav2Lip-style rendering. MuseTalk and other models can be added later behind the same interface.

### PostProcessor

Inputs:

- Raw rendered video.
- Script and subtitle timing.
- Audio.
- BGM.
- Intro/outro configuration.
- Cover strategy.

Outputs:

- Final MP4.
- Cover image.
- Processing logs.

FFmpeg should be the primary implementation tool.

## Task Flow

The system uses three input modes but normalizes them into one standard `VideoTask` pipeline.

### Input Mode 1: Topic Or Product Material

The user provides:

- Topic or product description.
- Key selling points.
- Target style.
- Target duration.
- Selected digital human.
- Selected voice.
- Post-processing template.

The system generates a口播 script before entering the main media pipeline.

### Input Mode 2: Existing Script

The user provides:

- Existing口播 script.
- Selected digital human.
- Selected voice.
- Post-processing template.

The system skips original script generation and performs normalization and validation before TTS.

### Input Mode 3: Reference Video Or Link

The user provides:

- Uploaded reference video, or a link where supported.
- Rewrite style or constraints.
- Selected digital human.
- Selected voice.
- Post-processing template.

Phase one should prioritize uploaded video. Link parsing can be optional because platform anti-crawling, login, and rate limits can make it unreliable.

## Generation Pipeline

1. Create task.
2. Prepare script.
3. Validate and review script.
4. Generate TTS audio.
5. Render raw digital human video.
6. Apply post-processing.
7. Save result and metadata.
8. Allow preview, download, and retry if needed.

## Multi-Agent Responsibilities

The first phase should implement these as logical agents or service modules, not necessarily as independent autonomous processes.

### Planning Agent

Converts topic or product material into a video structure and determines the script direction.

### Script Agent

Generates, normalizes, or rewrites口播 scripts.

### Review Agent

Checks for empty content, sensitive words, repeated text, duration mismatch, invalid model output, and obvious formatting problems.

### Voice Agent

Generates TTS audio from the selected voice profile.

### Avatar Rendering Agent

Calls the avatar renderer plugin and produces the raw口播 video.

### Post-Processing Agent

Adds subtitles, BGM, intro/outro, cover, and final MP4 export.

### Record Agent

Persists task status, logs, artifacts, and final result metadata.

## Task States

Recommended task states:

- `draft`: task is being prepared.
- `queued`: task has been submitted.
- `script_ready`: script output is ready.
- `audio_ready`: TTS output is ready.
- `rendered`: raw digital human video is ready.
- `post_processed`: final media processing is complete.
- `completed`: final result is available.
- `failed`: a step failed.

Each step should store:

- Status.
- Start time.
- End time.
- Duration.
- Artifact paths.
- User-facing error message.
- Technical log or stack trace.

## Web Pages

### Dashboard

Shows:

- Current task status.
- Recent generated videos.
- Failed tasks.
- GPU/model service status.
- Quick action to create a new video task.

This is an operational dashboard, not a full analytics page.

### New Video Task

A step-by-step form:

1. Select input mode.
2. Fill text or upload material.
3. Select digital human profile.
4. Select voice profile.
5. Select post-processing template.
6. Submit task.

### Digital Human Profiles

Manages:

- Name.
- Preview image.
- Source video or image.
- Default crop or aspect ratio.
- Compatible renderer.
- Status.

Custom training or cloning is reserved for later and should not appear as a misleading finished feature in phase one.

### Voice Profiles

Manages:

- Name.
- Provider.
- Gender or style tags.
- Preview audio.
- Default flag.
- Status.

Voice cloning fields and provider capability can be reserved internally.

### Task And Result Records

Shows:

- Input content.
- Generated script.
- Step status.
- Logs.
- Intermediate artifacts.
- Final MP4.
- Cover.
- Download action.
- Retry action from failed step.

## Core Data Objects

### DigitalHumanProfile

Represents one reusable digital human avatar configuration.

Key fields:

- ID.
- Name.
- Preview image path.
- Source media path.
- Default aspect ratio.
- Renderer adapter key.
- Status.
- Created time.
- Updated time.

### VoiceProfile

Represents one reusable voice configuration.

Key fields:

- ID.
- Name.
- Provider key.
- Voice key.
- Style tags.
- Preview audio path.
- Is default.
- Status.
- Created time.
- Updated time.

### VideoTask

Represents one video generation task.

Key fields:

- ID.
- Input mode.
- Raw input.
- Selected digital human ID.
- Selected voice ID.
- Post-processing template ID.
- Current state.
- Failed step.
- Final video path.
- Cover path.
- Created time.
- Updated time.

### ScriptDraft

Represents generated or normalized script output.

Key fields:

- ID.
- Task ID.
- Version.
- Script text.
- Structured segments.
- Estimated duration.
- Source mode.
- Created time.

### MediaAsset

Represents uploaded, intermediate, and final media artifacts.

Key fields:

- ID.
- Task ID.
- Asset type.
- File path.
- Duration.
- Metadata.
- Created time.

### GenerationStepLog

Represents one pipeline step execution.

Key fields:

- ID.
- Task ID.
- Step name.
- Status.
- Started time.
- Finished time.
- Duration.
- Error code.
- User message.
- Technical log.

### PostProcessTemplate

Represents reusable post-processing settings.

Key fields:

- ID.
- Name.
- Subtitle style.
- BGM path.
- Intro media path.
- Outro media path.
- Cover strategy.
- Created time.
- Updated time.

## Error Handling

- Every pipeline step must validate its inputs before running.
- Every pipeline step must validate expected outputs after running.
- A failed step should move the task to `failed` and record both user-facing and technical details.
- Retry should start from the failed step when previous artifacts are still valid.
- If LLM output is invalid, the system should record the raw response and provide a retry action.
- If TTS output is missing or unreadable, the system should fail before avatar rendering.
- If avatar rendering fails, post-processing must not run.
- If FFmpeg fails, the raw rendered video should remain available for diagnosis.
- Reference links should degrade gracefully to an instruction to upload the video file manually.

## Testing Strategy

### Unit Tests

Cover:

- Input validation.
- Task state transitions.
- Provider result schemas.
- Path generation.
- Error recording.
- Retry step selection.

### Integration Tests

Use mocked providers to test the full pipeline:

- Mock LLM output.
- Mock TTS audio artifact.
- Mock avatar renderer video artifact.
- Mock post-processor final output.

The test should verify that task state, logs, media assets, and final result metadata are correct.

### Media Tool Tests

Verify:

- FFmpeg is installed and callable.
- Audio duration can be read.
- Video duration can be read.
- Expected output files exist after processing.

### Minimal End-To-End Test

Use:

- One short script.
- One default voice.
- One default digital human profile.
- One post-processing template.

Expected result:

- A downloadable MP4.
- A generated cover image.
- Complete step logs.

## Milestones

### Milestone 1: Architecture Skeleton

Build:

- Web backend.
- Database schema.
- Local storage layout.
- Task state machine.
- Basic Web UI shell.

### Milestone 2: Existing Script Task Loop

Build:

- Existing script input.
- Task creation.
- TTS mock or real TTS.
- Task record and logs.
- Result page shell.

### Milestone 3: Digital Human Rendering

Build:

- Default `AvatarRenderer`.
- Digital human profile selection.
- Raw口播 video generation.

### Milestone 4: Post-Processing

Build:

- Subtitle generation.
- BGM mixing.
- Intro/outro support.
- Cover generation.
- Final MP4 export.

### Milestone 5: Intelligent Script Generation

Build:

- Cloud LLM provider.
- Topic/product material input.
- Existing script normalization.
- Script review checks.

### Milestone 6: Reference Video Input

Build:

- Reference video upload.
- Audio/subtitle/basic information extraction.
- Rewrite prompt path.

### Milestone 7: Management Completion

Build:

- Digital human profile management.
- Voice profile management.
- Failure retry.
- Log viewer.
- Result preview and download.

## Acceptance Criteria

The first phase is accepted when:

- The Web UI can create tasks from all three input modes.
- A user can select a digital human profile and voice profile.
- The system can generate or normalize a script.
- The system can generate audio.
- The system can render a raw digital human口播 video.
- The system can apply subtitles, BGM, intro/outro, cover generation, and final MP4 export.
- The result page can preview or download the final MP4.
- Failed tasks show a clear failure reason and can retry from the failed step.
- The system runs one task at a time on a single GPU server.

## Future Extensions

- Digital human livestreaming.
- Product library.
- Knowledge base and retrieval-augmented script generation.
- Multi-platform publishing.
- Team permissions.
- Data analytics.
- Multi-GPU or concurrent task scheduling.
- Visual workflow editor.
- Local LLM provider.
- Higher-quality renderers such as MuseTalk or ER-NeRF.
- Full custom digital human training.
- Voice cloning workflow.
