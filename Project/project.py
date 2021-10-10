import math
import time
from lirc import RawConnection
import RPi.GPIO as GPIO

#CONSTANTS
BLANK_NUM = 0
MARKER_NUM = -1
PLAYER1_NUM = 1
PLAYER2_NUM = 2

CLOCK_TICK = 0.0001

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
BOARD_FULL = [["1", "1", "1"], ["1", "1", "1"], ["1", "1", "1"]]

#INT Array Variables
gameState = [[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM]]
latchpins = [15, 19, 21, 23]
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
clockPin = 13

#Boolean Variables
gameInProgress = False
turnState = True
prevStartState = True
choosingColor = False

#OBJ Variables
connection = RawConnection()

#GPIOGarbage
"""
Sets up the GPIO pins for the LED display.

Parameters
----------
dataPin : int
    The pin that the data line of the display is connected to.
clockPin : int
    The pin that the clock line of the display is connected to.
latchpins : list of int
    The pins that the latch line of the display is connected to.

Returns
-------
None
"""
def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(dataPin, GPIO.OUT)
    GPIO.setup(clockPin, GPIO.OUT)
    for pin in latchpins:
        GPIO.setup(pin, GPIO.OUT)

"""
    This function is used to destroy the GPIO setup.
    It is called when the program is exited.
    It takes no parameters.
    It returns nothing.
"""
def destroy():
    GPIO.cleanup()

#Game

#Util

"""
    This function resets the game state by setting all the shift registers to 0 and setting the game state to the initial blank state.
    Parameters:
        None
    Returns:
        None
"""
def resetGameState():
    global gameInProgress
    global gameState
    gameInProgress = False
    gameState = [[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM]]
    GPIO.output(dataPin, GPIO.LOW)

    for i, state in enumerate(shiftStates):
        shiftStates[i] = [False, False, False, False, False, False, False, False]

    for i in range(8):
        GPIO.output(clockPin, GPIO.LOW)
        GPIO.output(clockPin, GPIO.HIGH)
    GPIO.output(clockPin, GPIO.LOW)

    for pin in latchpins:
        GPIO.output(pin, GPIO.LOW)
        GPIO.output(pin, GPIO.HIGH)
        GPIO.output(pin, GPIO.LOW)
	
"""
    Changes the color of the player with the given ID to the given color.
    
    Parameters:
        playerID (int): The ID of the player to change the color of.
        newColor (list): The new color to change the player to.
        
    Returns:
        None
"""
def chooseColor(playerID, newColor): 
    if(not (playerID == PLAYER2_NUM or playerID == PLAYER1_NUM)):
        print("Recieved an invalid player ID: " + str(playerID))
    elif(matchingArrays(playerColors[0 if playerID == 1 else 1], newColor) or matchingArrays(newColor, markerColor)): 
        print("The other player is already this color, please select another color")
    else:
        playerColors[0 if playerID == PLAYER1_NUM else 1] = newColor
        print("Successfully changed player " + str(playerID) + "'s color")

"""
This function clears the game board, 
and sets the game state to the default state.

Parameters:
    None

Returns:
    None
"""
def clearBoard():
    global gameState
    gameState = [[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM],[BLANK_NUM,BLANK_NUM,BLANK_NUM]]

"""
Checks the game state for a win condition.

Parameters
----------
gameState : list
    A list of lists representing the game state.

Returns
-------
bool
    True if a win condition exists, False otherwise.
"""
def checkForWin():
    #Check Rows
    for row in gameState:
        if matchingRows(row) and (row[0] == PLAYER1_NUM or row[0] == PLAYER2_NUM):
            won(row[0])
            return True
    
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

"""
Checks if the game is over by checking if there are any unnblocked rows.

Parameters:
    gameState (list): A list of lists representing the game state.

Returns:
    bool: True if the game is over, False otherwise.
"""
def checkForFail():
    cols = [[], [], []]
    diag = [[], []]
    for i, row in enumerate(gameState):
        if(not isRowBlocked(row)):
            return False
        for j, thing in enumerate(row):
            cols[j].append(thing)

    for col in cols:
        if(not isRowBlocked(col)):
            return False

    for i in range(3):
        diag[0].append(gameState[i][i])
        diag[1].append(gameState[i][2 - i])
    for d in diag:
        if(not isRowBlocked(col)):
            return False

    fail()
    return True

