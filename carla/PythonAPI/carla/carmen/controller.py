#!/usr/bin/env python

# Controler module for CARMEn
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.



# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================

import carla

import sys
import math

if sys.version_info >= (3, 0):
    from configparser import ConfigParser
else:
    from ConfigParser import RawConfigParser as ConfigParser

try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import KMOD_SHIFT
    from pygame.locals import K_0
    from pygame.locals import K_9
    from pygame.locals import K_BACKQUOTE
    from pygame.locals import K_BACKSPACE
    from pygame.locals import K_COMMA
    from pygame.locals import K_DOWN
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_F1
    from pygame.locals import K_LEFT
    from pygame.locals import K_PERIOD
    from pygame.locals import K_RIGHT
    from pygame.locals import K_SLASH
    from pygame.locals import K_SPACE
    from pygame.locals import K_TAB
    from pygame.locals import K_UP
    from pygame.locals import K_a
    from pygame.locals import K_c
    from pygame.locals import K_d
    from pygame.locals import K_h
    from pygame.locals import K_m
    from pygame.locals import K_p
    from pygame.locals import K_q
    from pygame.locals import K_r
    from pygame.locals import K_s
    from pygame.locals import K_w
    from pygame.locals import K_j
    from pygame.locals import K_l
    from pygame.locals import K_PAGEUP              
    from pygame.locals import K_PAGEDOWN              
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')


# ==============================================================================
# -- Classes -------------------------------------------------------------------
# ==============================================================================


