# Tiny Japanese Story (new system)

A brand-new, separate project. The existing `tiny-japanese-youtube` and `tiny-japanese-video` repos are NOT touched; assets are only copied from them into `assets/`.

## Goal
Story-style lesson videos where characters act out the scene: enter a room, look confused, meet another character, talk, then move to a new place with a new background.

## Approach: 2D puppet rig
- Each character = layered images (body, head, eyes, mouth) plus pose and expression variants.
- Each scene = background + a timeline of actions, defined in a JSON file.
- A renderer draws frames from the timeline (positions, poses, expressions, speech) and encodes the video with ffmpeg.
- Subtitles (Japanese / romaji / English) come from the dialogue lines in the same scene file.

## Layout
```
assets/
  characters/<name>/   body.png, head_*.png, eyes_*.png, mouth_*.png
  backgrounds/         classroom.png, hallway.png, ...
scenes/                story JSON files (see scenes/example_classroom.json)
src/                   renderer (to be built)
out/                   rendered videos
```

## Action vocabulary (scene timeline)
- `enter` / `exit` (from left/right/door), `walk_to`, `face`
- `expression` (neutral, confused, surprised, happy)
- `say` (Japanese, romaji, English, optional audio)
- `wait`
- `cut_to` (change background / setting)

## Next steps
1. Copy existing character and background art into `assets/` (read-only from the old repos).
2. Build the renderer for one scene and test it.
3. Add scene transitions, then the vocabulary / grammar / quiz segments.
4. Connect to the existing upload flow only after the output looks right.
