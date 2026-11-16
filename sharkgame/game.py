"""Core rules for a small original grow-and-eat game.

The shark swims in one of three lanes. Creatures scroll toward it from the
right. Smaller prey is eaten for XP, mines hurt, and boosts double XP for a
while. Every ``XP_PER_LEVEL * level`` XP the shark grows one size and gains
max health. The whole simulation is deterministic for a given seed, which
keeps it testable.

No external dependencies; Python 3.10+.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

LANES = 3
WIDTH = 30
SHARK_X = 4
MAX_TICKS = 600

XP_PER_LEVEL = 20          # level n needs XP_PER_LEVEL * n total XP to advance
MINE_DAMAGE = 25
BOOST_TICKS = 40
SPAWN_CHANCE = 0.35

SHIELD_TICKS = 30
FRENZY_TICKS = 30
FRENZY_MULTIPLIER = 3
HEAL_AMOUNT = 40


class Kind(Enum):
    FISH = "fish"       # edible, size 1-3
    MINE = "mine"       # damages the shark on contact
    BOOST = "boost"     # temporarily doubles XP


class Card(Enum):
    """Single-use power-ups. Each card is removed from the hand when played."""

    SHIELD = "shield"   # the next mine does no damage
    FRENZY = "frenzy"   # XP is multiplied for a while
    HEAL = "heal"       # restore HP


@dataclass
class Creature:
    kind: Kind
    lane: int
    x: int
    size: int = 1


@dataclass
class Shark:
    lane: int = 1
    level: int = 1
    xp: int = 0
    max_hp: int = 100
    hp: int = 100
    boost_ticks: int = 0

    @property
    def size(self) -> int:
        return self.level


@dataclass
class Game:
    seed: int = 0
    tick_count: int = 0
    score: int = 0
    shark: Shark = field(default_factory=Shark)
    creatures: list[Creature] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    hand: list[Card] = field(default_factory=list)
    shield_ticks: int = 0
    frenzy_ticks: int = 0

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        self._draw_card()  # one starting card

    def _draw_card(self) -> None:
        card = self._rng.choice(list(Card))
        self.hand.append(card)
        self.events.append(f"Drew a {card.value} card.")

    def play_card(self, index: int = 0) -> str:
        """Use one card from the hand. It is consumed and cannot be used again."""
        if not self.hand:
            return "No cards in hand."
        if index < 0 or index >= len(self.hand):
            raise IndexError(f"no card at position {index}")
        card = self.hand.pop(index)
        if card is Card.SHIELD:
            self.shield_ticks = SHIELD_TICKS
            msg = f"Shield up for {SHIELD_TICKS} ticks."
        elif card is Card.FRENZY:
            self.frenzy_ticks = FRENZY_TICKS
            msg = f"Frenzy! XP x{FRENZY_MULTIPLIER} for {FRENZY_TICKS} ticks."
        else:
            self.shark.hp = min(self.shark.max_hp, self.shark.hp + HEAL_AMOUNT)
            msg = f"Healed {HEAL_AMOUNT} HP."
        self.events.append(f"Played {card.value}: {msg}")
        return msg

    # ----- state queries -------------------------------------------------

    @property
    def over(self) -> bool:
        return self.shark.hp <= 0 or self.tick_count >= MAX_TICKS

    def xp_needed(self) -> int:
        """XP required to advance from the current level (XP resets on level-up)."""
        return XP_PER_LEVEL * self.shark.level

    # ----- simulation ----------------------------------------------------

    def step(self, action: str = "stay") -> list[str]:
        """Advance one tick. ``action`` is ``"up"``, ``"down"`` or ``"stay"``."""
        if self.over:
            return []
        self.events = []
        self.tick_count += 1

        self._move_shark(action)
        self._scroll_and_spawn()
        self._resolve_collisions()
        self._tick_boost()
        return list(self.events)

    def _move_shark(self, action: str) -> None:
        if action == "up":
            self.shark.lane = max(0, self.shark.lane - 1)
        elif action == "down":
            self.shark.lane = min(LANES - 1, self.shark.lane + 1)
        elif action != "stay":
            raise ValueError(f"unknown action: {action!r}")

    def _scroll_and_spawn(self) -> None:
        for c in self.creatures:
            c.x -= 1
        self.creatures = [c for c in self.creatures if c.x >= 0]

        if self._rng.random() < SPAWN_CHANCE:
            kind = self._rng.choices(
                [Kind.FISH, Kind.MINE, Kind.BOOST], weights=[6, 2, 1]
            )[0]
            size = self._rng.randint(1, 3) if kind is Kind.FISH else 1
            self.creatures.append(
                Creature(kind, self._rng.randrange(LANES), WIDTH - 1, size)
            )

    def _resolve_collisions(self) -> None:
        remaining: list[Creature] = []
        for c in self.creatures:
            if c.lane != self.shark.lane or c.x != SHARK_X:
                remaining.append(c)
                continue
            self._collide(c)
        self.creatures = remaining

    def _collide(self, c: Creature) -> None:
        if c.kind is Kind.BOOST:
            self.shark.boost_ticks = BOOST_TICKS
            self.events.append("Boost! XP doubled for a while.")
        elif c.kind is Kind.MINE:
            if self.shield_ticks:
                self.shield_ticks = 0
                self.events.append("Shield blocked a mine.")
            else:
                self.shark.hp = max(0, self.shark.hp - MINE_DAMAGE)
                self.events.append(f"Hit a mine! -{MINE_DAMAGE} HP.")
        elif c.size <= self.shark.size:
            multiplier = 1
            if self.shark.boost_ticks:
                multiplier *= 2
            if self.frenzy_ticks:
                multiplier *= FRENZY_MULTIPLIER
            gain = c.size * 10 * multiplier
            self.shark.xp += gain
            self.score += gain
            self.events.append(f"Ate a size-{c.size} fish (+{gain} XP).")
            self._check_level_up()
        else:
            self.events.append("Fish too big to eat; it got away.")

    def _check_level_up(self) -> None:
        needed = self.xp_needed()
        if self.shark.xp >= needed:
            self.shark.xp -= needed
            self.shark.level += 1
            self.shark.max_hp += 10
            self.shark.hp = min(self.shark.max_hp, self.shark.hp + 20)
            self.events.append(f"Grew to level {self.shark.level}!")
            self._draw_card()

    def _tick_boost(self) -> None:
        if self.shark.boost_ticks:
            self.shark.boost_ticks -= 1
        if self.frenzy_ticks:
            self.frenzy_ticks -= 1


# ----- rendering ---------------------------------------------------------

_SYMBOL = {Kind.FISH: "f", Kind.MINE: "*", Kind.BOOST: "+"}


def render(game: Game) -> str:
    """Return a text picture of the lanes and the shark's status."""
    rows = []
    for lane in range(LANES):
        cells = ["." for _ in range(WIDTH)]
        for c in game.creatures:
            if c.lane == lane:
                cells[c.x] = _SYMBOL[c.kind] if c.kind is not Kind.FISH else str(c.size)
        if lane == game.shark.lane:
            cells[SHARK_X] = "S"
        rows.append("".join(cells))
    s = game.shark
    status = (
        f"tick {game.tick_count}/{MAX_TICKS}  level {s.level}  "
        f"xp {s.xp}/{game.xp_needed()}  hp {s.hp}/{s.max_hp}  "
        f"score {game.score}"
    )
    if s.boost_ticks:
        status += f"  [boost {s.boost_ticks}]"
    if game.frenzy_ticks:
        status += f"  [frenzy {game.frenzy_ticks}]"
    if game.shield_ticks:
        status += f"  [shield {game.shield_ticks}]"
    hand = ", ".join(c.value for c in game.hand) or "empty"
    status += f"\nhand: {hand}"
    return "\n".join(rows) + "\n" + status
