*This project has been created as part of the 42 curriculum by elhamza.*

# Fly-in

## Description

Fly-in is a Python program that moves a fleet of drones through a network of
zones, from a start zone to an end zone, in the fewest possible simulation
turns.

## Instructions

The project uses a `Makefile` to run everything. All commands run from the
root of the project.

```bash
make install       # install the project dependencies
make run            # run the main program
make debug          # run the main program with the Python debugger (pdb)
make clean          # remove cache files (__pycache__, .mypy_cache, etc.)
make lint           # check the code with flake8 and mypy
make lint-strict    # check the code with flake8 and mypy --strict
```

To run the simulation on a specific map, edit the map path used in
`src/simulation.py`, or run a module directly, for example:

```bash
python3 -m src.simulation
```

Map files go in the `maps/` folder. Example edge-case maps used to test the
project are in `maps/edge_cases/`.

## Resources

### References used

- Python official documentation: [https://docs.python.org/3/](https://docs.python.org/3/)
- Dijkstra's algorithm — general explanations found through web searches
  ("dijkstra algorithm explained simply")

### How AI was used

AI was help to understand the algorithm Dijkstra

## Algorithm choices and implementation strategy

### Parsing

The parser reads the map file line by line, skips comments and blank
lines, and turns each line into a `Zone` or `Connection` object. All
validation happens during parsing: duplicate names, duplicate connections,
invalid zone types, bad coordinates, and missing `nb_drones` are all
caught early, with a clear error message that includes the line number.

### Pathfinding

Finding the best path for a drone uses **Dijkstra's algorithm**, because
movement costs are different per zone type (normal = 1, restricted = 2),
so a simple shortest-path search (like plain BFS) is not enough — Dijkstra
correctly accounts for these different costs. Blocked zones are never
explored at all.

To spread drones across different routes instead of forcing them all
through the same path, the project also uses a **depth-first search
(DFS)** to find several different valid paths between start and end, not
just the single cheapest one.

### Simulation and scheduling

The simulation moves all drones turn by turn. Every turn:
1. Drones that are finishing a restricted-zone movement arrive first.
2. For every other drone, the simulation checks its planned path and
   tries to move it to the next zone.
3. Before moving a drone, the simulation checks:
   - Is the next zone blocked?
   - Does the next zone have free capacity (`max_drones`)?
   - Does the connection have free capacity (`max_link_capacity`)?
4. If a drone's usual path is full or blocked this turn, the simulation
   looks for a different available path for that drone (an alternative
   route with less congestion) before making it wait.
5. Restricted-zone movement takes exactly two turns. The destination zone
   is reserved as soon as the drone starts moving, so the drone is
   guaranteed a place when it arrives, and it can never be forced to wait
   in the middle of the connection.

A safety limit (`max_turns`) stops the simulation with a clear error if a
map makes it impossible for a drone to ever reach the goal, instead of
running forever.

### Performance results

The project was tested against the maps and turn targets given in the
subject:

| Map | Drones | Target | Result |
|---|---|---|---|
| Linear path (easy) | 2 | ≤ 6 turns | 4 turns |
| Simple fork (easy) | 4 | ≤ 8 turns | 4 turns |
| Basic capacity (easy) | 4 | ≤ 6 turns | 4 turns |
| Dead end trap (medium) | 5 | ≤ 12 turns | 8 turns |
| Circular loop (medium) | 6 | ≤ 15 turns | 15 turns |
| Priority puzzle (medium) | 5 | ≤ 12 turns | 7 turns |
| Maze nightmare (hard) | 8 | ≤ 30 turns | 13 turns |
| Capacity hell (hard) | 12 | ≤ 35 turns | 16 turns |
| Ultimate challenge (hard) | 15 | ≤ 45 turns | 26 turns |
| The Impossible Dream (bonus) | 25 | reference: 45 turns | 44 turns |

All maps finish inside the target, and no zone or connection ever goes
over its allowed capacity during any run (this is checked automatically
by the simulation itself, and would stop the program immediately if it
ever happened).

## Visual representation

The project uses **colored terminal output** to make the simulation easier
to follow:
- Each zone is printed using the color given in the map file
  (for example, a zone with `color=red` prints in red text).
- If a map uses a color the terminal does not support, the zone name is
  printed in the normal color instead. The program never crashes because
  of an unusual color name.
- Every turn, the simulation only prints zones that currently contain at
  least one drone, instead of printing the whole map every time. This
  keeps the output readable, even on large maps with many zones.
- Drones that are delivered are clearly marked as `DELIVERED`.
- Drones that are flying through a restricted zone are clearly marked as
  `IN TRANSIT`, together with the name of the connection they are on.

This helps a person watching the simulation quickly see where the drones
are, which zones are busy, and which drones have already finished,
without having to read every single turn line by line.

## Project structure

```
fly-in/
├── main.py
├── Makefile
├── requirements.txt
├── maps/
│   ├── easy/
│   ├── medium/
│   ├── hard/
│   ├── challenger/
└── src/
    ├── zone.py
    ├── connection.py
    ├── network.py
    ├── drone.py
    ├── parser.py
    ├── pathfinding.py
    └── simulation.py
```