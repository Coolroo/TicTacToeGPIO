import math
import time
from lirc import RawConnection
import RPi.GPIO as GPIO

#CONSTANTS
BLANK_NUM = 0
MARKER_NUM = -1
PLAYER1_NUM = 1
PLAYER2_NUM = 2

#DEBUG
CONSOLE_DEBUG = True

#Board Presets
BOARD_RING = [["1", "1", "1"], ["1", "0", "1"], ["1", "1", "1"]]
BOARD_DOT = [["0", "0", "0"], ["0", "1", "0"], ["0", "0", "0"]]
BOARD_X = [["1", "0", "1"], ["0", "1", "0"], ["1", "0", "1"]]
BOARD_INVERSE_X = [["0", "1", "0"], ["1", "0", "1"], ["0", "1", "0"]]
BOARD_PLUS = [["0", "1", "0"], ["1", "1", "1"], ["0", "1", "0"]]
BOARD_CORNERS = [["1", "0", "1"], ["0", "0", "0"], ["1", "0", "1"]]

BOARD_EMPTY = [["0", "0", "0"], ["0", "0", "0"], ["0", "0", "0"]]

#INT Array Variables
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

#Boolean Array Variables

#Colors are stored as a boolean array with 3 entries corresponding to RED, GREEN, BLUE
playerColors = [[True,False,False],[False,False,True]]
markerColor = [True, True, False]
shiftStates = [
    [False, False, False, False, False, False, False, False], 
    [False, False, False, False, False, False, False, False], 
    [False, False, False, False, False, False, False, False], 
    [False, False, False, False, False, False, False, False]
]

#INT Variables
dataPin = 11
clockPin = 15

#Boolean Variables
gameInProgress = False
turnState = True
prevStartState = True
choosingColor = False

#OBJ Variables
connection = RawConnection()

#GPIOGarbage
#Setup for the GPIO Board
def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(dataPin, GPIO.OUT)
    GPIO.setup(clockPin, GPIO.OUT)
    for pin in latchpins:
        GPIO.setup(pin, GPIO.OUT)

#Cleans up the GPIO board
def destroy():
    GPIO.cleanup()

#Game

#Util

#Resets the game to the state it was in before the game started
def resetGameState():
    global gameInProgress
    global gameState
    gameInProgress = False
    gameState = [[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM]]
    GPIO.output(dataPin, GPIO.LOW)

    for state in shiftStates:
        for i in range(8):
            state[i] = False

    for i in range(8):
        GPIO.output(clockPin, GPIO.LOW)
        GPIO.output(clockPin, GPIO.HIGH)
    GPIO.output(clockPin, GPIO.LOW)

    for pin in latchpins:
        GPIO.output(pin, GPIO.LOW)
        GPIO.output(pin, GPIO.HIGH)
	
#Sets the color of a given player, as long as it is not the marker color and not the other player's color
def chooseColor(playerID, newColor): 
    if(not (playerID == PLAYER2_NUM or playerID == PLAYER1_NUM)):
        print("Recieved an invalid player ID: " + str(playerID))
    elif(matchingArrays(playerColors[0 if playerID == 1 else 1], newColor) or matchingArrays(newColor, markerColor)): 
        print("The other player is already this color, please select another color")
    else:
        playerColors[0 if playerID == PLAYER1_NUM else 1] = newColor
        print("Successfully changed player " + str(playerID) + "'s color")

#Clears the board
def clearBoard():
    global gameState
    gameState = [[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM]]

#Checks to see if any player has won
def checkForWin():
    #Check Rows
    for row in gameState:
        if matchingRows(row) and (row[0] == PLAYER1_NUM or row[0] == PLAYER2_NUM):
            won(row[0])
            return True

def checkForFail():
    cols = [[], [], []]
    diag = [[], []]
    for i, row in enumerate(gameState):
        if(not isRowBlocked(row)):
            return
        for j, thing in enumerate(row):
            cols[j][i] = thing

    for col in cols:
        if(not isRowBlocked(col)):
            return

    for i in range(3):
        diag[0][i] = gameState[i][i]
        diag[1][i] = gameState[i][2 - i]
    for d in diag:
        if(not isRowBlocked(col)):
            return

    fail()


    #Check Columns
    cols = [[], [], []]
    for i, row in enumerate(gameState):
        for j, col in enumerate(row):
            cols[j].append(col)
    for row in cols:
        if matchingRows(row) and (row[0] == PLAYER1_NUM or row[0] == PLAYER2_NUM):
            won(row[0])
            return True

    #Check Diagonals
    diag = [[], []]
    for i in range(3):
            diag[0].append(gameState[i][i])
            diag[1].append(gameState[i][2-i])
    for row in diag:
        if matchingRows(row) and (row[0] == PLAYER1_NUM or row[0] == PLAYER2_NUM):
            won(row[0])
            return True
    return False

