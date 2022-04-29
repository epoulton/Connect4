import bidict
import copy
import enum
import itertools
import random
import string


class Actions(enum.Enum):

    PLACE = enum.auto()
    REMOVE = enum.auto()


class Game:

    def __init__(self, agents):
        self.agents = agents

    def play(self):
        agents = itertools.cycle(random.sample(self.agents, len(self.agents)))
        state = State([agent.token for agent in self.agents])

        while True:
            selected_action = next(agents).select_action(state.expose_to_agent())

            if not state.execute_action(selected_action):
                # TODO: What if the action fails?
                pass

            outcome = state.check_for_end()

            if outcome:
                break

        for agent in self.agents:
            agent.notify_outcome(outcome)

        return outcome


class State:

    internal_tokens = string.ascii_lowercase

    def __init__(self, external_tokens, size=(6, 7)):
        # TODO: Ensure len(external_tokens) <= len(self.internal_tokens)
        self.token_map = bidict.bidict({k: v for k, v in zip(external_tokens, State.internal_tokens[:len(external_tokens)])})
        self.n_rows, self.n_columns = size

        self.board = [None]*self.n_rows*self.n_columns

    def __str__(self):
        return '\n'.join([
            ''.join([
                '[',
                ','.join([
                    ' ' if cell is None else str(self.token_map.inverse[cell])[0] for cell in self.board[row*self.n_columns : (row + 1)*self.n_columns]
                ]),
                ']'
            ]) for row in range(self.n_rows)
        ])

    def expose_to_agent(self):
        return copy.deepcopy(self)

    def execute_action(self, action):
        if action['action'] == Actions.PLACE:
            is_successful = self._place_token(action['column'], action['token'])
        
        elif action['action'] == Actions.REMOVE:
            is_successful = self._remove_token(action['column'])
            
        else:
            # TODO: What to do if the action string is something else?
            is_successful = False
        
        return is_successful

    def check_for_end(self):
        outcome = None

        if None not in self.board:
            outcome = {token: 'Draw' for token in self.token_map}

        else:
            for line in self._generate_lines():
                if line[0] is not None and len(set(line)) == 1:
                    outcome = {token: 'Win' if line[0] == self.token_map[token] else 'Loss' for token in self.token_map}
                    break

        return outcome

    def _generate_lines(self):
        for row in range(self.n_rows):
            for column in range(self.n_columns - 3):
                yield self.board[row*self.n_columns + column : row*self.n_columns + column + 4]

        for row in range(self.n_rows - 3):
            for column in range(self.n_columns):
                yield self.board[row*self.n_columns + column : (row + 4)*self.n_columns + column : self.n_columns]

        for row in range(self.n_rows - 3):
            for column in range(self.n_columns - 3):
                yield self.board[row*self.n_columns + column : (row + 4)*self.n_columns + column + 4 : self.n_columns + 1]

        for row in range(self.n_rows - 3):
            for column in range(3, self.n_columns):
                yield self.board[row*self.n_columns + column : (row + 4)*self.n_columns + column - 4 : self.n_columns - 1]

    def _place_token(self, column, token):
        lowest_open_cell_in_column = None

        for row in range(self.n_rows):
            if self.board[row*self.n_columns + column - 1] is None:
                lowest_open_cell_in_column = row
            else:
                break

        if lowest_open_cell_in_column is not None:
            self.board[lowest_open_cell_in_column*self.n_columns + column - 1] = self.token_map[token]
            is_successful = True
            
        else:
            # TODO: What if the column is full?
            is_successful = False
            
        return is_successful

    def _remove_token(self, column):
        highest_filled_cell_in_column = None

        for row in range(self.n_rows):
            if self.board[row*self.n_columns + column - 1] is not None:
                highest_filled_cell_in_column = row
                break

        if highest_filled_cell_in_column is not None:
            self.board[highest_filled_cell_in_column*self.n_columns + column - 1] = None
            is_successful = True

        else:
            # TODO: What if the column is empty?
            is_successful = False

        return is_successful


class Agent:

    def __init__(self, token):
        self.token = token

    def select_action(self, state):
        raise NotImplementedError

    def notify_outcome(self, outcome):
        raise NotImplementedError


class CLIAgent(Agent):

    def select_action(self, state):
        print(state)
        column = int(input(' '.join([str(self.token), 'to play.'])))
        # TODO: Validate input

        return {'action': Actions.PLACE, 'column': column, 'token': self.token}

    def notify_outcome(self, outcome):
        print(self.token, outcome[self.token])


if __name__ == '__main__':
    p1 = CLIAgent('X')
    p2 = CLIAgent('O')

    g = Game([p1, p2])
    g.play()
