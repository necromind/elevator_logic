import enum
import logging
import random

from typing import List, Optional

logger = logging.getLogger(__name__)
FLOOR_MAX_LIMIT = 10
ELEVATOR_CAPACITY = 5


class FloorError(Exception):
    """ Raised when floor number is not correct. """
    pass


class EnterElevatorError(Exception):
    """ Raised in incorrect elevator entering. """
    pass


class ElevatorMoveError(Exception):
    """ Raised while elevator moving action. """
    pass


class ElevatorDoorsError(Exception):
    """ Raised with elevator's doors errors. """
    pass


class StatusElevator(enum.Enum):
    idle = 0
    moving = 1
    open = 2


class Direction(enum.Enum):
    up = 0
    down = 1


class FloorValidatorMixin:
    def _validate_floor(self, floor: int, allow_zero: bool = False) -> None:
        if not allow_zero and floor < 1:
            raise FloorError('The floor cannot be less than 1.')
        if floor > FLOOR_MAX_LIMIT:
            raise FloorError(
                f'The floor cannot be more than {FLOOR_MAX_LIMIT}.')


class Passenger(FloorValidatorMixin):
    id: int
    __floor_current: int
    __floor_destination: int
    elevator_called: bool = False
    is_inside: bool = False

    def __init__(self, floor: Optional[int] = None, id: Optional[int] = None) -> None:
        if id:
            self.floor_current = id
        else:
            self.floor_current = random.randint(1, FLOOR_MAX_LIMIT)
        if not id:
            self.id = random.randint(1, 1000)
        else:
            self.id = id
        self.generate_destination()

    def __str__(self) -> str:
        return f'Passenger {self.id}'

    def generate_destination(self) -> None:
        self.floor_destination = self.floor_current
        while self.floor_destination == self.floor_current:
            self.floor_destination = random.randint(1, FLOOR_MAX_LIMIT)

    @property
    def floor_current(self) -> int:
        return self.__floor_current

    @floor_current.setter
    def floor_current(self, floor: int) -> None:
        self._validate_floor(floor, allow_zero=True)
        self.__floor_current = floor

    @property
    def floor_destination(self) -> int:
        return self.__floor_destination

    @floor_destination.setter
    def floor_destination(self, floor: int) -> None:
        self._validate_floor(floor)
        self.__floor_destination = floor

    def call_elevator(self, elevator: 'Elevator') -> None:
        elevator.add_floor_outside(self.__floor_current)
        self.elevator_called = True

    def enter_elevator(self, elevator: 'Elevator') -> None:
        elevator.add_floor_outside(self.__floor_destination)
        self.is_inside = True
        self.elevator_called = False
        self.floor_current = 0

    def leave_elevator(self, elevator: 'Elevator') -> None:
        self.floor_current = elevator.floor
        self.is_inside = False
        self.generate_destination()

    def tick(self, elevator: 'Elevator') -> None:
        if not self.is_inside and not self.elevator_called:
            self.call_elevator(elevator)


class Elevator(FloorValidatorMixin):
    status: StatusElevator
    direction: Direction
    __floor: int
    __floors_queue: set[int]
    passengers: set[Passenger]

    def __init__(self) -> None:
        self.status = StatusElevator.idle
        self.direction = Direction.up
        self.__floor = 1
        self.__floors_queue = set()
        self.passengers = set()
        logger.debug(f'Elevator created. {random.randint(0, 100)}')

    @property
    def floor(self) -> int:
        return self.__floor

    @floor.setter
    def floor(self, floor: int) -> None:
        self._validate_floor(floor)
        self.__floor = floor

    def get_floors_queue(self):
        return self.__floors_queue

    def add_floor_inside(self, floor: int) -> None:
        """ Add floor to the floors queue from inside the elevator. """
        self._validate_floor(floor)
        self.__floors_queue.add(floor)

    def add_floor_outside(self, floor: int) -> None:
        """ Add floor to the floors queue from outside the elevator. """
        self._validate_floor(floor)
        self.__floors_queue.add(floor)

    def change_direction(self):
        if self.direction == Direction.up:
            self.direction = Direction.down
        else:
            self.direction = Direction.up

    def move(
        self, all_passengers: Optional[List[List[Passenger]]] = None
    ) -> None:
        """ Move the elevator by one floor. """
        if len(self.__floors_queue) == 0:
            return
        if self.status == StatusElevator.open:
            raise ElevatorMoveError('Doors open. Elevator cannot move.')

        logger.debug(
            f'Elevator starts moving. Current floor: {self.floor}. '
            f'Direction: {self.direction.name}.'
        )
        self.status = StatusElevator.moving
        try:
            if self.direction == Direction.up:
                self.floor += 1
            else:
                self.floor -= 1

            self.status = StatusElevator.idle

            if self.floor in self.__floors_queue:
                self.open_doors()
                if all_passengers:
                    for passenger in all_passengers[self.floor]:
                        self.add_passenger(passenger)
                for passenger in self.passengers.copy():
                    if passenger.floor_destination == self.floor:
                        self.remove_passenger(passenger)
                self.close_doors()
                self.__floors_queue.remove(self.floor)
        except FloorError:
            """ Top or down floor limits. """
            self.status = StatusElevator.idle
            logger.debug('Elevator moving. Floor limit reached.')

        if self.floor == 1:
            self.direction = Direction.up
        elif self.floor == FLOOR_MAX_LIMIT:
            self.direction = Direction.down
        else:
            # Check if no more floors in the direction and change direction
            need_change = True
            for floor in self.__floors_queue:
                if self.direction == Direction.up:
                    if floor > self.floor:
                        need_change = False
                        break
                else:
                    if floor < self.floor:
                        need_change = False
                        break

            if need_change:
                self.change_direction()

        logger.debug(
            f'Elevator finished moving. Current floor: {self.floor}. '
            f'Direction: {self.direction.name}.'
        )

    def open_doors(self):
        if self.status != StatusElevator.idle:
            raise ElevatorDoorsError(
                'Cannot open doors. Elevator is not in idle status.')
        self.status = StatusElevator.open
        logger.debug('Elevator doors opened.')

    def close_doors(self):
        if self.status != StatusElevator.open:
            raise ElevatorDoorsError(
                'Cannot close doors. Doors are not opened.')
        self.status = StatusElevator.idle
        logger.debug('Elevator doors closed.')

    def add_passenger(self, passenger: Passenger) -> None:
        if self.status != StatusElevator.open:
            raise EnterElevatorError('Doors closed. Passenger cannot enter.')
        if passenger in self.passengers:
            raise EnterElevatorError('Passenger already in elevator.')
        self.passengers.add(passenger)
        passenger.enter_elevator(self)
        logger.debug(f'{passenger} entered elevator.')

    def remove_passenger(self, passenger: Passenger) -> None:
        if self.status != StatusElevator.open:
            raise EnterElevatorError('Doors closed. Passenger cannot remove.')
        if passenger not in self.passengers:
            raise EnterElevatorError('Passenger not in elevator.')
        self.passengers.remove(passenger)
        passenger.leave_elevator(self)
        logger.debug(f'{passenger} leaved elevator.')
