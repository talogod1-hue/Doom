# Shark Game (original prototype)

A small terminal grow-and-eat game written from scratch, inspired by the
genre. It uses its own rules, names, and art (plain text). It is not affiliated
with, and does not reuse any assets or data from, any commercial game.

## Rules

- The shark swims in one of three lanes and can move up or down.
- Fish scroll in from the right. Fish up to your size are eaten for XP
  (size × 10). Bigger fish get away.
- Mines (`*`) cost 25 HP. Boosts (`+`) double XP for 40 ticks.
- Every `20 × level` XP you grow one level: +10 max HP, +20 HP healed, and one new card.
- Cards are single use. You start with one. Press `p` to play the first card in
  your hand: **Shield** blocks the next mine, **Frenzy** triples XP for 30 ticks,
  **Heal** restores 40 HP.
- The run ends when HP hits 0 or after 600 ticks. Score is total XP gained.

## Run it

```bash
python3 -m sharkgame                  # keys: u = up, d = down, enter = stay, q = quit
python3 -m sharkgame --auto --seed 3  # watch the built-in autopilot
```

## Test

```bash
python3 -m unittest tests.test_sharkgame -v
```

## Layout

| File | Role |
|------|------|
| `game.py` | Deterministic rules and text rendering (no I/O) |
| `__main__.py` | Terminal loop and autopilot |
