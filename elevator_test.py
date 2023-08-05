import pytest

from unittest import mock

from elevator import (
    FLOOR_MAX_LIMIT, Passenger, Elevator, StatusElevator,
    Direction,
    ElevatorMoveError, FloorError, ElevatorDoorsError, EnterElevatorError
)


FLOOR_VALIDATE_ARGS = ['floor', [-1, 0, FLOOR_MAX_LIMIT+1]]


@pytest.fixture
def passenger():
    return Passenger()


@pytest.fixture
def elevator():
    return Elevator()


class TestPassenger:
    """ Tests for Passenger class. """

    @pytest.mark.parametrize(
        'floor_current',
        [f for f in range(1, FLOOR_MAX_LIMIT+1)]
    )
    def test_generate_destination(self, passenger: Passenger, floor_current):
        passenger.floor_current = floor_current
        passenger.generate_destination()
        assert passenger.floor_current != passenger.floor_destination

    @pytest.mark.parametrize(*FLOOR_VALIDATE_ARGS)
    def test_floor_destination_validate(self, passenger: Passenger, floor):
        with pytest.raises(FloorError):
            passenger.floor_destination = floor

    @mock.patch('elevator.Elevator.add_floor_outside')
    def test_call_elevator(
        self, mock_add_floor_outside, passenger: Passenger, elevator: Elevator
    ):
        passenger.call_elevator(elevator)
        mock_add_floor_outside.assert_called_once_with(passenger.floor_current)

    @mock.patch('elevator.Passenger.generate_destination')
    def test_leave_elevator(
        self, mock_generate_destination, passenger: Passenger,
        elevator: Elevator
    ):
        passenger.leave_elevator(elevator)
        assert passenger.floor_current == elevator.floor
        mock_generate_destination.assert_called_once()


