import sys
import pygame
from pynput.keyboard import Key, Controller
import keyboard
import random

import os
os.environ['SDL_JOYSTICK_HIDAPI_PS4_RUMBLE'] = '1'

pygame.init()
pygame.joystick.init()

keyboard_presser = Controller()

joystick = pygame.joystick.Joystick(0)
joystick.init()

rumble_on = False
sub_rumble_on = False
pattern_index = 0
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

def reset_joystick():
    try:
        os.environ['SDL_JOYSTICK_HIDAPI_PS4_RUMBLE'] = '1'

        pygame.init()
        pygame.joystick.init()
        global joystick
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

        print("Reset Joystick")
    except:
        print("Failed to reset joystick")


pattern_periods = {
    0: 1200,   # heartbeat cycle length in ms
    1: 2000,   # wave cycle length
    2: 400,    # stutter cycle length
    3: 600,    # swap cycle length
    4: 200,    # strong/weak alternating pattern tick length
    5: 200,    # square pattern: same timing as L1, but strong/weak
}

pattern_names = {
    0: "Heartbeat",
    1: "Wave",
    2: "Stutter",
    3: "Swap",
    4: "Strong/Weak Alternating",
    5: "Strong/Weak Alternating (Square)",
}

# Weak vibration level used during the "off" phase of the square pattern
WEAK_LEVEL = 0.4

# Track state for the strong/weak alternating pattern
strong_active = False
last_switch_time = 0

def sample_pattern(index, current_time):
    global strong_active, last_switch_time

    period = pattern_periods[index]
    t = (current_time % period) / period  # normalized time [0,1]

    if index == 0:  # heartbeat
        if t < 0.2:
            return 1, 0
        elif t < 0.6:
            return 0, 1
        else:
            return 1, 1

    elif index == 1:  # wave
        import math
        strength = (math.sin(2 * math.pi * t) + 1) / 2
        return strength, strength

    elif index == 2:  # stutter
        if int(t * 10) % 2 == 0:
            return 1, 1
        else:
            return 0, 0

    elif index == 3:  # swap
        if t < 0.5:
            return 1, 0
        else:
            return 0, 1

    elif index == 4 or index == 5:  # strong/weak alternating (L1 timing)
        # If currently strong, small chance to stop each tick
        if strong_active:
            if random.random() < 0.20:
                print("Switching to weak")
                strong_active = False
                last_switch_time = current_time
        else:
            # Weak phase always short
            if (current_time - last_switch_time > 10000 or random.random() < 0.60):
                print("Switching to strong")
                strong_active = True
                last_switch_time = current_time

        if strong_active:
            return 1, 1  # very strong vibration
        elif index == 5:
            return WEAK_LEVEL, WEAK_LEVEL  # weak vibration (square pattern)
        else:
            return 0, 0  # no vibration

    return 0, 0



keyboard.on_press_key('f8', toggle_arrows)

while True:
    if sub_rumble_on:
        iterations = 4
    else:
        if pattern_index > 0:
            iterations = 1
        else:
            iterations = random.randint(5, 7)
    for j in range(iterations):
        if pattern_index > 0:
            current_time = pygame.time.get_ticks()
            left_motor, right_motor = sample_pattern(pattern_index, current_time)
            joystick.rumble(left_motor, right_motor, 1000)
        else:
            if rumble_on:
                # Start a rumble effect on the joystick 
                joystick.rumble(int(all_on or not sub_rumble_on), int(all_on or sub_rumble_on), 1000)
        
        for i in range(20):
            # Wait for the effect to finish
            pygame.time.wait(50)

            break_cycle = False
            try:
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
                            pattern_index = 0
                        
                        # Triangle
                        if event.button == 3:
                            rumble_on = True
                            switch_rumble = False
                            sub_rumble_on = True
                            all_on = False
                            break_cycle = True
                            pattern_index = 0
                        
                        # Square
                        if event.button == 2:
                            rumble_on = True
                            switch_rumble = False
                            all_on = False
                            break_cycle = True
                            pattern_index = 5
                            print("Selected Pattern: {}".format(pattern_names[pattern_index]))
                        
                        # Circle
                        if event.button == 1:
                            rumble_on = False
                            all_on = False
                            break_cycle = True
                            pattern_index = 0
                        
                        # R1
                        if event.button == 10:
                            rumble_on = True
                            all_on = True
                            break_cycle = True
                            pattern_index = 0
                        
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
                        # if event.button == 9 and enable_extra_controls:
                        #     # press Alt + Tab
                        #     keyboard_presser.press(Key.alt)
                        #     keyboard_presser.press(Key.tab)
                        #     keyboard_presser.release(Key.tab)
                        #     keyboard_presser.release(Key.alt)
                        if event.button == 9:
                            rumble_on = False
                            sub_rumble_on = False
                            switch_rumble = False
                            all_on = False
                            break_cycle = True
                            # pattern_index = random.randint(0, 3)
                            pattern_index = 4 # forcing pattern 4
                            print("Selected Pattern: {}".format(pattern_names[pattern_index]))

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

                    if event.type == pygame.JOYDEVICEADDED:
                        reset_joystick()
                        pygame.time.wait(1000)
            except:
                print("Error in event loop")

            if break_cycle:
                break

        # Stop the rumble effect
        joystick.stop_rumble()
        if break_cycle:
            break

    # switch with a chance (not using)
    if sub_rumble_on:
        chance = 1
    else:
        chance = 1
        
    if switch_rumble and random.random() < chance:
        sub_rumble_on = not sub_rumble_on