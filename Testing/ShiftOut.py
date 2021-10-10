import RPi.GPIO as GPIO
from time import sleep

print("What is the latch pin?")
latchPin = int(input())
print("What is the Clock Pin?")
clockPin = int(input())
print("What is the data pin?")
dataPin = int(input())

print("What do you want to shift out?")
data = input().split()

GPIO.setmode(GPIO.BOARD)
GPIO.setup(dataPin, GPIO.OUT)
GPIO.setup(clockPin, GPIO.OUT)
GPIO.setup(latchPin, GPIO.OUT)

GPIO.output(latchPin, GPIO.LOW)
for bit in data:
    GPIO.output(dataPin, GPIO.HIGH if bit == "1" else GPIO.LOW)
    GPIO.output(clockPin, GPIO.LOW)
    GPIO.output(clockPin, GPIO.HIGH)
GPIO.output(latchPin, GPIO.HIGH)

input()
for bit in range(8):
    GPIO.output(dataPin, GPIO.LOW)
    GPIO.output(clockPin, GPIO.LOW)
    GPIO.output(clockPin, GPIO.HIGH)
GPIO.output(latchPin, GPIO.HIGH)
GPIO.cleanup()