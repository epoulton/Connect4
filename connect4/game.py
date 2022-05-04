import bidict
import enum
import itertools
import random

from . import agents as agents_module


class Game:
    """
    The Game class acts as the game manager or referee and mediates all interactions between an agent and the game
    state. Agents must be created prior to creating a game and passed as arguments to the Game constructor. The
    Game.play() method will begin the interaction between agents and state, and it will resolve by calling the
    Agent.notify_outcome() method on each agent.

    """

    def __init__(self, agents, board_size=(6, 7)):
        # User-called method. Validate arguments.
        if not (isinstance(agents, list) or isinstance(agents, tuple)):
            raise TypeError('Unsupported type for argument "agents". Argument must be of type "List" or "Tuple".')
        if len(agents) < 2:
            raise ValueError('Argument "agents" must be of at least length 2.')
        for element in agents:
            if not isinstance(element, agents_module.Agent):
                raise TypeError('Unsupported element type in argument "agents". Elements must be of type "Agent".')
        if not (isinstance(board_size, list) or isinstance(board_size, tuple)):
            raise TypeError('Unsupported type for argument "board_size". Argument must be of type "List" or "Tuple".')
        if not len(board_size) == 2:
            raise ValueError('Argument "board_size" must be of length 2.')
        for element in board_size:
            if not isinstance(element, int):
                raise TypeError('Unsupported element type in argument "board_size". Elements must be of type "int".')
            if element < 1:
                raise ValueError('Elements in argument "board_size" must be strictly positive (>0).')

        self._agents = agents
        self._board_size = board_size

    def play(self):
        # Setup agent cycle, state, and outcome in advance.
        agents = itertools.cycle(random.sample(self._agents, len(self._agents)))
        state = State([agent.token for agent in self._agents], board_size=self._board_size)
        outcome = Outcome(self._agents)

        while True:
            current_agent = next(agents)
            action = current_agent.select_action(state.expose_view())

            # Never trust an agent to play by the rules. Check for universally invalid actions (independent of state).
            if action.action is not Actions.PLACE:
                raise ValueError('In Connect4, only the PLACE action is permitted.')
            if not isinstance(action.place_column, int):
                raise TypeError(
                    'Unsupported return type from method Agent.select_action(). Return must be of type "int".'
                )
            if action.place_column < 1 or action.place_column > self._board_size[1]:
                raise ValueError(
                    f'Returned value from Agent.select_action() must lie within the closed interval [0, '
                    f'{self._board_size[1]}].'
                )

            # In the single action game, this is fine. In a multi-action game, this will need to be more generic.
            # Any specific invalid actions (dependent on state) will be caught by the state.
            state.place_token(action.place_column, current_agent.token)
            outcome.append_to_record(current_agent.token, action)
            result = state.check_for_outcome()

            if result[0] is Outcomes.WIN:
                for agent in outcome.agent_outcomes:
                    outcome.agent_outcomes[agent] = Outcomes.WIN if agent.token is result[1] else Outcomes.LOSE

                break

            elif result[0] is Outcomes.DRAW:
                for agent in outcome.agent_outcomes:
                    outcome.agent_outcomes[agent] = Outcomes.DRAW

                break

        for agent in self._agents:
            agent.notify_outcome(outcome)


