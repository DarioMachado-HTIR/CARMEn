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
import csv

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
from carmen.utils import CARMEnPoint, CARMEnCheckpoint
from carmen.interface import CARMEnHUD
from carmen.controller import CARMEnControler

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

        traffic_manager = client.get_trafficmanager()

        display = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            pygame.HWSURFACE | pygame.DOUBLEBUF)
        
        panel = widgets.Panel(core.Grid((2, 10), (args.width, args.height)), None, None, (0, 0))

        new_hud = CARMEnHUD(args.width, args.height, __doc__, panel)
        
        start_point_list = []
        if args.filter.find("walker") != -1:
            start_point_list.append( CARMEnPoint(100.4, 299.8, 'player_start') )
        elif args.filter.find("vehicle") != -1:
            start_point_list.append( CARMEnPoint(59.6, 306.6, 'player_start') )

        new_session = CARMEnSession(carla_world = client.get_world()
                          , hud = new_hud
                          , actor_filter = args.filter
                          , player_start_list = start_point_list
                          , waypoints = False
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

        while True:
            new_clock.tick_busy_loop(120)
            if new_controller.parse_events(session = new_session
                                       , clock = new_clock
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
