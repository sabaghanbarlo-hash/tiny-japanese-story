# Tiny Japanese Story

A separate copy of the Tiny Japanese YouTube generator where the characters **act out the story**: they walk into a room, look confused, notice each other, wave, change places and backgrounds. The original project (`tiny-japanese-youtube`) is not touched by this one.

Paste a script in the studio page, press the button, get a video (story + vocabulary + grammar + quiz, 1920x1080).

## Make a video
1. Open the studio page (GitHub Pages of this repo: `https://sabaghanbarlo-hash.github.io/tiny-japanese-story/`).
2. Paste a script, press **Make video**. One-time setup: a fine-grained GitHub token limited to this repo (Contents + Actions read/write), saved only in your browser.
3. The render job (GitHub Actions) takes about 10-20 minutes and publishes the video on the page.

Locally: `pip install -r requirements.txt` (plus ffmpeg and a Japanese font), then
`python lesson.py lessons/01-first-day-at-school.txt -o output`. Quick checks: `--preview folder/` saves still frames, `--dummy-audio` skips the voices.

## Script format
Same as the original (`title:` `episode:` `scene:` header, then `[story]` `[vocab]` `[grammar]` `[quiz]`), plus **stage directions** inside `[story]`:

```
@scene classroom
> Mika enters left            # enters left | right, optionally "to center"
& Alex enters right           # "&" = at the same time as the line above
> Alex looks confused         # confused surprised happy sad shy neutral
Alex: ここが きょうしつ？ | Is this the classroom?
> Mika walks to next to Alex  # left center right home | next to Alex | 40 (percent)
> Mika waves
> Alex jumps
> Alex faces Mika            # or: faces left / right
> wait 1.5
> both exit right
@scene hallway                # background change; between directions it switches mid-walk
```
Directions run in order, then the next spoken line plays. When two characters meet they turn toward each other, and the one already there gets a "!". A script with no directions plays like the original (both characters standing in place). Scenes: cafe, station, sakura, restaurant, store, bookstore, classroom, home, airport, street, park, beach, hospital.

## How it is built
- `lesson.py` - copy of the original generator (script parsing, voices, vocab/grammar/quiz slides, encoding) wired to the acting layer.
- `acting.py` - stage directions -> keyframes, and the rigged Mika/Alex drawing (walk cycle, waving arm, expressions).
- `.github/workflows/render.yml`, `docs/index.html` - the render job and the studio page.
- YouTube upload is not wired up here yet.
