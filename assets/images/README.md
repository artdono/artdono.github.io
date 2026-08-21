# Images

Drop files here with exactly these names and they appear on the site. No code
changes needed — a missing file shows a neutral placeholder, never a broken icon.

| File | Where it appears | Shape it is cropped to |
|---|---|---|
| `portrait.jpg` | About me, beside the text | portrait, 4:5 |
| `about/photo-1.jpg` | About me, photo grid, first | portrait, 3:4 |
| `about/photo-2.jpg` | About me, photo grid, second | landscape, 4:3 |
| `about/photo-3.jpg` | About me, photo grid, third | landscape, 4:3 (16:9 on tablet) |
| `og-preview.png` | Link preview when the site is shared | 1200 × 630 |

Photos are cropped with `object-fit: cover`, so the centre of the frame survives
and the edges may be trimmed. Keep the subject near the middle.

Aim for roughly 1600px on the long edge and under ~400KB each — this site has no
image pipeline, so what you commit is what visitors download.

To change a filename, a caption, or the alt text, edit `data/content.json` and
run `python3 scripts/build.py`.
