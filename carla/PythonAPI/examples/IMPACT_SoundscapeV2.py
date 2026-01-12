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


class Scene:
    """Creates a Scene instance that gets all VehicleSpawnPoints of the Unreal Level"""

    def __init__(self, world):
        
        self.spawn_points = self.extract_spawn_points(world)

    def extract_spawn_points(self, world):
        print("Extracting spawn points...")
        spawn_points = world.get_map().get_spawn_points()
        for n, transform in enumerate(spawn_points):
            print(f"Spawn point {n} found in {transform} ")
        return spawn_points


class SpawnPoint:
    """Creates a SpawnPoint instance that defines the desired spawn point for the route"""

    def __init__(self, x, y, name):
        
        self.x = x
        self.y = y
        self.name = name

    def get_valid_spawn_point(self, scene_spawn_points):

        # Check trough all spawn points for the desired point
        for n, transform in enumerate(scene_spawn_points):
            if abs(self.x - transform.location.x) < 0.5 and abs(self.y - transform.location.y) < 0.5:
                print(f"Spawn point {self.name} found in spawn point {n}, in location {transform.location}")
                start_point = transform
                return start_point
                
        print("Desired point not found among Spawn Points!")
        return None


class Route:
    """Creates a Route instance with defined start point, end point and target speed"""

    def __init__(self, start_point, end_point, name, target_speed):
        
        self.start_point = start_point
        self.end_point = end_point
        self.name = name
        self.target_speed = target_speed


class Vehicle:
    """Creates a Vehcile instance which contains all the info of the vehicle, including id for spawn/destriuction \
        and agent for control. Colors can be grey, red, dark_blue, cyan, black and white. Models can be audi_a2, citroen_c3, \
        lincoln_mkz, mercedes_coupe, mini_cooper, nissan_patrol"""

    def __init__(self, world, model, color, route, current_speed=None):

        color_scheme = {'grey' : '76,76,76'
                    , 'red' : '190,0,0'
                    , 'dark_blue' : '0,5,75'
                    , 'cyan' : '19,84,127'
                    , 'black' : '14,14,14'
                    , 'white' : '255,255,255'
                    }
        
        model_list = {'audi_a2' : 'vehicle.audi.a2'
                      , 'citroen_c3' : 'vehicle.citroen.c3'
                      , 'lincoln_mkz' : 'vehicle.lincoln.mkz_2020'
                      , 'mercedes_coupe' : 'vehicle.mercedes.coupe_2020'
                      , 'mini_cooper' : 'vehicle.mini.cooper_s_2021'
                      , 'nissan_patrol' : 'vehicle.nissan.patrol_2021'
                    }
        
        self.model = model_list[model]
        self.color = color_scheme[color]
        self.route = route
        self.speed = route.target_speed if current_speed is None else current_speed
        self.blueprint = self.get_blueprint(world)
        self.id = self.spawn_vehicle(world)
        self.agent = self.set_agent(self.id)

    def get_blueprint(self, world):
        # Get blueprint.
        blueprint = world.get_blueprint_library().find(self.model)
        blueprint.set_attribute('role_name', 'hero')
        if blueprint.has_attribute('color'):
            blueprint.set_attribute('color', self.color)
        
        return blueprint
    
    def spawn_vehicle(self, world):

        vehicle = world.spawn_actor(self.blueprint, self.route.start_point)
        print(f"Created a {self.model} in start point {self.route.start_point}")
        
        return vehicle
    
    def set_agent(self, vehicle):

        agent = BasicAgent(vehicle, self.speed)
        agent.set_target_speed(self.speed)
        agent.follow_speed_limits(False)
        agent.ignore_traffic_lights(True)
        agent.ignore_stop_signs(True)

        start_location = self.route.start_point.location
        end_location = self.route.end_point.location
        agent.set_destination(end_location, start_location)
        print(f"Created an agent for vehicle {self.model}, will move at {self.route.target_speed} Km/h")

        return agent


# ==============================================================================
# -- Global functions ----------------------------------------------------------
# ==============================================================================

def get_actor_blueprints(world, filter, generation):
    bps = world.get_blueprint_library().filter(filter)

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
        return []
    

# ==============================================================================
# -- Game Loop ---------------------------------------------------------
# ==============================================================================

