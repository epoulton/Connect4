import random

from . import _game


class Agent:
    """
    The base Agent class is defined below to establish the public API that must be implemented by any agent to be
    compatible with the Game.play() method. The Agent.select_action() method will be called with a StateView as
    argument, and it must return a single action (documented below). The Agent.notify_outcome() method will be called
    with an Outcome as argument at the conclusion of the Game.play() method.

    """

    def __init__(self, token):
        self.token = token

    def select_action(self, state_view):
        raise NotImplementedError

    def notify_outcome(self, outcome):
        raise NotImplementedError


class CLIAgent(Agent):
    """
    An inherited Agent class meant to provide user interaction with the game at the command line.

    """

    def select_action(self, state_view):
        self._print_board(state_view)

        while True:
            column = input(' '.join([str(self.token), 'to play.']))

            try:
                column = int(column)
            except ValueError:
                print('Input could not be converted to an integer.')
                continue

            if column < 1 or column > state_view.board_size[1]:
                print('Selected column lies outside the board. Columns are indexed from 1.')
                continue

            break

        return _game.Action(_game.Actions.PLACE, column)

    def notify_outcome(self, outcome):
        print(outcome.agent_outcomes[self])

    @staticmethod
    def _print_board(view):
        for row in range(view.board_size[0]):
            print(''.join([
                '[',
                ','.join([
                    ' ' if token is None else str(token)[0]
                    for token in view.board[row * view.board_size[1]: (row + 1) * view.board_size[1]]
                ]),
                ']']))


class RandomAgent(Agent):
    """
    An inherited Agent class implementing an AI that places tokens randomly in the open columns.

    """

    def select_action(self, state_view):
        open_columns = [
            index + 1
            for index, token in zip(range(state_view.board_size[1]), state_view.board[:state_view.board_size[1]])
            if token is None
        ]
        return _game.Action(_game.Actions.PLACE, random.choice(open_columns))

    def notify_outcome(self, outcome):
        pass
