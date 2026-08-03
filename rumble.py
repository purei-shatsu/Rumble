import sys
import math
import pygame
from pynput.keyboard import Key, Controller
from pynput.mouse import Button, Controller as MouseController
import keyboard
import random

import os
os.environ['SDL_JOYSTICK_HIDAPI_PS4_RUMBLE'] = '1'

pygame.init()
pygame.joystick.init()

keyboard_presser = Controller()
mouse_presser = MouseController()

def init_joysticks():
    js_list = []
    for i in range(pygame.joystick.get_count()):
        js = pygame.joystick.Joystick(i)
        js.init()
        js_list.append(js)
        print(f"  [{i}] {js.get_name()} (guid={js.get_guid()})")
    print(f"Initialized {len(js_list)} joystick(s)")
    return js_list

joysticks = init_joysticks()


def rumble_all(left, right, duration):
    for js in joysticks:
        try:
            js.rumble(left, right, duration)
        except Exception as e:
            print(f"rumble failed on {js.get_name()}: {e}")


def stop_rumble_all():
    for js in joysticks:
        try:
            js.stop_rumble()
        except Exception as e:
            print(f"stop_rumble failed on {js.get_name()}: {e}")

rumble_on = False
sub_rumble_on = False
pattern_index = 0
switch_rumble = True
all_on = False

TICK_MS = 20            # poll interval, kept at TICK_MS * TICKS_PER_CYCLE = rumble duration
TICKS_PER_CYCLE = 50
REPEAT_DELAY = 400      # ms held before a direction starts repeating
REPEAT_INTERVAL = 50    # ms between repeats afterwards
TRIGGER_THRESHOLD = 0.0 # L2/R2 axis value counted as pressed
MOUSE_DEADZONE = 0.15
MOUSE_SPEED = 14        # pixels per tick at full deflection

held_keys = {}

def press_held(key, name, active):
    if not active:
        held_keys.pop(key, None)
        return

    now = pygame.time.get_ticks()
    next_fire = held_keys.get(key)
    if next_fire is None:
        print("Keyboard_presser: {}".format(name))
        next_fire = now + REPEAT_DELAY
    elif now >= next_fire:
        next_fire = now + REPEAT_INTERVAL
    else:
        return

    keyboard_presser.press(key)
    keyboard_presser.release(key)
    held_keys[key] = next_fire


held_modifiers = {}

def hold_key(key, name, active):
    if active == held_modifiers.get(key, False):
        return

    if active:
        print("Keyboard_presser: {} down".format(name))
        keyboard_presser.press(key)
    else:
        print("Keyboard_presser: {} up".format(name))
        keyboard_presser.release(key)
    held_modifiers[key] = active


left_click_down = False

def set_left_click(active):
    global left_click_down
    if active == left_click_down:
        return

    if active:
        print("Mouse_presser: Left click down")
        mouse_presser.press(Button.left)
    else:
        mouse_presser.release(Button.left)
    left_click_down = active


def release_modifiers():
    for key in list(held_modifiers):
        hold_key(key, "modifier", False)
    set_left_click(False)


def axis_to_speed(value):
    if abs(value) < MOUSE_DEADZONE:
        return 0

    # rescale past the deadzone so motion eases in, then square it for fine control near centre
    scaled = (abs(value) - MOUSE_DEADZONE) / (1 - MOUSE_DEADZONE)
    return int(round(math.copysign(scaled * scaled * MOUSE_SPEED, value)))


def poll_axes():
    left_stick_horizontal = joysticks[0].get_axis(0)
    left_stick_vertical = joysticks[0].get_axis(1)

    press_held(Key.left, "Left", left_stick_horizontal < -0.5)
    press_held(Key.right, "Right", left_stick_horizontal > 0.5)
    press_held(Key.up, "Up", left_stick_vertical < -0.5)
    press_held(Key.down, "Down", left_stick_vertical > 0.5)

    move_x = axis_to_speed(joysticks[0].get_axis(2))
    move_y = axis_to_speed(joysticks[0].get_axis(3))
    if move_x or move_y:
        mouse_presser.move(move_x, move_y)

    # triggers rest at -1.0 and reach 1.0 fully pressed
    hold_key(Key.alt, "Alt", joysticks[0].get_axis(4) > TRIGGER_THRESHOLD)
    press_held(Key.tab, "Tab", joysticks[0].get_axis(5) > TRIGGER_THRESHOLD)

num_buttons = joysticks[0].get_numbuttons() if joysticks else 0

enable_extra_controls = True

def toggle_arrows(e):
    global enable_extra_controls
    enable_extra_controls = not enable_extra_controls
    if not enable_extra_controls:
        release_modifiers()
    print("Arrows Enabled: {}".format(enable_extra_controls))

def reset_joystick():
    try:
        os.environ['SDL_JOYSTICK_HIDAPI_PS4_RUMBLE'] = '1'

        pygame.init()
        pygame.joystick.init()
        global joysticks
        joysticks = init_joysticks()

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
    6: 200,    # triangle pattern: constant weak (the weak part of square)
}

pattern_names = {
    0: "Heartbeat",
    1: "Wave",
    2: "Stutter",
    3: "Swap",
    4: "Strong/Weak Alternating",
    5: "Strong/Weak Alternating (Square)",
    6: "Constant Weak (Triangle)",
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

    elif index == 6:  # constant weak (the weak part of square, never strong)
        return WEAK_LEVEL, WEAK_LEVEL

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
            rumble_all(left_motor, right_motor, 1000)
        else:
            if rumble_on:
                rumble_all(int(all_on or not sub_rumble_on), int(all_on or sub_rumble_on), 1000)
        
        for i in range(TICKS_PER_CYCLE):
            # Wait for the effect to finish
            pygame.time.wait(TICK_MS)

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
                            sub_rumble_on = False
                            all_on = False
                            break_cycle = True
                            pattern_index = 6
                            print("Selected Pattern: {}".format(pattern_names[pattern_index]))
                        
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
                        
                        # R3
                        if event.button == 8 and enable_extra_controls:
                            set_left_click(True)

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

                    if event.type == pygame.JOYBUTTONUP and event.button == 8:
                        set_left_click(False)

                    if event.type == pygame.JOYDEVICEADDED:
                        reset_joystick()
                        pygame.time.wait(1000)

                if enable_extra_controls:
                    poll_axes()
            except:
                print("Error in event loop")

            if break_cycle:
                break

        # Stop the rumble effect
        stop_rumble_all()
        if break_cycle:
            break

    # switch with a chance (not using)
    if sub_rumble_on:
        chance = 1
    else:
        chance = 1
        
    if switch_rumble and random.random() < chance:
        sub_rumble_on = not sub_rumble_on