"""
This function is used to declare a winner of the game. 
It takes a player number and displays the winning animation.

Parameters:
    playerNum (int): The player number that won.

Returns:
    None
"""
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

"""
This function is used to indicate that the game has failed. 
It will do this by flashing the board red three times.

Parameters:
    None

Output:
    None
"""
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
"""
startGame()
    Starts a game of Tic Tac Toe.

    Parameters
    ----------
    None

    Returns
    -------
    None
"""
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

"""
Makes a move for the current player at the current marker position.

Parameters:
    None

Returns:
    True if the move was made, False otherwise
"""
def makeMove():
    global turnState
    if gameState[markerPos[0]][markerPos[1]] == BLANK_NUM:
        gameState[markerPos[0]][markerPos[1]] = PLAYER1_NUM if turnState else PLAYER2_NUM
        turnState = not turnState
        refreshDisplay(False)
        if not checkForWin():
            checkForFail()
        return True
    else:
        print("Cannot move here as player " + str(gameState[markerPos[0]][markerPos[1]]) + " already has this space marked")
        return False


#Interaction

"""
This function moves the marker a relative distance from its current position.

Parameters
----------
x : int
    The number of squares to move the marker horizontally.
y : int
    The number of squares to move the marker vertically.

Returns
-------
None

"""
def moveMarkerRelative(x, y):
    markerPos[1] += x
    markerPos[0] += y
    markerPos[1] %= 3
    markerPos[0] %= 3

"""
Sets the position of the marker on the grid.

Parameters
----------
x : int
    The x coordinate of the marker.
y : int
    The y coordinate of the marker.

Returns
-------
None
"""
def setMarkerPos(x = markerPos[0],y = markerPos[1]):
    markerPos[0] = x % 3
    markerPos[1] = y % 3

#Display

"""
This function displays the current state of the board.

Parameters:
    showMarker: A boolean that determines whether or not the marker is displayed.

Returns:
    None
"""
def refreshDisplay(showMarker = True):
    #Clear the board if the game is over
    print("Refreshing Display")
    if not gameInProgress:
        clearBoard()
        print("Game not in progress, clearing board")
    #Clone the board so we can modify it based on the marker position
    board = cloneBoard()
    #Add the marker to the board
    if showMarker:
        board[markerPos[0]][markerPos[1]] = MARKER_NUM
    if CONSOLE_DEBUG:
        print("The game state is")
        print(str(board[0]))
        print(str(board[1]))
        print(str(board[2]))
    #Generate ShiftStates
    buildShiftStates(board)
    if CONSOLE_DEBUG:
        print("The shift states are:")
        for thing in shiftStates:
            print(str(thing))
    #Apply Shift States
    shiftOut(shiftStates)
    
"""
    Builds the shift states for the board.
    
    Parameters:
        board (list): The board to build the shift states for.
        
    Returns:
        shiftStates (list): The shift states for the board.
"""
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

"""
Builds a list of lists of boolean values representing the current state of the LEDs.

Parameters:
    board (list): A list of lists of ints representing the current state of the board.
    keys (dict): A dictionary of the form {str(int): [bool, bool, bool]} representing the current state of the keys.

Returns:
    list: A list of lists of booleans representing the current state of the LEDs.
"""
def buildColorStates(board, keys):
    state = []
    for i, row in enumerate(shiftStates):
        state.append([False, False, False, False, False, False, False, False])
    for i, row in enumerate(board):
        for j, position in enumerate(row):
            association = LEDAssociation[(i * 3) + j]
            if str(position) not in keys:
                for k in range(3):
                    state[association[k][0]][association[k][1]] = False
            else:
                for k in range(3):
                    state[association[k][0]][association[k][1]] = keys[str(position)][k]
    return state

                    
#INPUTS
"""
This function processes the input from the controller and makes changes to the board based on that input.

Parameters:
    None

Returns:
    None
"""
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
        showMarker = True
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
        else:
            showMarker = False

        if command == "KEY_OK":
            showMarker = not makeMove()
        elif command == "KEY_NUMERIC_STAR":
            print("Selecting color for player 1")
            selectColor(1)
        elif command == "KEY_NUMERIC_POUND":
            print("Selecting color for player 2")
            selectColor(2)
        #Refresh the display after an input
        refreshDisplay()

