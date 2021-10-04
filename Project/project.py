gameState = [[0,0,0],[0,0,0],[0,0,0]]

playerColors = [[True,False,False],[False,False,True]]
dataPin = 0
clockPin = 0
latchpins = []
markerPos = [1, 1]
gameInProgress = False

def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(dataPin, GPIO.OUT)
    GPIO.setup(clockPin, GPIO.OUT)
    for pin in latchpins:
        GPIO.setup(pin, GPIO.OUT)

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
    elif(matchingArrays(playerColors[0 if playerID == 1 else 1], newColor): 
        print("The other player is already this color, please select another color")
    else:
        playerColors[playerID] = newColor
        print("Successfully changed player " + str(playerID) + "'s color")

def matchingArrays(A1, A2):
    for i, thing in enumerate(A1):
        if A2[i] != thing:
            return True
    return False
