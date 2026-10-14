# Changelog

All notable changes to the English translation patch. Versions match the GitHub Releases.

## Unreleased

### Translation
- Kunlun: the answers to the Five Kaiyan Generals now use the same words as the Pyramid Book
  (Flesh / Body Heat / Breath / Blood / Organs), and their window is wider so "Body Heat" fits.
- Airport: full country names ("Hong Kong" instead of "HongKong"); destination window widened.
- "Attack who?" / "Use it on who?".
- About 100 messages reflowed: sentences that were broken mid-line now use fewer lines when they fit
  (the wording itself is unchanged).

### Fixes to the original game
- **Hole in the wall of the Treasury labyrinth (Olympia, Greece).** In the labyrinth behind the locked door on
  the Treasury's B1, one wall cell just below the path, on the screen below the chest with the Book of Almadel,
  was walkable in the original Japanese game. Stepping through it let the party walk off the path into the
  empty area around the candles, and walking from there into the screen on the right left the party stuck at
  the screen edge.
  - **How to reproduce (original game or earlier patches):** in the Treasury labyrinth, go to the screen just
    below the Book of Almadel chest. On the path, find the cell where the wall below the path has a gap (under the
    party in the screenshot) and walk down: you leave the path. Walk right into the next screen and the party
    gets stuck.
  - **Cause:** the map (no. `$4D`) uses block `$1BA` (walkable) for that single wall cell instead of the wall
    block `$049`. Block `$1BA` appears nowhere else in that map.
  - **Fix:** the collision check (`$00:B797`) treats that cell as a wall in map `$4D`. Graphics are unchanged.

## v0.2.1-beta — 2026-10-11

- Battle: poisoned/paralyzed characters show "Poison" / "Numb" instead of garbled text; no leftover letters
  when the name comes back.
- Status screen: "Numb" translated; Healthy / Poison / Numb and the names fully overwrite each other.
- "Holy Stone" everywhere (some lines said "Holy Rock"); Gupta's full name is "Armalik Gupta", as in the manual.

## v0.2-beta — 2026-10-10

- Books and item texts read from the menu translated (Atlas, Pyramid Book, talisman and pentacle books,
  Nauthiz temple trials).
- Full enemy and enemy-attack names (no more abbreviations like "Hunchbk").
- Ron is now Long (Stephen Long, as in the anime).

## v0.1-beta — 2026-10-10

- First public beta: full script, menus, battle text, names, graphic text screens (intro, monologue,
  cutscene lines, game over).
