# Phase 10 — Video-ready backend
Video jobs are accepted separately from image jobs with provider/model, duration, FPS, aspect ratio, motion strength, reference assets, external job ID and progress. Video processing metadata is attached to the unified media asset model for duration, thumbnail, preview and transcode state.

The provider contract now includes generate_video and get_job_status. The social publishing contract includes publish_video, but the implementation intentionally raises a disabled error until a supported provider/platform flow is enabled.