# Images

Drop files here with exactly these names and they appear on the site. No code
changes needed — a photo that is not there yet shows a neutral placeholder,
never a broken image.

| File | Where it appears | Cropped to |
|---|---|---|
| `portrait.jpg` | Hero, beside your name | portrait, 4:5 |
| `about/photo-1.jpg` | About me, beside the text | portrait, 4:5 |
| `about/photo-2.jpg` | About me, photo grid, first | portrait, 3:4 |
| `about/photo-3.jpg` | About me, photo grid, second | portrait, 3:4 |
| `about/photo-4.jpg` | About me, photo grid, third | portrait, 3:4 |
| `og-preview.png` | Link preview on LinkedIn and in messages | 1200 × 630 |

Every frame is portrait, because every photo here is. Cropping is
`object-fit: cover` from the centre, so keep the subject near the middle —
the left and right edges are what get trimmed.

Aim for roughly 1600px on the long edge and under ~400KB each. This site has
no image pipeline: what you commit is what visitors download.

To change a filename, caption, or alt text, edit `data/content.json` and run
`python3 scripts/build.py`.
