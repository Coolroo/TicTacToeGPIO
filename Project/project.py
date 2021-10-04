gameState = [[0,0,0],[0,0,0],[0,0,0]]

playerColors = [[True,False,False],[False,False,True]]
dataPin = 0
clockPin = 0
latchpins = []
markerPos = [1, 1]
gameInProgress = False
shiftStates = [[False, False, False, False, False, False, False, False], [False, False, False, False, False, False, False, False], [False, False, False, False, False, False, False, False], [False, False, False, False, False, False, False, False]]

LEDAssociation = [
        {
         "red" : [0, 0]
         "green" : [0, 1]
         "blue" : [0, 2]
        },
        {
         "red" : [0, 3]
         "green" : [0, 4]
         "blue" : [0, 5]
        },
        {
            "red" : [0,6]
            "green" : [0,7]
            "blue" : [1,0]
        },
        {
            "red" : [1,1]
            "green" : [1,2]
            "blue" : [1,3]
        },
        {
            "red" : [1,4]
            "green" : [1,5]
            "blue" : [1,6]
        },
        {
            "red" : [1,7]
            "green" : [2,0]
            "blue" : [2,1]
        },
        {
            "red" : [2,2]
            "green" : [2,3]
            "blue" : [2,4]
        },
        {
            "red" : [2,5]
            "green" : [2,6]
            "blue" : [2,7]
        },
        {
            "red" : [3,0]
            "green" : [3,1]
            "blue" : [3,2]
        }

        
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
    elif(matchingArrays(playerColors[0 if playerID == 1 else 1], newColor) or matchingArrays(newColor, [True, True, True])): 
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
    board = cloneBoard
    board[markerPos[0]][markerPos[1]] = -1
    for i, row in enumerate(board):
        for j, position in enumerate(row):
            register = (j + (9 * i)) / 8
            pin = ((9 * i) + j) % 8




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