class State:
    """
    The State class tracks the state of the game board. The base State class will typically only be instantiated by the
    Game.play() method, and this instance will never be exposed directly to an agent. To expose the state to an agent,
    the State.expose_view() method will be called, and it will return a StateView object as documented below. Agents are
    free to implement inherited State classes for the purpose of exploring/evaluating actions.

    """

    def __init__(self, external_tokens, board_size):
        self._token_map = bidict.bidict(
            {token: value for token, value in zip(external_tokens, range(len(external_tokens)))}
        )
        self._n_rows, self._n_columns = board_size

        self._board = [None] * self._n_rows * self._n_columns

    def expose_view(self):
        # Must expose the view as defined by the StateView class.
        return StateView(
            (self._n_rows, self._n_columns),
            [token if token is None else self._token_map.inverse[token] for token in self._board]
        )

    def place_token(self, column, token):
        lowest_open_cell_in_column = None

        for row in range(self._n_rows):
            if self._board[row * self._n_columns + column - 1] is not None:
                break
            else:
                lowest_open_cell_in_column = row

        # If the column is full, that is a state dependent invalid action.
        if lowest_open_cell_in_column is None:
            raise ActionError(f'Cannot place a token in column {column}. Column is full. Columns are indexed from 1.')
        else:
            self._board[lowest_open_cell_in_column * self._n_columns + column - 1] = self._token_map[token]

    def check_for_outcome(self):
        # If the game has been won, returns the tuple (Outcomes.WIN, winning_token).
        # If the game is a draw, returns the tuple (Outcomes.DRAW, None).
        # If the game is unfinished, returns None.
        outcome = None
        winning_token = None

        for line in self._generate_lines():
            if line[0] is not None and len(set(line)) == 1:
                outcome = Outcomes.WIN
                winning_token = self._token_map.inverse[line[0]]
                break

        if outcome is None and None not in self._board:
            outcome = Outcomes.DRAW

        return outcome, winning_token

    def _generate_lines(self):
        # Horizontal lines: --
        for row in range(self._n_rows):
            for column in range(self._n_columns - 3):
                yield self._board[row * self._n_columns + column: row * self._n_columns + column + 4]

        # Vertical lines: |
        for row in range(self._n_rows - 3):
            for column in range(self._n_columns):
                yield self._board[
                      row * self._n_columns + column: (row + 4) * self._n_columns + column: self._n_columns
                      ]

        # Diagonal lines: \
        for row in range(self._n_rows - 3):
            for column in range(self._n_columns - 3):
                yield self._board[
                      row * self._n_columns + column: (row + 4) * self._n_columns + column + 4: self._n_columns + 1
                      ]

        # Diagonal lines: /
        for row in range(self._n_rows - 3):
            for column in range(3, self._n_columns):
                yield self._board[
                      row * self._n_columns + column: (row + 4) * self._n_columns + column - 4: self._n_columns - 1
                      ]


class StateView:
    """
    StateView is a data-only class meant to act as an interface between State and Agent objects.
    A StateView has two fields:
        board_size: A 2-tuple of ints specifying the number of rows and columns in the board, in that order.
        board: A flat list of tokens representing the tokens in each cell of the board. Cells are ordered row-by-row,
               beginning at the upper left cell and ending at the lower right cell. Tokens are passed by reference to
               the original tokens given as arguments to the Game constructor. Empty cells are represented by None.

    """

    def __init__(self, board_size, board):
        self.board_size = board_size
        self.board = board


class Action:
    """
    Action is a data-only class meant to act as an interface between Agent and Game objects.
    An Action has two fields:
        action: An Actions object representing the desired action (a bit superfluous in a single action game, but useful
                in games with more complex action spaces).
        column: An int representing the desired column in which to place the agent's token.

    """

    def __init__(self, action, column):
        self.action = action
        self.place_column = column

    def __str__(self):
        return ', '.join([str(self.action), str(self.place_column)])


class Actions(enum.Enum):
    PLACE = enum.auto()


class ActionError(Exception):
    """
    An error class that can be raised when an action is deemed invalid by the state. Other exception classes, such as
    ValueError, can be raised when the game can determine that an action would always be invalid (such as placing a
    token in column -1). When the validity of an action must be determined based on the state (such as placing a token
    in a full column), and ActionError should be raised.

    """
    pass


class Outcome:
    """
    Outcome is a data-only class meant to act as a record of the progress and outcome of a game between agents.
    An Outcome has the following fields:
        agent_outcomes: A dict of {Agent: Outcomes} pairs for each participating agent.
        record: A list of (token, Action) tuples that can be used to recreate the progress of play during the game.

    """

    def __init__(self, agents):
        self.agent_outcomes = {agent: None for agent in agents}
        self.record = []

    def __str__(self):
        return '\n'.join([
            'Agent outcomes',
            '\n'.join([
                ''.join([str(agent.token), ': ', str(self.agent_outcomes[agent])]) for agent in self.agent_outcomes
            ]),
            'Action record',
            '\n'.join([', '.join([str(element) for element in record]) for record in self.record])
        ])

    def append_to_record(self, token, action):
        self.record.append((token, action))


class Outcomes(enum.Enum):
    WIN = enum.auto()
    LOSE = enum.auto()
    DRAW = enum.auto()