#Win as a given player
def won(playerNum):
    global gameInProgress
    print("Player " + str(playerNum) + " won!")
    shiftOut(buildColorStates(BOARD_RING, {"1" : playerColors[0 if playerNum == PLAYER1_NUM else 1]}))
    time.sleep(1)
    shiftOut(buildColorStates(BOARD_DOT, {"1" : playerColors[0 if playerNum == PLAYER1_NUM else 1]}))
    time.sleep(1)
    shiftOut(buildColorStates(BOARD_X, {"1" : playerColors[0 if playerNum == PLAYER1_NUM else 1]}))
    time.sleep(1)
    shiftOut(buildColorStates(BOARD_INVERSE_X, {"1" : playerColors[0 if playerNum == PLAYER1_NUM else 1]}))
    time.sleep(1)
    shiftOut(buildColorStates(BOARD_PLUS, {"1" : playerColors[0 if playerNum == PLAYER1_NUM else 1]}))
    time.sleep(1)
    shiftOut(buildColorStates(BOARD_CORNERS, {"1" : playerColors[0 if playerNum == PLAYER1_NUM else 1]}))
    time.sleep(1)
    gameInProgress = False

def fail():
    global gameInProgress
    shiftOut(buildColorStates(BOARD_X, {"1" : [True, False, False]}))
    time.sleep(1)
    shiftOut(buildColorStates(BOARD_EMPTY, {}))
    time.sleep(1)
    shiftOut(buildColorStates(BOARD_X, {"1" : [True, False, False]}))
    time.sleep(1)
    shiftOut(buildColorStates(BOARD_EMPTY, {}))
    time.sleep(1)
    shiftOut(buildColorStates(BOARD_X, {"1" : [True, False, False]}))
    time.sleep(1)
    shiftOut(buildColorStates(BOARD_EMPTY, {}))
    time.sleep(1)
    gameInProgress = False
        

#Gameplay
#Starts the game
def startGame():
    global prevStartState
    global gameInProgress
    global turnState
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

#Makes a move based on the current player and the marker position
def makeMove():
    global turnState
    if gameState[markerPos[0]][markerPos[1]] == BLANK_NUM:
        gameState[markerPos[0]][markerPos[1]] = PLAYER1_NUM if turnState else PLAYER2_NUM
        turnState = not turnState
        if not checkForWin():
            checkForFail()
    else:
        print("Cannot move here as player " + str(gameState[markerPos[0]][markerPos[1]]) + " already has this space marked")


#Interaction

#Moves the marker based on its relative position
def moveMarkerRelative(x, y):
    markerPos[0] += x
    markerPos[1] += y
    markerPos[0] %= 3
    markerPos[1] %= 3

#Sets the marker's absolute position
def setMarkerPos(x = markerPos[0],y = markerPos[1]):
    markerPos[0] = x % 3
    markerPos[1] = y % 3

#Display

#Refreshes all of the shift states based on the board and marker position and shifts them to their respective registers
def refreshDisplay(showMarker = True):
    #Clear the board if the game is over
    if not gameInProgress:
        clearBoard()
    #Clone the board so we can modify it based on the marker position
    board = cloneBoard()
    #Add the marker to the board
    board[markerPos[0]][markerPos[1]] = MARKER_NUM if showMarker else 0
    if CONSOLE_DEBUG:
        print("The game state is " + str(board))
    #Generate ShiftStates
    buildShiftStates(board)
    #Apply Shift States
    shiftOut(shiftStates)
    
