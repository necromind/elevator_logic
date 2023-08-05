# Elevator logic

```
python3 -m venv .venv
source ./.venv/bin/activate
python -m pip install -r requirements.txt
```

Run tests:
```
pytest
```

- elevator.py - all logic classes in one file
- elevator_test.py - tests
- main.py - gui demo

Logic:
- Passengers arrive randomly at different floors and press the elevator button.
- Passengers enter the queue of the Elevator's called floors.
- Passengers can enter the Elevator only if it's on their current floor and if it's not full.
- The elevator moves from floor to floor and stops whenever needed to let Passengers in or out.


![Demo](https://raw.githubusercontent.com/necromind/elevator_logic/main/elevator_demo.gif)
