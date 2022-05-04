import connect4

p1 = connect4.CLIAgent('X')
p2 = connect4.RandomAgent('O')

connect4.Game([p1, p2]).play()
