# RENDER POLICY — where rendering is allowed

## Hard rules

1. **Never render inside the agent sandbox.** No frame generation, no
   `renderer.py`, no ffmpeg, no export of any image sequence or video in the
   assistant's workspace. That environment is for authoring source only.
2. **All rendering happens on GitHub.** The single supported path is the
   `Render film` GitHub Actions workflow (`.github/workflows/render.yml`),
   triggered with `workflow_dispatch`, which renders the frames, muxes the
   audio and publishes the finished MP4 as a release asset.
3. **All deliverables live on GitHub.** Source, assets, docs, the rendered
   video and the release all live in this repository on branch `main`.
   Google Drive holds nothing but a pointer back to GitHub.

Trigger a render:

```bash
curl -X POST \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/tred13/criteria-/actions/workflows/render.yml/dispatches \
  -d '{"ref":"main","inputs":{"start":"0","end":"900","publish_release":"true"}}'
```