class CARMEnControler(object):
    
    def __init__(self, start_in_autopilot, keyboard_control, joystick_control, walker_speed, walker_lateral_speed, walker_turn_speed):

        self._autopilot_enabled = start_in_autopilot
        self.keyboard_control = keyboard_control
        self.joystick_control = joystick_control
        self.walker_speed = walker_speed
        self.walker_lateral_speed = walker_lateral_speed
        self.walker_turn_speed = walker_turn_speed
        self.end_session = False

        if not self.keyboard_control:
            # initialize steering wheel
            pygame.joystick.init()

            #create empty list to store joysticks
            joysticks = []

            #event handler
            for event in pygame.event.get():
                if event.type == pygame.JOYDEVICEADDED:
                    joy = pygame.joystick.Joystick(event.device_index)
                    joysticks.append(joy)

            #show number of connected joysticks
            print("\nControllers: " + str(pygame.joystick.get_count()))
            for joystick in joysticks:
                print("Controller Type: " + str(joystick.get_name()))
                print("Number of axes: " + str(joystick.get_numaxes()))
            print("\n")
            
            joystick_count = pygame.joystick.get_count()
            if not joystick_control:
                if joystick_count > 2:
                    raise ValueError("Please Connect Just One Steering Wheel")

                self._joystickAxes = pygame.joystick.Joystick(1)
                self._joystickAxes.init()
                self._joystickButtons = pygame.joystick.Joystick(0)
                self._joystickButtons.init()

                self._parser = ConfigParser()
                self._parser.read(r'C:\carla\wheel_config.ini')

                self._steer_idx = int(
                    self._parser.get('GT DD Pro 8Nm Racing Wheel', 'steering_wheel'))
                self._throttle_idx = int(
                    self._parser.get('GT DD Pro 8Nm Racing Wheel', 'throttle'))
                self._brake_idx = int(
                    self._parser.get('GT DD Pro 8Nm Racing Wheel', 'brake'))
                self._handbrake_down_idx = int(
                    self._parser.get('GT DD Pro 8Nm Racing Wheel', 'handbrake_down'))
                self._handbrake_up_idx = int(
                    self._parser.get('GT DD Pro 8Nm Racing Wheel', 'handbrake_up'))
                self._manual_gear_shift_idx = int(
                    self._parser.get('GT DD Pro 8Nm Racing Wheel', 'manual_gear_shift'))
                self._gear_down_idx = int(
                    self._parser.get('GT DD Pro 8Nm Racing Wheel', 'gear_down'))
                self._gear_up_idx = int(
                    self._parser.get('GT DD Pro 8Nm Racing Wheel', 'gear_up'))
                self._ad_idx = int(
                    self._parser.get('GT DD Pro 8Nm Racing Wheel', 'ad'))
            
            else:
                if joystick_count > 1:
                    raise ValueError("Please Connect Just One Joystick")

                self._joystickAxes = pygame.joystick.Joystick(0)
                self._joystickAxes.init()
                self._joystickButtons = pygame.joystick.Joystick(0)
                self._joystickButtons.init()

                self._parser = ConfigParser()
                self._parser.read(r'C:\carla\joystick_config.ini')

                JOYSTICK_MODEL = 'Saitek Pro Flight X-56 Rhino Stick'
                #JOYSTICK_MODEL = 'Xbox One For Windows'

                self._speed_idx = int(
                    self._parser.get(JOYSTICK_MODEL, 'long_speed'))
                self._lat_speed_idx = int(
                    self._parser.get(JOYSTICK_MODEL, 'lateral_speed'))
                self._turn_yaw_idx = int(
                    self._parser.get(JOYSTICK_MODEL, 'turn_yaw'))
            
        else:
            print("Keyboard control selected!")

    def set_new_player_controller(self, session):
        
        if isinstance(session.player, carla.Vehicle):
            self._control = carla.VehicleControl()
            session.player.set_autopilot(self._autopilot_enabled)
        elif isinstance(session.player, carla.Walker):
            self._control = carla.WalkerControl()
            self._autopilot_enabled = False
            self._rotation = session.player.get_transform().rotation
            self._strafe = 0.0
        else:
            raise NotImplementedError("Actor type not supported")
        self._steer_cache = 0.0
        session.hud.notification("Press 'H' or '?' for help.", seconds=4.0)


    def parse_events(self, session, clock, left_threshold=None, right_threshold=None, checkpoints=None):
        for event in pygame.event.get():
            for b in session.hud.buttons:
                if session.run is None or b.text.value == "        Stop Run":
                    b.on_click(event, lambda: session.hud.button_pressed(b))
                    b.on_release(event, lambda: session.hud.button_released(b, session, self))
            for opt in session.hud.opts:
                if session.run is None:
                    opt.activate(event)
                    opt.on_change(event, lambda: session.hud.option_changed(opt))
            if event.type == pygame.QUIT or self.end_session:
                return True
            #if event.type == pygame.JOYBUTTONDOWN and session.run is not None:
            #    if abs(event.dict['value']) > 0.1:
            #        print(f"Axis: {event.dict['axis']} = {event.dict['value']}")
            if event.type == pygame.JOYBUTTONDOWN and session.run is not None:
                if session.run.stop:
                    break
                #elif event.button == 0:
                #    session.restart()
                #elif event.button == 1:
                #    session.hud.toggle_info()
                #elif event.button == 2:
                #    session.camera_manager.toggle_camera()
                #elif event.button == 3:
                #    session.next_weather()
                if isinstance(self._control, carla.VehicleControl):
                    if event.button == self._manual_gear_shift_idx:
                        self._control.manual_gear_shift = not self._control.manual_gear_shift
                        self._control.gear = session.player.get_control().gear
                        session.hud.notification('%s Transmission' %
                                                ('Manual' if self._control.manual_gear_shift else 'Automatic'))
                    elif self._control.manual_gear_shift and event.button == self._gear_down_idx:
                        self._control.gear = max(-1, self._control.gear - 1)
                    elif self._control.manual_gear_shift and event.button == self._gear_up_idx:
                        self._control.gear = self._control.gear + 1
                    elif not self._control.manual_gear_shift and event.button == self._gear_up_idx and self._control.reverse:
                        self._control.gear = 1
                    elif not self._control.manual_gear_shift and event.button == self._gear_down_idx and not self._control.reverse:
                        self._control.gear = -1
                    elif event.button == 23:
                        session.camera_manager.next_sensor()        
                    elif event.button == self._handbrake_down_idx:
                        self._control.hand_brake = False
                    elif event.button == self._handbrake_up_idx:
                        self._control.hand_brake = True
                    elif event.button == self._ad_idx:
                        self._autopilot_enabled = not self._autopilot_enabled
                        session.player.set_autopilot(self._autopilot_enabled)
                        session.hud.notification('Autopilot %s' % ('On' if self._autopilot_enabled else 'Off'))

            elif event.type == pygame.KEYUP and session.run is not None:
                #print("keyboard")
                if session.run.stop:
                    break
                elif self._is_quit_shortcut(event.key):
                    return True
                #elif event.key == K_BACKSPACE:
                #    session.restart()
                #elif event.key == K_F1:
                #    session.hud.toggle_info()
                #elif event.key == K_h or (event.key == K_SLASH and pygame.key.get_mods() & KMOD_SHIFT):
                #    session.hud.help.toggle()
                #elif event.key == K_TAB:
                #    session.camera_manager.toggle_camera()
                #elif event.key == K_c and pygame.key.get_mods() & KMOD_SHIFT:
                #    session.next_weather(reverse=True)
                #elif event.key == K_c:
                #    session.next_weather()
                #elif event.key == K_BACKQUOTE:
                #    session.camera_manager.next_sensor()
                #elif event.key > K_0 and event.key <= K_9:
                #    session.camera_manager.set_sensor(event.key - 1 - K_0)
                #elif event.key == K_r:
                #    session.camera_manager.toggle_recording()
                if isinstance(self._control, carla.VehicleControl):
                    if event.key == K_q:
                        self._control.gear = 1 if self._control.reverse else -1
                    elif event.key == K_m:
                        self._control.manual_gear_shift = not self._control.manual_gear_shift
                        self._control.gear = session.player.get_control().gear
                        session.hud.notification('%s Transmission' %
                                            ('Manual' if self._control.manual_gear_shift else 'Automatic'))
                    elif self._control.manual_gear_shift and event.key == K_COMMA:
                        self._control.gear = max(-1, self._control.gear - 1)
                    elif self._control.manual_gear_shift and event.key == K_PERIOD:
                        self._control.gear = self._control.gear + 1
                    elif event.key == K_p:
                        self._autopilot_enabled = not self._autopilot_enabled
                        session.player.set_autopilot(self._autopilot_enabled)
                        session.hud.notification('Autopilot %s' % ('On' if self._autopilot_enabled else 'Off'))
                    elif event.key == K_PAGEDOWN:
                        self._control.hand_brake = False
                    elif event.key == K_PAGEUP:
                        self._control.hand_brake = True

        if not self._autopilot_enabled and session.run is not None:
            if isinstance(self._control, carla.VehicleControl):
                if self.keyboard_control:
                    self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
                else:
                    self._parse_vehicle_wheel()
                self._control.reverse = self._control.gear < 0
            elif isinstance(self._control, carla.WalkerControl):
                if self.keyboard_control:
                    self._parse_walker_keys(pygame.key.get_pressed(), clock.get_time(), session, self.walker_speed, self.walker_lateral_speed, self.walker_turn_speed, left_threshold, right_threshold)
                else:
                    self._parse_walker_joy(clock.get_time(), session, self.walker_speed, self.walker_lateral_speed, self.walker_turn_speed, left_threshold, right_threshold)
            session.player.apply_control(self._control)

    def _parse_vehicle_keys(self, keys, milliseconds):
        self._control.throttle = 1.0 if keys[K_UP] or keys[K_w] else 0.0
        steer_increment = 5e-4 * milliseconds
        if keys[K_LEFT] or keys[K_a]:
            self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        self._steer_cache = min(0.7, max(-0.7, self._steer_cache))
        self._control.steer = round(self._steer_cache, 1)
        self._control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
        self._control.hand_brake = keys[K_SPACE]


    def _parse_vehicle_wheel(self):
        numAxes = self._joystickAxes.get_numaxes()
        jsInputs = [float(self._joystickAxes.get_axis(i)) for i in range(numAxes)]
        #print (jsInputs)
        jsButtons = [float(self._joystickButtons.get_button(i)) for i in
                     range(self._joystickButtons.get_numbuttons())]
        #print (jsButtons)

        # Custom function to map range of inputs [1, -1] to outputs [0, 1] i.e 1 from inputs means nothing is pressed
        # For the steering, it seems fine as it is
        K1 = 1.0  # 0.55
        #steerCmd = K1 * math.tan(1.1 * jsInputs[self._steer_idx])
        steerCmd = K1 * jsInputs[self._steer_idx] #K1 is steering ratio
        #print(str(jsInputs[self._steer_idx]) + " > " + str(steerCmd), end='\r')
        
        K2 = 1.6  # 1.6
        throttleCmd = K2 + (2.05 * math.log10(
            -0.7 * jsInputs[self._throttle_idx] + 1.4) - 1.2) / 0.92
        if throttleCmd <= 0:
            throttleCmd = 0
        elif throttleCmd > 1:
            throttleCmd = 1
        # removes edge case at the start
        if jsInputs[self._throttle_idx] == 0.0:
            throttleCmd = 0.0

        brakeCmd = 1.6 + (2.05 * math.log10(
            -0.7 * jsInputs[self._brake_idx] + 1.4) - 1.2) / 0.92
        if brakeCmd <= 0:
            brakeCmd = 0
        elif brakeCmd > 1:
            brakeCmd = 1
        # removes edge case at the start
        if jsInputs[self._brake_idx] == 0.0:
            brakeCmd = 0.0

        self._control.steer = steerCmd
        self._control.brake = brakeCmd
        self._control.throttle = throttleCmd


    def _parse_walker_keys(self, keys, milliseconds, session, walking_speed=1.6, lateral_speed=0.8, turn_speed=0.08, left_threshold=None, right_threshold=None):
        
        # Pedestrian is stopped by default
        self._control.speed = 0.0
        
        # If Run stopped, no longer control the pedestrian
        if session.run.stop:
            return
        
        # Get Stop Button
        if keys[K_s]:
            self._control.speed = 0.0
        
         # Get Yaw Buttons
        if keys[K_LEFT]:
            self._control.speed = .01
            self._rotation.yaw -= turn_speed * milliseconds
        if keys[K_RIGHT]:
            self._control.speed = .01
            self._rotation.yaw += turn_speed * milliseconds
        
        # Get Lateral Speed Buttons
        if keys[K_a] or keys[K_d]:
            # Get walker transform
            t = session.player.get_transform()
            # Get lateral speed vector
            lat_speed = - float(keys[K_a]) * lateral_speed/1000 * milliseconds + \
                float(keys[K_d]) * lateral_speed/1000 * milliseconds
            v_right =  lat_speed * t.get_right_vector()
            # Get new pos from lateral speed vector
            pos = session.player.get_location()
            pos_new = carla.Location(pos.x + v_right.x, pos.y + v_right.y, pos.z + v_right.z)
            # Apply new position
            session.player.set_location(pos_new)
        
        # Get Front Speed Button
        if keys[K_w]:
            self._control.speed = walking_speed
        
        # Set actor direction
        self._rotation.yaw = round(self._rotation.yaw, 1)
        self._control.direction = self._rotation.get_forward_vector()

    def _parse_walker_joy(self, milliseconds, session, walking_speed=1.6, lateral_speed=0.8, turn_speed=0.08, left_threshold=None, right_threshold=None):

        # Pedestrian is stopped by default
        self._control.speed = 0.0
        
        # If Run stopped, no longer control the pedestrian
        if session.run.stop:
            return
        
        # Get Joystick Axis
        numAxes = self._joystickAxes.get_numaxes()
        jsInputs = [float(self._joystickAxes.get_axis(i)) for i in range(numAxes)]

        # Remove Analog Stick Noise
        noise_threshold = 0.1
        
        if jsInputs[self._speed_idx] > noise_threshold:
            jsInputs[self._speed_idx] = ( jsInputs[self._speed_idx] - noise_threshold ) / ( 1 - noise_threshold )
        elif jsInputs[self._speed_idx] < -noise_threshold:
            jsInputs[self._speed_idx] = ( jsInputs[self._speed_idx] + noise_threshold ) / ( 1 - noise_threshold )
        else:
            jsInputs[self._speed_idx] = 0
        
        if jsInputs[self._lat_speed_idx] > noise_threshold:
            jsInputs[self._lat_speed_idx] = ( jsInputs[self._lat_speed_idx] - noise_threshold ) / ( 1 - noise_threshold )
        elif jsInputs[self._lat_speed_idx] < -noise_threshold:
            jsInputs[self._lat_speed_idx] = ( jsInputs[self._lat_speed_idx] + noise_threshold ) / ( 1 - noise_threshold )
        else:
            jsInputs[self._lat_speed_idx] = 0
        
        if jsInputs[self._turn_yaw_idx] > 3*noise_threshold:
            jsInputs[self._turn_yaw_idx] = ( jsInputs[self._turn_yaw_idx] - 3*noise_threshold ) / ( 1 - 3*noise_threshold )
        elif jsInputs[self._turn_yaw_idx] < -3*noise_threshold:
            jsInputs[self._turn_yaw_idx] = ( jsInputs[self._turn_yaw_idx] + 3*noise_threshold ) / ( 1 - 3*noise_threshold )
        else:
            jsInputs[self._turn_yaw_idx] = 0
        
        # Invert Front Axis
        jsInputs[self._speed_idx] = -jsInputs[self._speed_idx]

        # Smooth analog sticks with analog noise
        #jsInputs[self._turn_yaw_idx] = 2 * ( 1 / ( 1 + math.exp(-5*jsInputs[self._turn_yaw_idx]) ) - 0.5 )

        # Print Values (DEBUG)
        #if jsInputs[self._speed_idx] != 0 or jsInputs[self._lat_speed_idx] != 0 or jsInputs[self._turn_yaw_idx] != 0:
        #    print(f"Speed: {round(jsInputs[self._speed_idx],2)}, Lat Speed: {round(jsInputs[self._lat_speed_idx],2)}, Yaw: {round(jsInputs[self._turn_yaw_idx],2)}") 

        # Get Stop Axis
        if jsInputs[self._speed_idx] < 0:
            self._control.speed = 0
        
        # Get Yaw Axis
        if abs(jsInputs[self._turn_yaw_idx]) > 0:
            self._control.speed = .01
            self._rotation.yaw += jsInputs[self._turn_yaw_idx] * turn_speed * milliseconds

        # Get Lateral Speed Axis
        if abs(jsInputs[self._lat_speed_idx]) > 0:
            # Get walker transform 
            t = session.player.get_transform()    
            # Get lateral speed vector
            lat_speed = jsInputs[self._lat_speed_idx] * lateral_speed/1000 * milliseconds
            v_right =  lat_speed * t.get_right_vector()
            # Get new pos from lateral speed vector
            pos = session.player.get_location()
            pos_new = carla.Location(pos.x + v_right.x, pos.y + v_right.y, pos.z + v_right.z)
            # Apply new position
            session.player.set_location(pos_new)
        
        # Get Front Speed Axis
        if jsInputs[self._speed_idx] > 0:
            self._control.speed = walking_speed * jsInputs[self._speed_idx]
        
        # Set actor direction
        self._rotation.yaw = round(self._rotation.yaw, 2)
        #print(self._rotation.yaw)
        self._control.direction = self._rotation.get_forward_vector()

    @staticmethod
    def _is_quit_shortcut(key):
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)
