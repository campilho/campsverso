from collections import deque
from itertools import pairwise

from hypothesis import given
from hypothesis import strategies as st

from campsverso_cartridge_api import Position
from campsverso_kernel.space import corners, find_path

SIZE = 8


def _bfs(start: Position, goal: Position, walls: frozenset[Position]) -> int | None:
    seen = {start: 0}
    queue = deque([start])
    while queue:
        here = queue.popleft()
        if here == goal:
            return seen[here]
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            step = Position(here.x + dx, here.y + dy)
            if 0 <= step.x < SIZE and 0 <= step.y < SIZE and step not in walls and step not in seen:
                seen[step] = seen[here] + 1
                queue.append(step)
    return None


positions = st.builds(Position, st.integers(0, SIZE - 1), st.integers(0, SIZE - 1))


@given(st.frozensets(positions, max_size=20), positions, positions)
def test_caminho_e_valido_minimo_e_reprodutivel(
    walls: frozenset[Position], start: Position, goal: Position
) -> None:
    walls = walls - {start}

    def walkable(p: Position) -> bool:
        return 0 <= p.x < SIZE and 0 <= p.y < SIZE and p not in walls

    path = find_path(start, goal, walkable)
    expected = _bfs(start, goal, walls)
    if expected is None:
        assert path is None
        return
    assert path is not None
    assert path[0] == start
    assert path[-1] == goal
    assert len(path) - 1 == expected
    assert all(walkable(p) for p in path)
    assert all(a.chebyshev(b) == 1 and (a.x == b.x or a.y == b.y) for a, b in pairwise(path))
    assert find_path(start, goal, walkable) == path


def test_esquinas_do_trajeto() -> None:
    path = [Position(4, 6), Position(4, 7), Position(4, 8), Position(5, 8), Position(6, 8)]
    assert corners(path) == [Position(4, 8), Position(6, 8)]
    assert corners([Position(1, 1)]) == []
