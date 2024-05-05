import sys
import pygame
from pynput.keyboard import Key, Controller
import keyboard

pygame.init()
pygame.joystick.init()

keyboard_presser = Controller()

joystick = pygame.joystick.Joystick(0)
joystick.init()

rumble_on = False
sub_rumble_on = False
switch_rumble = True
all_on = False

had_left = False
had_right = False

num_buttons = joystick.get_numbuttons()

enable_arrows = False

def toggle_arrows(e):
    global enable_arrows
    enable_arrows = not enable_arrows
    print("Arrows Enabled: {}".format(enable_arrows))

keyboard.on_press_key('space', toggle_arrows)

while True:
    for j in range(5):
        if rumble_on:
            # Start a rumble effect on the joystick 
            joystick.rumble(int(all_on or not sub_rumble_on), int(all_on or sub_rumble_on), 1000)
        
        for i in range(20):
            # Wait for the effect to finish
            pygame.time.wait(50)

            break_cycle = False
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    # print which button was pressed
                    print("Button Pressed: {}".format(event.button))

                    # Cross
                    if event.button == 0:
                        rumble_on = True
                        sub_rumble_on = False
                        switch_rumble = False
                        all_on = False
                    
                    # Triangle
                    if event.button == 3:
                        rumble_on = True
                        switch_rumble = False
                        sub_rumble_on = True
                        all_on = False
                    
                    # Square
                    if event.button == 2:
                        rumble_on = True
                        switch_rumble = True
                        all_on = False
                    
                    # Circle
                    if event.button == 1:
                        rumble_on = False
                        all_on = False
                    
                    # R1
                    if event.button == 10:
                        rumble_on = True
                        all_on = True
                    
                    break_cycle = True
                    break

                if enable_arrows:
                    # left key
                    left_stick_horizontal = joystick.get_axis(0)
                    right_stick_horizontal = joystick.get_axis(2)
                    left_stick_vertical = joystick.get_axis(1)
                    right_stick_vertical = joystick.get_axis(3)
                    if left_stick_horizontal < -0.5 or right_stick_horizontal < -0.5 or left_stick_vertical < -0.5 or right_stick_vertical < -0.5:
                        if not had_left:
                            had_left = True
                            print("Keyboard_presser: Left")
                            keyboard_presser.press(Key.left)
                            keyboard_presser.release(Key.left)
                    else:
                        had_left = False
                    
                    # right key
                    if left_stick_horizontal > 0.5 or right_stick_horizontal > 0.5 or left_stick_vertical > 0.5 or right_stick_vertical > 0.5:
                        if not had_right:
                            had_right = True
                            print("Keyboard_presser: Right")
                            keyboard_presser.press(Key.right)
                            keyboard_presser.release(Key.right)
                    else:
                        had_right = False

            if break_cycle:
                break

        # Stop the rumble effect
        joystick.stop_rumble()
        if break_cycle:
            break

    if switch_rumble:
        sub_rumble_on = not sub_rumble_on