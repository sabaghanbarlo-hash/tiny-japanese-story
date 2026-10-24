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
Same as the original (`title:` `episode:` `scene:` header, then `[story]` `[vocab]` `[grammar]` `[quiz]`), plus **stage directions** inside `[story]` (lines starting with `>`; `&` = at the same time as the line above):

```
@scene amusement park
> Mika enters left
& Alex enters left
> Alex looks surprised
> both walk to the cotton candy stall
> Alex buys cotton candy
> both eat
> both ride the carousel
> Mika waves
```
Characters walk, run, react, hold and eat things (cotton candy, ice cream, balloon, ticket, umbrella...), give things to each other, ride the carousel and Ferris wheel, and move between places. Places: amusement park, shrine, zoo, aquarium, cafe, classroom, station, store, home, bookstore, restaurant, airport, street, park, beach, hospital, sakura, town, mountain, river, train, bedroom, kitchen, schoolyard, festival, bus stop - many have named spots to walk to, and every place comes in three looks (normal, warm, cool) so the backgrounds do not repeat.

**Weather and time of day:** rain, storm and snow really fall on outdoor places, with ripples on the ground and an umbrella that keeps its owners dry; morning, sunset and night change the light. They start by themselves when the story says so ("It's raining!", "I have an umbrella!", "The rain stopped!"), or you set them with `@weather rain`, `@time night`, `> Mika opens the umbrella`.

**You do not have to write directions yourself**: copy the director prompt from the studio page (or `DIRECTOR_PROMPT.md`) into any Claude chat with your story idea and it writes the directed script. The complete vocabulary is in [DIRECTING.md](DIRECTING.md). A script with no directions plays like the original (both characters standing in place).

## How it is built
- `lesson.py` - copy of the original generator (script parsing, voices, vocab/grammar/quiz slides, encoding) wired to the acting layer.
- `acting.py` - stage directions -> keyframes, the rigged Mika/Alex drawing (walk cycle, waving arm, expressions, held items), rides and moving scenery.
- `atmos.py` - weather (rain, storm, snow), time-of-day colour grading, umbrellas, and reading the story text to start/stop them.
- `scenery.py` - the newer places (town, mountain, river, train, bedroom, kitchen, schoolyard, festival, bus stop), their animations and the three looks per place.
- `.github/workflows/render.yml`, `docs/index.html` - the render job and the studio page.

## Automatic YouTube upload
When a render finishes, the video is published on the studio page. The `tiny-japanese-youtube` repository has a small job (`Upload story videos`) that checks this repository for new videos every 10 minutes and uploads each one to the @tinyjapanese channel with the title, description and chapters from `<name>.description.txt` and the cover image. The YouTube link is saved there as `story-uploads/<name>.youtube.txt`, and the studio page shows it as soon as it exists. Nothing needs to be pressed. It uses the YouTube login already stored in that repository (privacy is `private` unless the repository variable `YT_PRIVACY` says otherwise). Details are in that repository's README.
