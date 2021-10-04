import math
gameState = [[0,0,0],[0,0,0],[0,0,0]]

playerColors = [[True,False,False],[False,False,True]]
markerColor = [True, True, True]
dataPin = 0
clockPin = 0
latchpins = []
markerPos = [1, 1]
gameInProgress = False
shiftStates = [[False, False, False, False, False, False, False, False], [False, False, False, False, False, False, False, False], [False, False, False, False, False, False, False, False], [False, False, False, False, False, False, False, False]]

LEDAssociation = [
                    [ #LED 1
                        [0,0], [0,1], [0,2]
                    ], 
                    [ #LED 2
                        [0,3], [0,4], [0,5]
                    ],
                    [ #LED 3
                        [0,6], [0,7], [1,0]
                    ],
                    [ #LED 4
                        [1,1], [1,2], [1,3]
                    ],
                    [ #LED 5
                        [1,4], [1,5], [1,6]
                    ],
                    [ #LED 6
                        [1,7], [2,0], [2,1]
                    ],
                    [ #LED 7
                        [2,2], [2,3], [2,4]
                    ],
                    [ #LED 8
                        [2,5], [2,6], [2,7]
                    ],
                    [ #LED 9
                        [3,0], [3,1], [3,2]
                    ]
                 ]

#GPIOGarbage
def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(dataPin, GPIO.OUT)
    GPIO.setup(clockPin, GPIO.OUT)
    for pin in latchpins:
        GPIO.setup(pin, GPIO.OUT)

def destroy():
    GPIO.cleanup()

#Game
def resetGameState():
    gameInProgress = False
    gameState= [[0,0,0],[0,0,0],[0,0,0]]
    GPIO.output(dataPin, GPIO.LOW)
    for i in range(0,8):
        GPIO.output(clockPin, GPIO.LOW)
        GPIO.output(clockPin, GPIO.HIGH)
    GPIO.output(clockPin, GPIO.LOW)
    for pin in latchpins:
        GPIO.output(pin, GPIO.LOW)
        GPIO.output(pin, GPIO.HIGH)
	
def chooseColor(playerID, newColor):
    if(playerID != 1 or playerID != 0):
        print("Recieved an invalid player ID: " + str(playerID))
    elif(matchingArrays(playerColors[0 if playerID == 1 else 1], newColor) or matchingArrays(newColor, markerColor)): 
        print("The other player is already this color, please select another color")
    else:
        playerColors[playerID] = newColor
        print("Successfully changed player " + str(playerID) + "'s color")

def moveMarkerRelative(x, y):
    marker[0] += x
    marker[1] += y
    for i in range(2):
        if(marker[i] > 2):
            marker[i] = 0
        elif(marker[i] < 0):
            marker[i] = 2

def refreshDisplay():
    if not gameInProgress:
        clearBoard()
    board = cloneBoard()
    board[markerPos[0]][markerPos[1]] = -1
    #Generate ShiftStates
    for i, row in enumerate(board):
        for j, position in enumerate(row):
            association = LEDAssociation[i][j]
            if position == 1 or position == 2:
                for k in range(3):
                    shiftStates[association[k][0]][association[k][1]] = playerColors[position - 1][k]
            elif position = -1:
                for k in range(3):
                    shiftStates[association[k][0]][association[k][1]] = markerColor[k]
            else:
                for k in range(3):
                    shiftStates[association[k][0]][association[k][1]] = False
    #Apply Shift States
    for i, state in enumerate(shiftStates):
        GPIO.output(latchpins[i], GPIO.LOW)
        for j, val in enumerate(state):
            GPIO.output(clockPin, GPIO.LOW)
            GPIO.output(dataPin, GPIO.HIGH if val else GPIO.LOW)
            GPIO.output(clockPin, GPIO.HIGH)
        GPIO.output(latchpins[i], GPIO.HIGH)





#UTIL
def matchingArrays(A1, A2):
    for i, thing in enumerate(A1):
        if A2[i] != thing:
            return True
    return False

def cloneBoard():
    newboard = []
    for i, thing in enumerate(gameState):
        newboard[i] = []
        for j, otherthing in enumerate(thing):
            newboard[i][j] = otherthing
    return newboard

def clearBoard():
    gameState = [[0,0,0], [0,0,0], [0,0,0]]
