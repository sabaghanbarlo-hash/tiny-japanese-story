# Directing guide (Tiny Japanese Story)

The studio does not guess a story from plain text: it plays a **directed script**. The usual workflow is to tell Claude the story idea ("Mika and Alex go to an amusement park, buy cotton candy, come back and ride the rides") and paste the directed script Claude writes into the studio page. This guide is the full vocabulary, so any story can be written with it.

## Script skeleton
```
title: A Day at the Amusement Park
episode: 2
scene: amusement park        # starting place

[story]
@scene amusement park        # change place (also allowed between directions)
> Mika enters left           # direction lines start with ">"; "&" = at the same time as the line above
Mika: こんにちは！ | Hello!   # spoken line: Speaker: Japanese | English | (optional romaji)
[vocab] [grammar] [quiz]     # same as the original generator
```
Directions run in order; then the next spoken line plays. Speech cannot happen during a direction (a ride or a walk), so put the comment *after* it.

## Directions (who = Mika, Alex, both)
| Direction | Notes |
|---|---|
| `enters left` / `enters right` / `enters left to center` | walks in from off-screen to home (or the spot) |
| `walks to <spot>` / `runs to <spot>` | spot: left, center, right, home, `next to Alex`, a percent (40), or a named spot of the place |
| `exits left` / `exits right` | walks off-screen |
| `looks <feeling>` | confused, surprised, happy, sad, shy, neutral (also: excited, worried, embarrassed...) |
| `faces <name / left / right>`, `looks at <name>` | |
| `waves`, `jumps`, `laughs`, `nods`, `cheers` | |
| `holds <item>`, `buys <item>`, `picks up <item>` | `buys` adds a little hop |
| `eats`, `eats <item>`, `drinks` | edible: cotton candy, ice cream, popcorn (3 bites, the item shrinks) |
| `drops` / `finishes` | puts the item away |
| `gives <item> to <name>` | `gives it to Alex` also works |
| `rides the carousel` / `rides the ferris wheel [for 8]` | amusement park only; walks to the ride, boards, rides, steps off |
| `wait 1.5` | pause (seconds) |

`both` does the same for both characters and spreads them out so they do not stand on the same spot. When two characters meet, they turn toward each other and the one already there gets a "!". Expressions stay until changed (`looks neutral` resets).

## Items
cotton candy, ice cream, balloon, ticket, drink, bag, book, popcorn, plush (prize toy). Items are not drawn while riding.

## Places and their spots
| Place (`@scene ...`) | Named spots |
|---|---|
| amusement park (fair, funfair, carnival) | entrance, ticket booth, carousel, cotton candy stall, prize stall (game stall), ferris wheel, bench. Rides: carousel, ferris wheel |
| shrine (temple, torii) | torii gate, offering box, lantern, steps |
| zoo | entrance, giraffe, elephant, fence |
| aquarium | big tank, jellyfish, shark, entrance (fish and jellyfish swim) |
| classroom | door, blackboard, desk |
| cafe | counter, window, door |
| station | platform, ticket gate, ticket machine |
| store | register, shelf, door |
| home, bookstore, restaurant, airport, street (night), park, beach, hospital, sakura | no named spots yet (use left / center / right / percent) |

## Adding things (for whoever extends the engine)
- New place: add its colors to `NEW_SCENES`, a drawing function to `SCENE_DRAW`, spots to `LANDMARKS` (all in `acting.py`).
- New item: draw it in `_draw_item` and add it to `ITEMS` (and `EDIBLE` if it can be eaten).
- New ride: moving scenery goes in `draw_dynamic`, rider position in `ride_pos`, spot in `RIDES`.
- New verb: add the word to `VERBS`, then handle it in `Stage._one`.
