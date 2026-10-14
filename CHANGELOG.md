# Changelog

All notable changes to the English translation patch. Versions match the GitHub Releases.

## v0.2.2-beta — 2026-10-15

### Translation
- Kunlun: the answers to the Five Kaiyan Generals now use the same words as the Pyramid Book
  (Flesh / Body Heat / Breath / Blood / Organs), and their window is wider so "Body Heat" fits.
- Airport: full country names ("Hong Kong" instead of "HongKong"); destination window widened.
- "Attack who?" / "Use it on who?".
- About 100 messages reflowed: sentences that were broken mid-line now use fewer lines when they fit
  (the wording itself is unchanged).

### Bug fixes
- **Hole in the wall of the Treasury labyrinth (Olympia, Greece) — a bug of the translation patch itself.**
  In the labyrinth behind the locked door on the Treasury's B1, on the screen below the chest with the Book of
  Almadel, the wall just below the path showed a few odd tiles and could be walked through. From there the party
  could walk into the empty area around the candles, and walking into the screen on the right left the party
  stuck at the screen edge. This does **not** happen in the original Japanese game.
  - **Affected versions:** v0.1-beta to v0.2.1-beta.
  - **How to reproduce (with those versions):** in the Treasury labyrinth, go to the screen just below the Book of
    Almadel chest and walk down from the left end of the path (the first cells of the wall below it): you leave the
    path. Walk right into the next screen and the party gets stuck.
  - **Cause:** the patch kept three of its own variables (font upload timer, font segment index, last graphics
    file loaded) at WRAM `$7F:FF00-FF05`. The game uses `$7F:8000-FFFF` for the dungeon map, so in maps large
    enough to reach that area three map cells were overwritten (here, three cells of the corridor's bottom wall).
  - **Fix:** the variables moved to unused WRAM (`$7E:E800-E805`). The map is no longer touched.
  - If you load a save state made inside that labyrinth with an older version, leave the labyrinth and come back
    so the map is reloaded.

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
