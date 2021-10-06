import math
from lirc import RawConnection
import RPi.GPIO as GPIO

BLANK_NUM = 0
MARKER_NUM = -1
PLAYER1_NUM = 1
PLAYER2_NUM = 2

CONSOLE_DEBUG = True


gameState = [[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM]]
latchpins = [13, 19, 21, 23]
markerPos = [1, 1]
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

playerColors = [[True,False,False],[False,False,True]]
markerColor = [True, True, True]
shiftStates = [
    [False, False, False, False, False, False, False, False], 
    [False, False, False, False, False, False, False, False], 
    [False, False, False, False, False, False, False, False], 
    [False, False, False, False, False, False, False, False]
]

gameInProgress = False
turnState = True
prevStartState = True
choosingColor = False

dataPin = 11
clockPin = 15

connection = RawConnection()

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

#Util
def resetGameState():
    global gameInProgress
    global gameState
    gameInProgress = False
    gameState = [[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM]]
    GPIO.output(dataPin, GPIO.LOW)

    for state in shiftStates:
        for i in range(8):
            state[i] = False

    for i in range(0,8):
        GPIO.output(clockPin, GPIO.LOW)
        GPIO.output(clockPin, GPIO.HIGH)
    GPIO.output(clockPin, GPIO.LOW)

    for pin in latchpins:
        GPIO.output(pin, GPIO.LOW)
        GPIO.output(pin, GPIO.HIGH)
	
def chooseColor(playerID, newColor): 
    if(not (playerID == PLAYER2_NUM or playerID == PLAYER1_NUM)):
        print("Recieved an invalid player ID: " + str(playerID))
    elif(matchingArrays(playerColors[0 if playerID == 1 else 1], newColor) or matchingArrays(newColor, markerColor)): 
        print("The other player is already this color, please select another color")
    else:
        playerColors[0 if playerID == PLAYER1_NUM else 1] = newColor
        print("Successfully changed player " + str(playerID) + "'s color")

def clearBoard():
    gameState = [[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM]]

def startGame():
    global prevStartState
    resetGameState()
    turnState = not prevStartState
    prevStartState = turnState
    gameInProgress = True
    while gameInProgress:
        try:
            processInput()
        except KeyboardInterrupt:
            break
    resetGameState()

def checkForWin():
    #Check Rows
    hasWon = False
    for row in gameState:
        if matchingRows(row) and (row[0] == PLAYER1_NUM or row[0] == PLAYER2_NUM):
            won(row[0])
            return

    #Check Columns
    cols = [[], [], []]
    for i, row in enumerate(gameState):
        for j, col in enumerate(row):
            cols[j].append(col)
    for row in cols:
        if matchingRows(row) and (row[0] == PLAYER1_NUM or row[0] == PLAYER2_NUM):
            won(row[0])
            return

    #Check Diagonals
    diag = [[], []]
    for i in range(3):
            diag[0].append(gameState[i][i])
            diag[1].append(gameState[i][2-i])
    for row in cols:
        if matchingRows(row) and (row[0] == PLAYER1_NUM or row[0] == PLAYER2_NUM):
            won(row[0])
            return


def won(playerNum):
    global gameInProgress
    print("Player " + str(playerNum) + " won!")
    gameInProgress = False
            
def matchingRows(list):
    if(len(list) == 0):
        return False
    firstElem = list[0]
    for thing in list:
        if thing != firstElem:
            return False
    return True

#Interaction
def moveMarkerRelative(x, y):
    markerPos[0] += x
    markerPos[1] += y
    markerPos[0] %= 3
    markerPos[1] %= 3

def setMarkerPos(x = markerPos[0],y = markerPos[1]):
    markerPos[0] = x % 3
    markerPos[1] = y % 3

#Display
def refreshDisplay(showMarker = True):
    if not gameInProgress:
        clearBoard()
    board = cloneBoard()
    board[markerPos[0]][markerPos[1]] = MARKER_NUM if showMarker else 0
    #Generate ShiftStates
    if CONSOLE_DEBUG:
        print("The game state is " + str(board))
    for i, row in enumerate(board):
        for j, position in enumerate(row):
            association = LEDAssociation[(i * 3) + j]
            if position == PLAYER1_NUM or position == PLAYER2_NUM:
                for k in range(3):
                    shiftStates[association[k][0]][association[k][1]] = playerColors[0 if position == PLAYER1_NUM else 1][k]
            elif position == MARKER_NUM:
                for k in range(3):
                    shiftStates[association[k][0]][association[k][1]] = markerColor[k]
            else:
                for k in range(3):
                    shiftStates[association[k][0]][association[k][1]] = False
    #Apply Shift States
    shiftOut(shiftStates)
    
