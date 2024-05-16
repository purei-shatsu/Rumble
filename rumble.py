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

enable_extra_controls = False

def toggle_arrows(e):
    global enable_extra_controls
    enable_extra_controls = not enable_extra_controls
    print("Arrows Enabled: {}".format(enable_extra_controls))

keyboard.on_press_key('f8', toggle_arrows)

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
                        break_cycle = True
                    
                    # Triangle
                    if event.button == 3:
                        rumble_on = True
                        switch_rumble = False
                        sub_rumble_on = True
                        all_on = False
                        break_cycle = True
                    
                    # Square
                    if event.button == 2:
                        rumble_on = True
                        switch_rumble = True
                        all_on = False
                        break_cycle = True
                    
                    # Circle
                    if event.button == 1:
                        rumble_on = False
                        all_on = False
                        break_cycle = True
                    
                    # R1
                    if event.button == 10:
                        rumble_on = True
                        all_on = True
                        break_cycle = True
                    
                    # RECTANGLE
                    if event.button == 15 and enable_extra_controls:
                        # Press Windows logo + Ctrl + O
                        keyboard_presser.press(Key.cmd)
                        keyboard_presser.press(Key.ctrl)
                        keyboard_presser.press('o')
                        keyboard_presser.release('o')
                        keyboard_presser.release(Key.ctrl)
                        keyboard_presser.release(Key.cmd)
                    
                    # L1
                    if event.button == 9 and enable_extra_controls:
                        # press Alt + Tab
                        keyboard_presser.press(Key.alt)
                        keyboard_presser.press(Key.tab)
                        keyboard_presser.release(Key.tab)
                        keyboard_presser.release(Key.alt)

                    if break_cycle:
                        break

                if enable_extra_controls:
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