def game_loop(args):    
    """
    Main loop of the simulation. It handles updating all the HUD information,
    ticking the agent and, if needed, the world.
    """

    try:
        vehicles_list = []

        client = carla.Client(args.host, args.port)
        client.set_timeout(60.0)

        traffic_manager = client.get_trafficmanager()
        world = client.get_world()

        blueprint_list = get_actor_blueprints(world, args.filter, args.generation)
        if not blueprint_list:
            raise ValueError("Couldn't find any blueprints with the specified filters")

        start = False
        stop = False
        wait = False

        t_1 = 0
        t_1_start = 0
        total_t_1 = 0

        spawn_points = Scene(world).spawn_points
        
        print("Creating new route...")
        route1_desired_start = SpawnPoint(75, -50.6, 'route1_start')
        route1_desired_end = SpawnPoint(-39.3, 65.9, 'route1_end')
        route1_name = 'route1'
        route1_target_speed = 20
        route1_start = route1_desired_start.get_valid_spawn_point(spawn_points)
        route1_end = route1_desired_end.get_valid_spawn_point(spawn_points)
        if route1_start is not None and route1_end is not None:
            route1 = Route(route1_start, route1_end, 'route1', route1_target_speed)
            print(f"Created Route {route1.name}!\n")
        else:
            print("Could not create Route 1!\n")

        print("Creating new route...")
        route2_desired_start = SpawnPoint(-36.1, 64.7, 'route2_start')
        route2_desired_end = SpawnPoint(75.0, -47.2, 'route2_end')
        route2_name = 'route2'
        route2_target_speed = 20
        route2_start = route2_desired_start.get_valid_spawn_point(spawn_points)
        route2_end = route2_desired_end.get_valid_spawn_point(spawn_points)
        if route2_start is not None and route2_end is not None:
            route2 = Route(route2_start, route2_end, 'route2', route2_target_speed)
            print(f"Created Route {route2.name}!\n")
        else:
            print("Could not create Route 2!\n")

        timetable = [
                     [10, 'mercedes_coupe', 'white', route1]          # lane 1
                     ,[15, 'mini_cooper', 'red', route2]              # lane 2
        ]
        
        next_i = 0
        next_spawn_t = timetable[next_i][0]
        next_route = timetable[next_i][1]

        wait_t = 5
        end_t = 184

        while True:
            world.wait_for_tick()

            if not start and not wait:
                # spawn the vehicle and add it to the vehilce list
                vehicle = Vehicle(world, 'mercedes_coupe', 'white', route1, 0)
                vehicles_list.append(vehicle)

                #start timer
                t_1_start = time.perf_counter()
                total_t_1 = 0
                # flag wait
                wait = True

            if wait and total_t_1 >= wait_t:
                #restart timer
                t_1_start = time.perf_counter()
                total_t_1 = 0
                for v in vehicles_list:
                    v.agent.set_target_speed(v.route.target_speed)
                    print('\n--- Start Run ---\n')
                # flag start
                wait = False
                start = True
            
            if total_t_1 >= next_spawn_t and start and not stop:
                # spawn the vehicle and add it to the vehilce list
                vehicle = Vehicle(world, timetable[next_i][1], timetable[next_i][2], timetable[next_i][3])
                vehicles_list.append(vehicle)
                next_i += 1
                if next_i >= len(timetable):
                    stop = True
                if not stop:
                    next_spawn_t = timetable[next_i][0]
                    next_route = timetable[next_i][1]
                #w, w.controller = spawn_walker(world, random.choice(blueprintsWalkers), w_route_l1_a_3)
                #walkers_list.append(w)

            # count timer
            t_1 = time.perf_counter()
            total_t_1 = t_1 - t_1_start

            if total_t_1 >= end_t:
                return

            for v in vehicles_list:
                if v.agent.done():
                    v.id.destroy()
                    vehicles_list.remove(v)
                else:
                    #v.agent.update_information(world)
                    control = v.agent.run_step()
                    control.manual_gear_shift = False
                    v.id.apply_control(control)

    finally:

        if world is not None:
            settings = world.get_settings()
            settings.synchronous_mode = False
            settings.fixed_delta_seconds = None
            world.apply_settings(settings)
            traffic_manager.set_synchronous_mode(True)

            print('\ndestroying %d vehicles' % len(vehicles_list))
            for v in vehicles_list:
                v.id.destroy()
            
            #print('\ndestroying %d walkers' % len(walkers_list))
            #for w in walkers_list:
            #    w.destroy()
            #    w.controller.destroy()
                


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
