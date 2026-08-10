# Recording checklist

## Tool pick (pick one)

| Tool | Best for | Cost / risk |
|------|----------|-------------|
| **Loom** | Fast share link, webcam optional | Account; free tier limits |
| **QuickTime** (macOS) | Local file, no account | File → New Screen Recording |
| **OBS** | Higher control, scenes for stills | Setup time |

Lowest friction on this Mac: **QuickTime** for capture → CapCut/Descript/iMovie for stills + VO.

## Capture settings

- [ ] Resolution: **1920×1080** (or native Retina scaled to 1080p export)
- [ ] Frame rate: **30 fps**
- [ ] Mic: quiet room; test 3s of voice first
- [ ] System audio: off (unless you want UI sounds)
- [ ] Mouse highlight: optional; keep pointer large enough to see
- [ ] Do not record the whole desktop—**one browser window**

## Pre-flight

- [ ] API healthy (`GET /health` or Swagger loads)
- [ ] Frontend loads; pipeline will complete (warm run once off-camera)
- [ ] Sample resume + constraints filled (don’t type live unless polished)
- [ ] Notifications off (Focus / Do Not Disturb)
- [ ] Stills ready: `docs/video/stills/*.png`

## Record

1. Start recording → open title still full-screen (Preview) **or** insert stills in edit later.
2. Switch to browser; run shots B→H from the [shot list](02-shot-list.md).
3. Stop recording; save as `aptitude-search-demo-raw.mov` (or Loom link).

## Edit (minimum)

1. Import raw + `stills/title-card.png`, `beat-three-stages.png`, `end-card.png`.
2. Lay VO from [script](01-script-storyboard.md) (or record VO in Descript over the picture).
3. Trim dead air; jump-cut pipeline wait.
4. Export **H.264 / 1080p / ~45s**.
5. Filename: `aptitude-search-demo-45s.mp4`.

## Publish tips

- First frame = title card (good thumbnail).
- Description one-liner: *Beyond the obvious job search — resume to verified openings.*
- Link product or repo only if you’re ready for traffic.
