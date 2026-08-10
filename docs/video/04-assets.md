# Assets — copy, titles, stills

## Brand / on-screen titles

| Use | Text |
|-----|------|
| Brand (hero) | Aptitude Search |
| Tagline | Beyond the obvious job search |
| Mid-beat | Three stages. One search. |
| Mid-beat sub | Profile · Role families · Verified jobs |
| End CTA | Try the pipeline |
| End support | Resume → aptitude profile → verified openings |

Aligns with product copy: resume → aptitude profile → **verified openings** (`verified_matches`). Stage 3 is job search—not a draft-only path.

## Short descriptions (upload / social)

**One line:**  
Aptitude Search turns a resume into verified job openings that fit how you work—not just keyword titles.

**Two lines:**  
Paste a resume. Infer aptitudes, map role families, and search the live web for open postings.  
Get verified matches with real links—beyond the obvious job search.

## Thumbnail text options

1. Aptitude Search  
2. Beyond keyword search  
3. Resume → verified jobs  

## Stills (PNG, 16:9)

| File | Role |
|------|------|
| [stills/title-card.png](stills/title-card.png) | Open (0:00) |
| [stills/beat-three-stages.png](stills/beat-three-stages.png) | Mid beat (~0:26) |
| [stills/end-card.png](stills/end-card.png) | Close / CTA |

Also available for thumbnails: repo banner at `assets/banner.png`.

## Mock frame notes (if you recreate stills)

- Background: `#fafafa`
- Text: `#09090b`
- Accent: `#15803d` (product CTA green)
- Avoid purple gradients, cream/serif “AI brochure” look, floating badges on UI screenshots

## Sample on-camera data

Use the fixture body so the demo is reproducible:

- Resume + constraints: `fixtures/pipeline-request-example.json`
- Endpoint (optional B-roll): `POST /v1/pipeline`
- Result field to highlight: `verified_matches`