class TestElevator:
    """ Tests for Elevator class. """

    @pytest.mark.parametrize(*FLOOR_VALIDATE_ARGS)
    def test_floor_validate(self, elevator: Elevator, floor):
        with pytest.raises(FloorError):
            elevator.floor = floor

    @mock.patch('elevator.Elevator._validate_floor')
    def test_add_floor_inside(self, mock_validate_floor, elevator: Elevator):
        new_floor = 1
        elevator.add_floor_inside(new_floor)
        mock_validate_floor.assert_called_once_with(new_floor)
        assert new_floor in elevator.get_floors_queue()

    @mock.patch('elevator.Elevator._validate_floor')
    def test_add_floor_outside(self, mock_validate_floor, elevator: Elevator):
        new_floor = 1
        elevator.add_floor_outside(new_floor)
        mock_validate_floor.assert_called_once_with(new_floor)
        assert new_floor in elevator.get_floors_queue()

    def test_change_direction(self, elevator: Elevator):
        start_direction = elevator.direction
        elevator.change_direction()
        assert start_direction != elevator.direction

    def test_move_no_floors_queue(self, elevator: Elevator):
        elevator.status = StatusElevator.open
        floor_start = elevator.floor
        elevator.move()
        assert floor_start == elevator.floor

    def test_move_invalid_status(self, elevator: Elevator):
        elevator.add_floor_inside(2)
        elevator.status = StatusElevator.open
        with pytest.raises(ElevatorMoveError):
            elevator.move()

    def test_move_floors_change(self, elevator: Elevator):
        elevator.add_floor_inside(2)
        elevator.floor = 1
        elevator.direction = Direction.up
        elevator.move()
        assert elevator.floor == 2
        elevator.add_floor_inside(1)
        elevator.direction = Direction.down
        elevator.move()
        assert elevator.floor == 1

    @pytest.mark.parametrize(
        'floor_start, floor_end, direction_start, direction_end',
        [
            (1, 2, Direction.down, Direction.up),
            (FLOOR_MAX_LIMIT, 1, Direction.up, Direction.down)
        ]
    )
    def test_move_direction_change_limits(
        self, elevator: Elevator, floor_start, floor_end,
        direction_start, direction_end
    ):
        elevator.floor = floor_start
        elevator.direction = direction_start
        elevator.add_floor_inside(floor_end)
        elevator.move()
        assert elevator.floor == floor_start
        assert elevator.direction == direction_end

    @pytest.mark.parametrize(
        'floor_destination, is_called', [(2, True), (3, False)]
    )
    @mock.patch('elevator.Elevator.open_doors')
    @mock.patch('elevator.Elevator.close_doors')
    def test_move_doors(
        self, mock_open_doors, mock_close_doors, elevator: Elevator,
        floor_destination, is_called
    ):
        elevator.floor = 1
        elevator.direction = Direction.up
        elevator.add_floor_inside(floor_destination)
        elevator.move()
        if is_called:
            mock_open_doors.assert_called_once()
            mock_close_doors.assert_called_once()
        else:
            assert not mock_open_doors.called
            assert not mock_close_doors.called

    def test_move_passengers_leave(
        self, elevator: Elevator, passenger: Passenger
    ):
        elevator.floor = 1
        elevator.direction = Direction.up
        elevator.add_floor_inside(2)
        elevator.passengers.add(passenger)
        passenger.floor_destination = 2
        assert passenger in elevator.passengers
        elevator.move()
        assert passenger not in elevator.passengers

    @pytest.mark.parametrize(
        'start_direction, end_direction',
        [(Direction.up, Direction.down), (Direction.down, Direction.up)]
    )
    def test_move_direction_change(
        self, elevator: Elevator, start_direction, end_direction
    ):
        elevator.floor = 2
        elevator.direction = start_direction
        elevator.add_floor_inside(1)
        elevator.add_floor_inside(3)
        elevator.move()
        # No more floors upstairs. Change direction
        assert elevator.direction == end_direction

    @pytest.mark.parametrize(
        'wrong_status', [s for s in StatusElevator if s != StatusElevator.idle]
    )
    def test_open_doors_errors(self, elevator: Elevator, wrong_status):
        with pytest.raises(ElevatorDoorsError):
            elevator.status = wrong_status
            elevator.open_doors()

    def test_open_doors_success(self, elevator: Elevator):
        elevator.status = StatusElevator.idle
        elevator.open_doors()
        assert elevator.status == StatusElevator.open

    @pytest.mark.parametrize(
        'wrong_status', [s for s in StatusElevator if s != StatusElevator.open]
    )
    def test_close_doors_errors(self, elevator: Elevator, wrong_status):
        with pytest.raises(ElevatorDoorsError):
            elevator.status = wrong_status
            elevator.close_doors()

    def test_close_doors_success(self, elevator: Elevator):
        elevator.status = StatusElevator.open
        elevator.close_doors()
        assert elevator.status == StatusElevator.idle

    @pytest.mark.parametrize(
        'wrong_status', [s for s in StatusElevator if s != StatusElevator.open]
    )
    def test_add_passenger_wrong_status(
        self, elevator: Elevator, passenger: Passenger, wrong_status
    ):
        with pytest.raises(EnterElevatorError):
            elevator.status = wrong_status
            elevator.add_passenger(passenger)

    def test_add_passenger_already_inside(
        self, elevator: Elevator, passenger: Passenger
    ):
        with pytest.raises(EnterElevatorError):
            elevator.status = StatusElevator.open
            elevator.passengers.add(passenger)
            elevator.add_passenger(passenger)

    def test_add_passenger_success(
        self, elevator: Elevator, passenger: Passenger
    ):
        elevator.status = StatusElevator.open
        elevator.add_passenger(passenger)
        assert passenger in elevator.passengers

    @pytest.mark.parametrize(
        'wrong_status', [s for s in StatusElevator if s != StatusElevator.open]
    )
    def test_remove_passenger_wrong_status(
        self, elevator: Elevator, passenger: Passenger, wrong_status
    ):
        with pytest.raises(EnterElevatorError):
            elevator.status = wrong_status
            elevator.remove_passenger(passenger)

    def test_remove_passenger_not_inside(
        self, elevator: Elevator, passenger: Passenger
    ):
        with pytest.raises(EnterElevatorError):
            elevator.status = StatusElevator.open
            elevator.remove_passenger(passenger)

    def test_remove_passenger_success(
        self, elevator: Elevator, passenger: Passenger
    ):
        elevator.status = StatusElevator.open
        elevator.add_passenger(passenger)
        elevator.remove_passenger(passenger)
        assert passenger not in elevator.passengers
