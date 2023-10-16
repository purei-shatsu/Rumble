import pygame

pygame.init()
pygame.joystick.init()

joystick = pygame.joystick.Joystick(0)
joystick.init()

rumble_on = False
sub_rumble_on = False
switch_rumble = True

num_buttons = joystick.get_numbuttons()

while True:
    for j in range(5):
        if rumble_on:
            # Start a rumble effect on the joystick
            joystick.rumble(int(not sub_rumble_on), int(sub_rumble_on), 1000)
        
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
                    
                    # Triangle
                    if event.button == 3:
                        rumble_on = True
                        switch_rumble = False
                        sub_rumble_on = True
                    
                    # Square
                    if event.button == 2:
                        rumble_on = True
                        switch_rumble = True
                    
                    # Circle
                    if event.button == 1:
                        rumble_on = False
                    
                    break_cycle = True
                    break
            
            if break_cycle:
                break

        # Stop the rumble effect
        joystick.stop_rumble()
        if break_cycle:
            break

    if switch_rumble:
        sub_rumble_on = not sub_rumble_on