import logging
import random
import time

from logging.handlers import BufferingHandler
from typing import List

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from elevator import FLOOR_MAX_LIMIT, Elevator, Passenger

PASSENGERS_LIMIT = 10
TICK_IN_SEC = 2  # Tick duration in sec
manual_tick = False  # Enter to continue

logger_elevator = logging.getLogger("elevator")
logger_elevator.setLevel(logging.DEBUG)
buffering_handler = BufferingHandler(capacity=21)
logger_elevator.addHandler(buffering_handler)

log_messages = []

console = Console()


def make_layout() -> Layout:
    """Define the layout."""
    layout = Layout(name="root")

    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
    )
    layout["main"].split_row(
        Layout(name="elevator"),
        Layout(name="logs", ratio=2, minimum_size=60),
    )
    return layout


class Header:
    """Display header with clock."""

    def __rich__(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row(
            "[b]Elevator[/b] demo . [i]Press ctrl-c for exit.[/i]",
        )
        return Panel(grid, style="white on blue")


def render_elevator(
    elevator: Elevator, passengers: List[List[Passenger]]
) -> str:
    elevator_str = '+-----+\n'

    count_passengers_inside = len(elevator.passengers)
    if count_passengers_inside < 10:
        passengers_inside_str = f'_{count_passengers_inside}_'
    elif count_passengers_inside < 100:
        passengers_inside_str = f'_{count_passengers_inside}'
    else:
        passengers_inside_str = f'{count_passengers_inside}'
    for floor in range(FLOOR_MAX_LIMIT, 0, -1):
        if elevator.floor == floor:
            elevator_str_cur = f'|[b]|{passengers_inside_str}|[/b]|'
            elevator_pointer = ' <--Elevator'
        else:
            elevator_str_cur = '|     |'
            elevator_pointer = ''
        elevator_str += f"""\
{elevator_str_cur} {floor}f {len(passengers[floor])}p {elevator_pointer}
+-----+
"""
    return elevator_str


def render(
    layout, passengers: List[List[Passenger]], elevator: Elevator
) -> None:
    layout["elevator"].update(Panel(
        render_elevator(elevator, passengers),
        border_style="green"
    ))
    layout['logs'].update(get_log())


def passengers_tick(
    passengers: List[List[Passenger]], elevator: Elevator
) -> None:
    for floor in range(1, len(passengers)):
        for passenger in passengers[floor]:
            passenger.tick(elevator)


def passengers_tick_end(passengers: List[List[Passenger]]) -> None:
    for floor in range(1, len(passengers)):
        for passenger in list(passengers[floor]):
            if passenger.floor_current != floor:
                passengers[0].append(passenger)
                passengers[floor].remove(passenger)

    for passenger in list(passengers[0]):
        if not passenger.is_inside:
            passengers[passenger.floor_current].append(passenger)
            passengers[0].remove(passenger)


def get_log():
    for li in buffering_handler.buffer:
        if len(log_messages) > 21:
            log_messages.pop(0)
        log_messages.append(li.msg)
    buffering_handler.flush()
    return Panel("\n".join(log_messages))


def main():
    layout = make_layout()
    layout["header"].update(Header())

    elevator = Elevator()
    passengers: List[List[Passenger]] = []
    for _ in range(0, FLOOR_MAX_LIMIT+1):
        passengers.append([])
    for _ in range(PASSENGERS_LIMIT):
        rand_floor = random.randint(1, FLOOR_MAX_LIMIT)
        passengers[rand_floor].append(
            Passenger(floor=rand_floor)
        )

    with Live(layout, refresh_per_second=10, screen=True):
        time_start = time.time()
        render(layout, passengers, elevator)
        while True:
            try:
                time.sleep(0.1)
                if time.time() - time_start > TICK_IN_SEC:
                    time_start = time.time()

                    passengers_tick(passengers, elevator)
                    elevator.move(passengers)
                    passengers_tick_end(passengers)

                    render(layout, passengers, elevator)

                    if manual_tick:
                        input()
            except KeyboardInterrupt:
                break

    print("\n".join(log_messages))


if __name__ == '__main__':
    main()