"""
    This function allows a player to select a color. 
    It takes a playerID and the current color as parameters. 
    It then asks the player to select a color and then changes the color of the player's pieces.

Parameters:
    playerID: the player who is selecting a color
    currcolor: the current color of the player's pieces

Returns:
    None
"""
def selectColor(playerID):
    colorSelected = False
    currcolor = playerColors[0 if playerID == PLAYER1_NUM else 1]
    shiftOut(buildColorStates(BOARD_FULL, {"1" : currcolor}))

    #While the player is selecting their color
    while not colorSelected:
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
            elif command == "KEY_OK":
                print("Changing player " + str(playerID) + "'s Color to " + str(currcolor))
                chooseColor(playerID, currcolor)
                colorSelected = True
                continue
            #Display the whole board as this color
            shiftOut(buildColorStates(BOARD_FULL, {"1" : currcolor}))


#UTIL

"""
This function takes a list of 8 booleans and shifts them out to the shift registers.

Parameters:
    states (list): A list of 8 booleans, each representing a state of the shift register.

Returns:
    None
"""
def shiftOut(states):
    clearRegisters()
    for i, state in enumerate(states): #Get all the registers
            GPIO.output(latchpins[i], GPIO.LOW) #Set the register's out pin to low
            time.sleep(CLOCK_TICK)
            for j in range(8): #Get the boolean in the current state
                GPIO.output(clockPin, GPIO.LOW) #Set the clock to low
                time.sleep(CLOCK_TICK)
                GPIO.output(dataPin, GPIO.HIGH if not len(state) <= 7-j and state[7-j] else GPIO.LOW) #Set the data pin to high/low based on the boolean value
                time.sleep(CLOCK_TICK)
                GPIO.output(clockPin, GPIO.HIGH) #Clock it
                time.sleep(CLOCK_TICK)
            GPIO.output(latchpins[i], GPIO.HIGH) #Latch it
            time.sleep(CLOCK_TICK)


"""
This function clears the registers and sets the outputs to low.

Parameters:
    dataPin: The GPIO pin that is connected to the data pin on the chip.
    clockPin: The GPIO pin that is connected to the clock pin on the chip.
    latchpins: The GPIO pins that are connected to the latch pins on the chip.

Returns:
    None
"""
def clearRegisters():
    GPIO.output(dataPin, GPIO.HIGH)
    for i in range(8):
        GPIO.output(clockPin, GPIO.LOW)
        GPIO.output(clockPin, GPIO.HIGH)
    GPIO.output(clockPin, GPIO.LOW)
    for pin in latchpins:
        GPIO.output(pin, GPIO.LOW)
        GPIO.output(pin, GPIO.HIGH)
        GPIO.output(pin, GPIO.LOW)


"""
Returns True if A1 and A2 have different values at any index, False otherwise.

Parameters:
    A1 (list): A list of integers.
    A2 (list): A list of integers.

Returns:
    bool: True if A1 and A2 have different values at any index, False otherwise.
"""
def matchingArrays(A1, A2):
    for i, thing in enumerate(A1):
        if A2[i] != thing:
            return True
    return False

"""
Clones the game board.

Returns:
    list: A copy of the game state.
"""
def cloneBoard():
    newboard = []
    for i, thing in enumerate(gameState):
        newboard.append([])
        for otherthing in thing:
            newboard[i].append(otherthing)
    return newboard

"""
Returns True if all the elements in the list are the same, False otherwise.

Parameters
----------
list : list
    A list of any type of objects.

Returns
-------
bool
    True if all the elements in the list are the same, False otherwise.

Examples
--------
>>> matchingRows([1, 1, 1, 1])
True
>>> matchingRows(['a', 'a', 'a', 'a'])
True
>>> matchingRows([1, 2, 3, 4])
False
>>> matchingRows(['a', 'b', 'c', 'd'])
False
"""
def matchingRows(list):
    if(list is None or len(list) == 0):
        return False
    firstElem = list[0]
    for thing in list:
        if thing != firstElem:
            return False
    return True

"""
Returns True if the row is blocked by both players.

Parameters:
row (list): A list of numbers representing the row to check.

Returns:
bool: True if the row is blocked by both players, False otherwise.
"""
def isRowBlocked(row):
    return PLAYER1_NUM in row and PLAYER2_NUM in row


#STARTUP
setup()
startGame()