#INPUTS
def processInput():
    try:
        keypress = connection.readline(.0001)
    except:
        keypress=""
    
    if(keypress != "" and keypress is not None):
        data = keypress.split()
        repeats = data[1]
        command = data[2]

        if(repeats != "00"):
            return
        ''' KEY_UP                   0x629D
          KEY_DOWN                 0xA857
          KEY_LEFT                 0x22DD
          KEY_RIGHT                0xC23D
          KEY_OK                   0x02FD
          KEY_1                    0x6897
          KEY_2                    0x9867
          KEY_3                    0xB04F
          KEY_4                    0x30CF
          KEY_5                    0x18E7
          KEY_6                    0x7A85
          KEY_7                    0x10EF
          KEY_8                    0x38C7
          KEY_9                    0x5AA5
          KEY_0                    0x4AB5
          KEY_NUMERIC_STAR         0x42BD
          KEY_NUMERIC_POUND        0x52AD'''
        if command == "KEY_UP":
            moveMarkerRelative(0, -1)
        elif command == "KEY_DOWN":
            moveMarkerRelative(0, 1)
        elif command == "KEY_RIGHT":
            moveMarkerRelative(1, 0)
        elif command == "KEY_LEFT":
            moveMarkerRelative(-1, 0)
        elif command == "KEY_OK":
            makeMove()
        elif command == "KEY_1":
            setMarkerPos(0, 0)
        elif command == "KEY_2":
            setMarkerPos(0, 1)
        elif command == "KEY_3":
            setMarkerPos(0, 2)
        elif command == "KEY_4":
            setMarkerPos(1, 0)
        elif command == "KEY_5":
            setMarkerPos(1, 1)
        elif command == "KEY_6":
            setMarkerPos(1, 2)
        elif command == "KEY_7":
            setMarkerPos(2, 0)
        elif command == "KEY_8":
            setMarkerPos(2, 1)
        elif command == "KEY_9":
            setMarkerPos(2, 2)
        elif command == "KEY_NUMERIC_STAR":
            print("Selecting color for player 1")
            selectColor(1)
        elif command == "KEY_NUMERIC_POUND":
            print("Selecting color for player 2")
            selectColor(2)
        refreshDisplay()

def makeMove():
    global turnState
    if gameState[markerPos[0]][markerPos[1]] == BLANK_NUM:
        gameState[markerPos[0]][markerPos[1]] = PLAYER1_NUM if turnState else PLAYER2_NUM
        turnState = not turnState
        checkForWin()


def selectColor(playerID):
    colorSelected = False
    currcolor = playerColors[playerID]
        
    while not colorSelected:
        changeColors = True
        try:
            keypress = connection.readline(.0001)
        except:
            keypress=""
    
        if(keypress != "" and keypress is not None):
            data = keypress.split()
            repeats = data[1]
            command = data[2]

            if(repeats != "00"):
                continue

            if command == "KEY_1":
                currcolor = [False, False, True]
            elif command == "KEY_2":
                currcolor = [False, True, False]
            elif command == "KEY_3":
                currcolor = [True, False, False]
            elif command == "KEY_4":
                currcolor = [False, True, True]
            elif command == "KEY_5":
                currcolor = [True, True, False]
            elif command == "KEY_6":
                currcolor = [True, False, True]
            elif command == "KEY_8":
                currcolor = [True, True, True]
            else:
                changeColors = False
            
            if command == "KEY_OK":
                print("Changing player " + str(playerID) + "'s Color to " + str(currcolor))
                chooseColor(playerID, currcolor)
                colorSelected = True
            
            
            if changeColors and not (matchingArrays(playerColors[0 if playerID == 1 else 1], currcolor) or matchingArrays(currcolor, markerColor)):
                colorStates = []
                for i, state in enumerate(shiftStates):
                    colorStates.append([])
                    for j in range(8):
                        colorStates.append(currcolor[((i * 8) + j) % 3])

                shiftOut(colorStates)


#UTIL

def shiftOut(states):
    for i, state in enumerate(states):
            GPIO.output(latchpins[i], GPIO.LOW)
            for high in state:
                GPIO.output(clockPin, GPIO.LOW)
                GPIO.output(dataPin, GPIO.HIGH if high else GPIO.LOW)
                GPIO.output(clockPin, GPIO.HIGH)
            GPIO.output(latchpins[i], GPIO.HIGH)

def matchingArrays(A1, A2):
    for i, thing in enumerate(A1):
        if A2[i] != thing:
            return True
    return False

def cloneBoard():
    newboard = []
    for i, thing in enumerate(gameState):
        newboard.append([])
        for otherthing in thing:
            newboard[i].append(otherthing)
    return newboard

setup()
startGame()
