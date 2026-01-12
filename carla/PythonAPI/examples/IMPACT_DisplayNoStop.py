#!/usr/bin/env python

# Copyright (c) 2018 Intel Labs.
# authors: German Ros (german.ros@intel.com)
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""Example of automatic vehicle control from client side."""

from __future__ import print_function

import argparse
import glob
import logging
import os
import numpy.random as random
import sys
import time

# ==============================================================================
# -- Find CARLA module ---------------------------------------------------------
# ==============================================================================
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

# ==============================================================================
# -- Add PythonAPI for release mode --------------------------------------------
# ==============================================================================
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/carla')
except IndexError:
    pass

import carla
from carla import ColorConverter as cc

from agents.navigation.behavior_agent import BehaviorAgent  # pylint: disable=import-error
from agents.navigation.basic_agent import BasicAgent  # pylint: disable=import-error
from agents.navigation.constant_velocity_agent import ConstantVelocityAgent  # pylint: disable=import-error


# ==============================================================================
# -- Global functions ----------------------------------------------------------
# ==============================================================================

def get_actor_blueprints(world, filter, generation):
    bps = []

    blueprints_nissan = [bp for bp in world.get_blueprint_library().filter('nissan')]
    for bp in blueprints_nissan:
        bps.append(bp)

    blueprints_audi = [bp for bp in world.get_blueprint_library().filter('audi')]
    for bp in blueprints_audi:
        bps.append(bp)
    
    blueprints_bmw = [bp for bp in world.get_blueprint_library().filter('bwm')]
    for bp in blueprints_bmw:
        bps.append(bp)

    return bps

    '''bps = world.get_blueprint_library().filter('nissan')

    if generation.lower() == "all":
        return bps

    # If the filter returns only one bp, we assume that this one needed
    # and therefore, we ignore the generation
    if len(bps) == 1:
        return bps

    try:
        int_generation = int(generation)
        # Check if generation is in available generations
        if int_generation in [1, 2, 3]:
            bps = [x for x in bps if int(x.get_attribute('generation')) == int_generation]
            return bps
        else:
            print("   Warning! Actor Generation is not valid. No actor will be spawned.")
            return []
    except:
        print("   Warning! Actor Generation is not valid. No actor will be spawned.")
        return []'''
    

# ==============================================================================
# -- Game Loop ---------------------------------------------------------
# ==============================================================================


def spawn_vehicle(world, vehicle, route, speed):
    # Get blueprint.
    blueprint = world.get_blueprint_library().find(vehicle)
    blueprint.set_attribute('role_name', 'hero')

    vehicle = world.try_spawn_actor(blueprint, route[0])

    #agent = BehaviorAgent(vehicle, behavior=args.behavior)
    agent = BasicAgent(vehicle, speed)
    agent.set_target_speed(speed)
    agent.follow_speed_limits(False)
    agent.ignore_traffic_lights(True)
    agent.ignore_stop_signs(True)

    start_location = route[0].location
    end_location = route[1].location
    agent.set_destination(end_location, start_location)

    return vehicle, agent

def spawn_walker(world, walker_bp, route):
    # Get blueprint.
    #walker_bp = world.get_blueprint_library().find(pedestrian)
    #walker_speed = walker_bp.get_attribute('speed').recommended_values[1]
    pedestrian_bp = random.choice(world.get_blueprint_library().filter('*walker.pedestrian*'))
    walker = world.spawn_actor(pedestrian_bp, route[0])

    world.wait_for_tick()

    controller_bp = world.get_blueprint_library().find('controller.ai.walker')
    controller = world.try_spawn_actor(controller_bp, walker.get_transform(), walker)

    controller.start()
    controller.go_to_location(route[1].location)
    controller.set_max_speed(1 + random.random())  # Between 1 and 2 m/s (default is 1.4 m/s)

    return walker, controller


def game_loop(args):    
    """
    Main loop of the simulation. It handles updating all the HUD information,
    ticking the agent and, if needed, the world.
    """

    try:
        vehicles_list = []
        walkers_list = []
        all_id = []

        client = carla.Client(args.host, args.port)
        client.set_timeout(60.0)

        traffic_manager = client.get_trafficmanager()
        world = client.get_world()

        blueprint_list = get_actor_blueprints(world, args.filter, args.generation)
        if not blueprint_list:
            raise ValueError("Couldn't find any blueprints with the specified filters")
        blueprintsWalkers = get_actor_blueprints(world, args.filterw, args.generationw)
        if not blueprintsWalkers:
            raise ValueError("Couldn't find any walkers with the specified filters")
        #for b in blueprintsWalkers:
        #    print(b.actor_id)

        start = False
        
        t_1 = 0
        t_1_start = 0
        total_t_1 = 0
        
        x_l1_a = 41.390
        y_l1_a = 288.220
            
        x_l1_b = 193.780
        y_l1_b = 288.220

        x_l2_a = 189.630
        y_l2_a = 288.220

        x_l2_b = 45.240
        y_l2_b = 288.220

        x_l1_temp1_a = 150.000
        x_l1_temp2_a = 110.000
        x_l1_temp3_a = 70.000
        #x_l1_temp4_a = 15.000
        y_l1_temp_a = 306.42003906

        x_l2_temp4_a = 180.000
        x_l2_temp3_a = 180.000
        x_l2_temp2_a = 120.000
        x_l2_temp1_a = 40.000
        y_l2_temp_a = 302.570

        speed = 20
        
        spawn_source_l1 = carla.Transform(carla.Location(x_l1_a, y_l1_a, 0.500000), carla.Rotation(0, 90, 0))
        end_source_l1 = carla.Transform(carla.Location(x_l1_b, y_l1_b, 0.500000), carla.Rotation(0, -90, 0))

        spawn_source_l2 = carla.Transform(carla.Location(x_l2_a, y_l2_a, 0.500000), carla.Rotation(0, 90, 0))
        end_source_l2 = carla.Transform(carla.Location(x_l2_b, y_l2_b, 0.500000), carla.Rotation(0, -180, 0))

        spawn_source_temp1_l1 = carla.Transform(carla.Location(x_l1_temp1_a, y_l1_temp_a, 0.500000), carla.Rotation(0, 0, 0))
        end_source_temp1_l1 = carla.Transform(carla.Location(x_l1_b, y_l1_b, 0.500000), carla.Rotation(0, -90, 0))
        
        #spawn_source_temp1_l2 = carla.Transform(carla.Location(x_l2_temp1_a, y_l2_temp_a, 0.500000), carla.Rotation(0, -180, 0))
        #end_source_temp1_l2 = carla.Transform(carla.Location(x_l2_b, y_l2_b, 0.500000), carla.Rotation(0, -90, 0))

        spawn_source_temp2_l1 = carla.Transform(carla.Location(x_l1_temp2_a, y_l1_temp_a, 0.500000), carla.Rotation(0,0, 0))
        end_source_temp2_l1 = carla.Transform(carla.Location(x_l1_b, y_l1_b, 0.500000), carla.Rotation(0, -90, 0))

        spawn_source_temp2_l2 = carla.Transform(carla.Location(x_l2_temp2_a, y_l2_temp_a, 0.500000), carla.Rotation(0, -180, 0))
        spawn_source_temp2_l22 = carla.Transform(carla.Location(x_l2_temp1_a, y_l2_temp_a, 0.500000), carla.Rotation(0, -180, 0))
        end_source_temp2_l2 = carla.Transform(carla.Location(x_l2_b, y_l2_b, 0.500000), carla.Rotation(0, -90, 0))

        spawn_source_temp3_l1 = carla.Transform(carla.Location(x_l1_temp3_a, y_l1_temp_a, 0.500000), carla.Rotation(0,0, 0))
        end_source_temp3_l1 = carla.Transform(carla.Location(x_l1_b, y_l1_b, 0.500000), carla.Rotation(0, -90, 0))

        spawn_source_temp3_l2 = carla.Transform(carla.Location(x_l2_temp3_a, y_l2_temp_a, 0.500000), carla.Rotation(0, -180, 0))
        end_source_temp3_l2 = carla.Transform(carla.Location(x_l2_b, y_l2_b, 0.500000), carla.Rotation(0, -90, 0))

        #spawn_source_temp4_l1 = carla.Transform(carla.Location(x_l1_temp4_a, y_l1_temp_a, 0.500000), carla.Rotation(0,0, 0))
        #end_source_temp4_l1 = carla.Transform(carla.Location(x_l1_b, y_l1_b, 0.500000), carla.Rotation(0, -90, 0))

        spawn_source_temp4_l2 = carla.Transform(carla.Location(x_l2_temp4_a, y_l2_temp_a, 0.500000), carla.Rotation(0, -180, 0))
        end_source_temp4_l2 = carla.Transform(carla.Location(x_l2_b, y_l2_b, 0.500000), carla.Rotation(0, -90, 0))

        route_l1 = [spawn_source_l1, end_source_l1]
        route_l2 = [spawn_source_l2, end_source_l2]
        
        route_temp1_l1 = [spawn_source_temp1_l1, end_source_temp1_l1]
        #route_temp1_l2 = [spawn_source_temp1_l2, end_source_temp1_l2]
        route_temp2_l1 = [spawn_source_temp2_l1, end_source_temp2_l1]
        route_temp2_l2 = [spawn_source_temp2_l2, end_source_temp2_l2]
        route_temp3_l1 = [spawn_source_temp3_l1, end_source_temp3_l1]
        route_temp3_l2 = [spawn_source_temp3_l2, spawn_source_temp2_l22]
        #route_temp4_l1 = [spawn_source_temp4_l1, end_source_temp4_l1]
        route_temp4_l2 = [spawn_source_temp4_l2, end_source_temp4_l2]

        hunday = 'vehicle.hunday.hunday'

        while True:
            world.wait_for_tick()

            if not start:
                # spawn the vehicle and add it to the vehilce list
                v1, v1.agent = spawn_vehicle(world, hunday, route_temp3_l2, speed)
                vehicles_list.append(v1)

                start = True

            for v in vehicles_list:
                loc = v.get_location()
                if v.agent.done():
                    v.destroy()
                    vehicles_list.remove(v)
                else:
                    #v.agent.update_information(world)
                    control = v.agent.run_step()
                    control.manual_gear_shift = False
                    v.apply_control(control)

    finally:

        if world is not None:
            settings = world.get_settings()
            settings.synchronous_mode = False
            settings.fixed_delta_seconds = None
            world.apply_settings(settings)
            traffic_manager.set_synchronous_mode(True)

            print('\ndestroying %d vehicles' % len(vehicles_list))
            for v in vehicles_list:
                v.destroy()
            
            print('\ndestroying %d walkers' % len(walkers_list))
            for w in walkers_list:
                w.destroy()
                w.controller.destroy()
                


# ==============================================================================
# -- main() --------------------------------------------------------------
# ==============================================================================


def main():
    """Main method"""

    argparser = argparse.ArgumentParser(
        description='CARLA Automatic Control Client')
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='debug',
        help='Print debug information')
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
        '-w', '--number-of-walkers',
        metavar='W',
        default=10,
        type=int,
        help='Number of walkers (default: 10)')
    argparser.add_argument(
        '--seedw',
        metavar='S',
        default=0,
        type=int,
        help='Set the seed for pedestrians module')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='vehicle.*',
        help='Actor filter (default: "vehicle.*")')
    argparser.add_argument(
        '--generation',
        metavar='G',
        default='2',
        help='restrict to certain actor generation (values: "1","2","All" - default: "2")')
    argparser.add_argument(
        '--filterw',
        metavar='PATTERN',
        default='walker.pedestrian.*',
        help='Filter pedestrian type (default: "walker.pedestrian.*")')
    argparser.add_argument(
        '--generationw',
        metavar='G',
        default='2',
        help='restrict to certain pedestrian generation (values: "1","2","All" - default: "2")')
    argparser.add_argument(
        '-b', '--behavior', type=str,
        choices=["cautious", "normal", "aggressive"],
        help='Choose one of the possible agent behaviors (default: normal) ',
        default='normal')

    args = argparser.parse_args()

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
