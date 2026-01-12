#!/usr/bin/env python

# Copyright (c) 2019 Intel Labs
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# Allows controlling a vehicle with a keyboard. For a simpler and more
# documented example, please take a look at tutorial.py.

"""
Welcome to CARLA manual control with steering wheel Fanatec GT DD Pro 8NMm.

To drive start by preshing the brake pedal.
Change your wheel_config.ini according to your steering wheel.

To find out the values of your steering wheel use jstest-gtk in Ubuntu.

"""

from __future__ import print_function


# ==============================================================================
# -- find carla module ---------------------------------------------------------
# ==============================================================================


import glob
import os
import sys

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass


# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================


import carla

from carla import ColorConverter as cc

from carmen.session import CARMEnSession
from carmen.interface import CARMEnHUD
from carmen.controller import CARMEnControler
from carmen.utils import CARMEnPoint, CARMEnCheckpoint

import argparse
import datetime
import logging

try:
    import pygame    
          
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

import PyGameWidgets.widgets as widgets
import PyGameWidgets.core as core



# ==============================================================================
# -- game_loop() ---------------------------------------------------------------
# ==============================================================================


def game_loop(args):
    os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"
    pygame.init()
    pygame.font.init()
    new_session = None
    road_id_list_for_ref = []
    lane_id_for_ref = []

    WINDOW_WIDTH = args.width
    WINDOW_HEIGHT = args.height

    try:      
        client = carla.Client(args.host, args.port)
        client.set_timeout(2.0)

        if not args.filter.find("walker") != -1:
            print("Not a Walker! Cancel Session!")
            return

        #traffic_manager = client.get_trafficmanager()

        display = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            pygame.HWSURFACE | pygame.DOUBLEBUF)
        
        panel = widgets.Panel(core.Grid((2, 10), (args.width, args.height)), None, None, (0, 0))

        new_hud = CARMEnHUD(args.width, args.height, __doc__, panel)

        '''use_keyboard = input("Use Keyboard? (Y/N): ")
        if use_keyboard == 'Y' or use_keyboard == 'y':
            keycontrol = True
            joycontrol = False
        elif use_keyboard == 'N' or use_keyboard == 'n':
            keycontrol = False
            use_joystick = input("Use Joystick ? (Y/N): ")
            if use_joystick == 'Y' or use_joystick == 'y':
                joycontrol = True
            elif use_joystick == 'N' or use_joystick == 'n':
                joycontrol = False'''

        subject_id = input("Insert subject ID (SXX): ")

        start_point_list = []
        start_point_list.append( CARMEnPoint(52.40, -50.65, 'player_start') )
        start_point_list.append( CARMEnPoint(34.46, -50.65, 'player_start_check1') )
        start_point_list.append( CARMEnPoint(12.41, -44.22, 'player_start_check2') )
        start_point_list.append( CARMEnPoint(-5.23, -26.58, 'player_start_check3') )
        start_point_list.append( CARMEnPoint(-23.25, -11.10, 'player_start_check4') )
        start_point_list.append( CARMEnPoint(-39.08, 6.70, 'player_start_check5') )
        start_point_list.append( CARMEnPoint(-54.08, 24.33, 'player_start_check6') )
        start_point_list.append( CARMEnPoint(38.45, -50.65, 'player_start_check7') )
        
        road_id_list_for_ref = [10, 32, 24, 23, 33, 59, 37, 35, 25, 15, 3, 43, 13, 2, 26]
        lane_id_for_ref = -1

        #save_directory = 'C:\\carla\\Unreal\\CarlaUE4\\Data\\'
        save_directory = 'C:\\Users\\Sistemas\\Documents\\OpenSignals (r)evolution\\files\\'

        new_session = CARMEnSession(carla_world = client.get_world()
                          , hud = new_hud
                          , actor_filter = args.filter
                          , player_start_list = start_point_list
                          , subject = subject_id
                          , directory = save_directory
                          , waypoints = True
                          , draw = False
                          , road_width = 3.4
                          , road_id_list = road_id_list_for_ref
                          , lane_id = lane_id_for_ref
                          )

        new_controller = CARMEnControler(start_in_autopilot = args.autopilot
                                 , keyboard_control = args.keycontrol
                                 , joystick_control = args.joycontrol
                                 , walker_speed = 1.277
                                 , walker_lateral_speed = 1.277
                                 , walker_turn_speed = 0.01
                                 )

        new_clock = pygame.time.Clock()

        # Possible spanw directions: 80% front, 20% back, 50/50 left-right
        direction_pools = []
        #cond_70F_30B = ["FR"]
        cond_70F_30B = ["FL", "FL", "FR", "FR", "BL", "BR"]
        direction_pools.append(cond_70F_30B)
        cond_70B_30F = ["BL", "BL", "BR", "BR", "FL", "FR"]
        direction_pools.append(cond_70B_30F)

        # Set checkpoints in the road for the pedestrian
        checkpoint_list = []
        checkpoint_list.append(CARMEnCheckpoint(session=new_session
                                 , desired_point = CARMEnPoint(32.8, -50.6, 'checkpoint1')
                                 , spawns_vehicle_when_reached = True
                                 , desired_spawn_back_left = CARMEnPoint(55.65, -48.94, 'checkpoint1_BL', -1)
                                 , desired_spawn_back_right = CARMEnPoint(55.65, -52.34, 'checkpoint1_BR', 1)
                                 , desired_spawn_front_left = CARMEnPoint(-5.77, -23.61, 'checkpoint1_FL', -1)
                                 , desired_spawn_front_right = CARMEnPoint(-8.18, -26.02, 'checkpoint1_FR', 1)
                                 )
        )
        
        checkpoint_list.append(CARMEnCheckpoint(session=new_session
                                 , desired_point = CARMEnPoint(10.85, -42.65, 'checkpoint2')
                                 , spawns_vehicle_when_reached = True
                                 , desired_spawn_back_left = CARMEnPoint(29.73, -48.40, 'checkpoint2_BL', -1)
                                 , desired_spawn_back_right = CARMEnPoint(28.57, -51.58, 'checkpoint2_BR', 1)
                                 , desired_spawn_front_left = CARMEnPoint(-24.39, -7.58, 'checkpoint2_FL', -1)
                                 , desired_spawn_front_right = CARMEnPoint(-26.78, -9.97, 'checkpoint2_FR', 1)
                                 )
        )
        
        checkpoint_list.append(CARMEnCheckpoint(session=new_session
                                 , desired_point = CARMEnPoint(-6.52, -25.25, 'checkpoint3')
                                 , spawns_vehicle_when_reached = True
                                 , desired_spawn_back_left = CARMEnPoint(8.83, -38.23, 'checkpoint3_BL', -1)
                                 , desired_spawn_back_right = CARMEnPoint(6.45, -40.61, 'checkpoint3_BR', 1)
                                 , desired_spawn_front_left = CARMEnPoint(-41.94, 10.64, 'checkpoint3_FL', -1)
                                 , desired_spawn_front_right = CARMEnPoint(-43.70, 7.73, 'checkpoint3_FR', 1)
                                 )
        )
        
        checkpoint_list.append(CARMEnCheckpoint(session=new_session
                                 , desired_point = CARMEnPoint(-24.43, -9.94, 'checkpoint4')
                                 , spawns_vehicle_when_reached = True
                                 , desired_spawn_back_left = CARMEnPoint(-9.34, -21.14, 'checkpoint3_BL', -1)
                                 , desired_spawn_back_right = CARMEnPoint(-10.69, -24.26, 'checkpoint4_BR', 1)
                                 , desired_spawn_front_left = CARMEnPoint(-53.31, 28.52, 'checkpoint4_FL', 1)
                                 , desired_spawn_front_right = CARMEnPoint(-56.70, 28.43, 'checkpoint4_FR', -1)
                                 )
        )
        
        checkpoint_list.append(CARMEnCheckpoint(session=new_session
                                 , desired_point = CARMEnPoint(-40.28, 7.45, 'checkpoint5')
                                 , spawns_vehicle_when_reached = True
                                 , desired_spawn_back_left = CARMEnPoint(-25.50, -6.47, 'checkpoint5_BL', 1)
                                 , desired_spawn_back_right = CARMEnPoint(-27.89, -8.86, 'checkpoint5_BR', -1)
                                 , desired_spawn_front_left = CARMEnPoint(-42.22, 51.35, 'checkpoint5_FL', 1)
                                 , desired_spawn_front_right = CARMEnPoint(-45.31, 52.76, 'checkpoint5_FR', -1)
                                 )
        )
        
        checkpoint_list.append(CARMEnCheckpoint(session=new_session
                                 , desired_point = CARMEnPoint(-54.53, 25.43, 'checkpoint6')
                                 , spawns_vehicle_when_reached = True
                                 , desired_spawn_back_left = CARMEnPoint(-42.66, 11.08, 'checkpoint6_BL', 1)
                                 , desired_spawn_back_right = CARMEnPoint(-44.42, 8.16, 'checkpoint6_BR', 1)
                                 , desired_spawn_front_left = CARMEnPoint(-33.19, 70.21, 'checkpoint6_FL', -1)
                                 , desired_spawn_front_right = CARMEnPoint(-36.79, 71.82, 'checkpoint6_FR', -1)
                                 )
        )
        
        checkpoint_list.append(CARMEnCheckpoint(session=new_session
                            , desired_point = CARMEnPoint(-45.54, 48.19, 'end_checkpoint')
                            )
        )

        new_session.set_checkpoints(checkpoint_list, direction_pools)

        while True:
            new_clock.tick_busy_loop(120)
            if new_controller.parse_events(session = new_session
                                       , clock = new_clock
                                       , left_threshold = 3.45
                                       , right_threshold = 0.45
                                       ):
                return
            new_session.tick(new_clock, args)
            new_session.render(display)
            pygame.display.flip()

    finally:
        print('\nClosed by User. Bye!')
        if args.rec:
            print('\nRecording Stoppped. Closing file.')
            # close the file
            args.f.close()
        if new_session is not None:
            new_session.destroy()

        pygame.quit()


def exit_program():
    print("Exiting the program...")
    sys.exit(0)



# ==============================================================================
# -- main() --------------------------------------------------------------------
# ==============================================================================


def main():
    argparser = argparse.ArgumentParser(
        description='CARLA Manual Control Client')
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='debug',
        help='print debug information')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-a', '--autopilot',
        action='store_true',
        help='enable autopilot')
    argparser.add_argument(
        '-k', '--keycontrol',
        action='store_true',
        help='keyboard control')
    argparser.add_argument(
        '-j', '--joycontrol',
        action='store_true',
        help='joystick control')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='440x720',
        help='window resolution (default: 440x720)')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='walker.pedestrian.0052',
        help='actor filter (default: "walker.pedestrian.0052")')
    argparser.add_argument(
        '--rec',
        action='store_true',
        help='record vehicle stats')
    argparser.add_argument(
        '--subject',
        metavar='SUBJECT',
        default='00',
        help='subject number (XX)')
    args = argparser.parse_args()

    args.width, args.height = [int(x) for x in args.res.split('x')]

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.info('listening to server %s:%s', args.host, args.port)

    print(__doc__)

    try:
        game_loop(args)

    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')


if __name__ == '__main__':

    main()
