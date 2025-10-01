what’s solid

* **Single, focused job.** The CLI does one thing cleanly: transcribe one audio file → JSON, with flags that matter (`--language`, `--language-routing`, `--probe-seconds`, `--no-probe`, `--out`, `--temperature`, `--debug`). Defaults are sensible and centrally defined.
* **Tidy configuration.** `TranscriptionConfig` centralizes models, allowed extensions (`.mp3`, `.m4a`, `.wav`), defaults, exit codes, ffmpeg and temp settings, and helper getters. This keeps behavior predictable.
* **Input hygiene.** You validate path existence + extension before work starts, and raise clear errors. 
* **Optional language routing that degrades gracefully.** If enabled, you try a short **ffmpeg** probe → quick transcription → keyword check → then full pass; if not, Whisper auto-detects. Metadata records routing decisions. 
* **Logging done right.** Per-module loggers, console/file handlers, on/off via CLI, plus helpers to tweak levels. Tests verify format and file outputs. 
* **Tests with structure.** Fixtures are rich; you cover config, language detection (pure + mocked), transcription, CLI, logging; and you validate CLI helpers (`setup_logging_from_args`, `perform_transcription`, `output_transcription_result`). 
* **Developer niceties.** There’s a `--dry-run` that outputs a realistic JSON skeleton without hitting the API, and the CLI tries to load a local `.env` automatically.

# Critic — what’s brittle or misleading

* **Import paths in some tests.** I see references that imply `transcribe_audio.src.core...` vs the actual `transcribe_audio.core...`. That will cause mocks to “miss” and create flaky tests. Audit/normalize all patch targets. 
* **Keyword language detection is crude.** It’s fine as a heuristic, but mixed speech and domain words will slip through. (You already fall back to Whisper, so keep expectations modest.) 
* **Client creation split across paths.** `detect_language_with_probe` can spin up its own OpenAI client if `client` is `None`. That makes retries/timeouts and test seams harder to reason about. Centralize. 
* **ffmpeg UX.** When ffmpeg is missing/fails, users might not notice they lost the “probe” speedup unless they read logs carefully. You do log a message, but it’s easy to miss. Surface one clear line. 

# Advisor — small, surgical upgrades that keep scope tight

1. **Single `get_client()` path.** Always pass a client in (routing + full transcription). Put timeouts/retries in config/env and test them once. (You already have `TranscriptionConfig.get_client`—make everything use it.) 
2. **Make routing telemetry explicit.** You already stash `_meta.routed_language` and `probe_seconds`; add `_meta.ffmpeg_used` (you’re close — it’s populated upstream) and keep the CLI printing a one-liner if probe wasn’t used.
3. **Normalize test patch targets.** Replace any lingering `...src.core...` with the real import paths your code uses. This removes “mock didn’t apply” headaches. 
4. **Tighten dependency bounds you actually validated.** You already set `openai>=1.40,<2.0` in pyproject/requirements — good. Keep this in the README and CI so future upgrades are intentional. 
5. **CLI UX polish (no scope creep):**

   * When `--language-routing` is on but ffmpeg isn’t used, log **one** user-facing line: “ffmpeg not available; using full file for detection.” (You already have a similar info path.) 
   * Keep `--dry-run` exactly as is (great for smoke tests), but ensure its `_meta` mirrors real runs (ffmpeg flags, models, etc.) — you’re already doing this. 
6. **Batch, but stay simple.** You’ve sketched stdin batch handling (one path per line). That’s perfect minimalism: process sequentially, emit one JSON per file, no concurrency. Don’t add queues/workers here. 

# Quick correctness checklist (actionable)

* [ ] Ensure **every** internal call path uses `TranscriptionConfig.get_client()`; remove ad-hoc client creation in detection. 
* [ ] Add/confirm `_meta.ffmpeg_used` is set consistently and printed via CLI when routing is enabled.
* [ ] Sweep tests for `src` in import paths and fix. 
* [ ] Keep the allowed extensions list and validation exactly as implemented (no FLAC etc., by design).
* [ ] Keep the dependency pin and note it in docs/CI. 
