"""Play the shark game in the terminal.

    python3 -m sharkgame                 # interactive: u = up, d = down, enter = stay
    python3 -m sharkgame --auto --seed 3 # watch the built-in autopilot play
"""

from __future__ import annotations

import argparse
import sys

from .game import Game, Kind, LANES, SHARK_X, render


def autopilot(game: Game) -> str:
    """Pick the lane that has the nearest safe-to-eat fish and avoids mines."""
    s = game.shark
    best_lane, best_score = s.lane, float("-inf")
    for lane in range(LANES):
        score = 0.0
        for c in game.creatures:
            if c.lane != lane or c.x < SHARK_X:
                continue
            dist = c.x - SHARK_X
            if c.kind is Kind.MINE:
                score -= 10 / (dist + 1)
            elif c.kind is Kind.BOOST:
                score += 4 / (dist + 1)
            elif c.size <= s.size:
                score += 6 / (dist + 1)
        score -= 0.5 * abs(lane - s.lane)  # small preference for staying put
        if score > best_score:
            best_lane, best_score = lane, score
    if best_lane < s.lane:
        return "up"
    if best_lane > s.lane:
        return "down"
    return "stay"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Terminal grow-and-eat game.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--auto", action="store_true", help="let the autopilot play")
    args = parser.parse_args(argv)

    game = Game(seed=args.seed)
    print("Eat smaller fish (digits), dodge mines (*), grab boosts (+).")
    print("Keys: u = up, d = down, enter = stay, q = quit.\n")

    while not game.over:
        if args.auto:
            action = autopilot(game)
        else:
            try:
                key = input("> ").strip().lower()
            except EOFError:
                break
            if key == "q":
                break
            action = {"u": "up", "d": "down", "": "stay"}.get(key)
            if action is None:
                print("Unknown key. Use u, d, enter or q.")
                continue

        game.step(action)
        print(render(game))
        for event in game.events:
            print("  " + event)
        print()

    if game.shark.hp <= 0:
        print("Your shark was wrecked.")
    elif game.over:
        print("Time's up.")
    print(f"Final score: {game.score} (level {game.shark.level})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