def buildShiftStates(board):
    for i, row in enumerate(board): #Get all the rows of the board
        for j, position in enumerate(row):  #Get all items in the row
            association = LEDAssociation[(i * 3) + j] #Get the association of the current position
            if position == PLAYER1_NUM or position == PLAYER2_NUM: #If this is a player number, set the LED color to this player's color
                for k in range(3):
                    shiftStates[association[k][0]][association[k][1]] = playerColors[0 if position == PLAYER1_NUM else 1][k]
            elif position == MARKER_NUM: #If this is the marker number, set the LED color to the marker color
                for k in range(3):
                    shiftStates[association[k][0]][association[k][1]] = markerColor[k]
            else: #Else turn the LED off
                for k in range(3):
                    shiftStates[association[k][0]][association[k][1]] = False

def buildColorStates(board, keys):
    state = []
    for row in shiftStates:
        state.append([])
    for i, row in enumerate(board):
        for j, position in enumerate(row):
            association = LEDAssociation[(i * 3) + j]
            if position not in keys:
                for k in range(3):
                    state[i].append(False)
            else:
                for k in range(3):
                    state[i].append(keys[position][k])
    return state

                    
#INPUTS
def processInput():
    try:
        #Get an input
        keypress = connection.readline(.0001)
    except KeyboardInterrupt:
        #We have to rethrow this exception so this doesn't consume it
        raise KeyboardInterrupt 
    except:
        #If we run into any other errors, just make keypress nothing
        keypress=""
    
    #Make sure we are using a valid key
    if(keypress != "" and keypress is not None):
        data = keypress.split() #Split the input up
        repeats = data[1] #This is how long the button has been held
        command = data[2] #This is what the input command was

        if(repeats != "00"): #If the button is being held, just ignore it
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
        #Refresh the display after an input
        refreshDisplay()

#A menu for players to select their color
def selectColor(playerID):
    colorSelected = False
    currcolor = playerColors[playerID]
        
    #While the player is selecting their color
    while not colorSelected:
        changeColors = True
        #This acts the same as ProcessInput()
        try:
            keypress = connection.readline(.0001)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except:
            keypress=""
    
        if(keypress != "" and keypress is not None):
            data = keypress.split()
            repeats = data[1]
            command = data[2]

            if(repeats != "00"):
                continue
            #Colors are stored as a boolean array with 3 entries corresponding to RED, GREEN, BLUE
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
            
            #If we are selecting the current color
            if command == "KEY_OK":
                print("Changing player " + str(playerID) + "'s Color to " + str(currcolor))
                chooseColor(playerID, currcolor)
                colorSelected = True
            
            #Shift out the color changes as the entire board for easily viewing the selected color
            if changeColors and not (matchingArrays(playerColors[0 if playerID == PLAYER1_NUM else 1], currcolor) or matchingArrays(currcolor, markerColor)):
                colorStates = []
                for i, state in enumerate(shiftStates):
                    colorStates.append([])
                    for j in range(8):
                        colorStates.append(currcolor[((i * 8) + j) % 3])
                #Shift out the current colorState
                shiftOut(colorStates)


#UTIL

#Shifts out a boolean array to the shift registers
def shiftOut(states):
    for i, state in enumerate(states): #Get all the registers
            GPIO.output(latchpins[i], GPIO.LOW) #Set the register's out pin to low
            for i in range(8): #Get the boolean in the current state
                GPIO.output(clockPin, GPIO.LOW) #Set the clock to low
                GPIO.output(dataPin, GPIO.HIGH if not len(state) <= 7-i and state[7-i] else GPIO.LOW) #Set the data pin to high/low based on the boolean value
                GPIO.output(clockPin, GPIO.HIGH) #Clock it
            GPIO.output(latchpins[i], GPIO.HIGH) #Latch it

#Checks if 2 arrays have the same elements
def matchingArrays(A1, A2):
    for i, thing in enumerate(A1):
        if A2[i] != thing:
            return True
    return False

#Clones the current gameState
def cloneBoard():
    newboard = []
    for i, thing in enumerate(gameState):
        newboard.append([])
        for otherthing in thing:
            newboard[i].append(otherthing)
    return newboard

#Checks if an array has all the same elements
def matchingRows(list):
    if(list is None or len(list) == 0):
        return False
    firstElem = list[0]
    for thing in list:
        if thing != firstElem:
            return False
    return True

def isRowBlocked(row):
    return PLAYER1_NUM in row and PLAYER2_NUM in row


#STARTUP
setup()
startGame()
