#!/usr/bin/env python

# CARMEnSession module for CARMEn
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.


# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================

import carla

from carmen.run import CARMEnRun
from carmen.global_functions import get_actor_display_name, clamp_to_range, clamp_to_direction
from carmen.sensors import GnssSensor, CameraManager, LaneInvasionSensor, CollisionSensor

import random
import re


# ==============================================================================
# -- Classes -------------------------------------------------------------------
# ==============================================================================


class CARMEnSession(object):
    def __init__(self, carla_world, hud, actor_filter, player_start_list,
                 subject="S00", experiment="carmen", directory='C:\\carla\\Unreal\\CarlaUE4\\Data\\',
                 model_list=None, color_scheme=None, waypoints=False, waypoint_distance=0.3, draw=False, 
                 road_width=3.4, road_id_list=[], lane_id=[]):
        self.world = carla_world
        self.run = None
        self.hud = hud
        self.player = None
        self.collision_sensor = None
        self.lane_invasion_sensor = None
        self.gnss_sensor = None
        self.camera_manager = None
        self._weather_presets = self.find_weather_presets()
        self._weather_index = 0
        self._actor_filter = actor_filter
        self.model_list = ['audi_a2', 'citroen_c3', 'lincoln_mkz', 'mercedes_coupe', 'mini_cooper', 'nissan_patrol'] if model_list is None else model_list
        self.color_scheme = ['grey', 'red', 'dark_blue', 'cyan', 'black', 'white'] if color_scheme is None else color_scheme
        self.spawn_points = self.extract_spawn_points()
        self.lat_dev = None
        self.ang_dev = None
        self.unique_waypoints = self.generate_unique_waypoints(waypoint_distance, draw, road_id_list, lane_id) if waypoints else None
        self.player_start_list = player_start_list
        self.subject = subject
        self.experiment = experiment
        self.directory = directory
        self.checkpoint_list = None
        self.directions_pools = None
        self.road_width = road_width
        self.world.on_tick(hud.on_world_tick)

    def restart(self, player_start):
        # Keep same camera config if the camera manager exists.
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0
        # Get a blueprint.
        blueprint = self.world.get_blueprint_library().find(self._actor_filter)
        blueprint.set_attribute('role_name', 'hero')
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        # Spawn the player.
        #print(self.player)
        if self.player is not None:
            spawn_point = self.player.get_transform()
            spawn_point.location.z += 2.0
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        while self.player is None:
            # Get transform of checkpoint 0 (player_start)
            spawn_point = player_start.get_valid_transform(self.spawn_points)
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        # Set up the sensors.
        self.collision_sensor = CollisionSensor(self.player, self.hud)
        if isinstance(self.player, carla.Vehicle): 
            self.lane_invasion_sensor = LaneInvasionSensor(self.player, self.hud)
        self.gnss_sensor = GnssSensor(self.player)
        self.camera_manager = CameraManager(self.player, self.hud)
        self.camera_manager.transform_index = cam_pos_index
        self.camera_manager.set_sensor(cam_index, notify=False)
        actor_type = get_actor_display_name(self.player)
        if self.unique_waypoints is not None:
            self.lat_dev, self.ang_dev = self.distance_from_my_waypoint(self.player.get_transform())
            self.lat_dev -= ( self.road_width / 2 )
        self.hud.notification(actor_type)

    def find_weather_presets(self):
        rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
        name = lambda x: ' '.join(m.group(0) for m in rgx.finditer(x))
        presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
        return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]

    def next_weather(self, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        preset = self._weather_presets[self._weather_index]
        self.hud.notification('Weather: %s' % preset[1])
        self.player.get_world().set_weather(preset[0])

    def set_checkpoints(self, checkpoint_list, directions_pools=None):
        self.checkpoint_list = checkpoint_list
        self.directions_pools = directions_pools

    def get_player_start(self, name):
        #print("Looking for Player Start point: ", name)
        for player_start in self.player_start_list:
            if player_start.name == name:
                return player_start
            else:
                continue
        print("Player Start not Found!")
        return None

    def set_new_run(self, is_demo, pool_idx):
        if self.run is None:
            if self.directions_pools is not None:
                new_direction_pool = self.directions_pools[pool_idx].copy()
            else:
                new_direction_pool = None
            self.run = CARMEnRun(self.road_width, new_direction_pool, is_demo)
            if is_demo:
                player_start_name = 'player_start_check1'
            else:
                player_start_name = 'player_start'
            player_start = self.get_player_start(player_start_name)
            if player_start is not None:
                self.restart(player_start)
                #print("Set New Run!")
                return True
            else:
                print("Could not Set new Run!")
                return False
        else:
            print("Run Already set!")
            return False

    def end_new_run(self):
        if self.run is not None:
            self.destroy()
            self.run = None
            return True
        else:
            print("No active Runs!")
            return False

    def tick(self, clock, args):
        if self.run is not None:
            self.run.tick(self) 
            if self.unique_waypoints is not None:
                self.lat_dev, self.ang_dev = self.distance_from_my_waypoint(self.player.get_transform())   
                self.lat_dev -= ( self.road_width / 2 ) 
        self.hud.tick(self, clock, args)


    def render(self, display):
        #self.camera_manager.render(display)
        self.hud.render(display)

    def extract_spawn_points(self):
        print("Extracting spawn points...")
        spawn_points = self.world.get_map().get_spawn_points()
        #for n, transform in enumerate(spawn_points):
            #print(f"Spawn point {n} found in {transform} ")
        print(f'Found {len(spawn_points)} spawn points in world')
        return spawn_points
    
    def generate_unique_waypoints(self, distance=0.3, draw=False, road_id_list=None, lane_id=None):
        # Genretate waypoints
        all_waypoints = self.world.get_map().generate_waypoints(distance) #0.3 is distance between waypoints in meters
        # make unique
        unique_waypoints = []
        for wp in all_waypoints:
            if wp.road_id in road_id_list and wp.lane_id == lane_id:
                if len(unique_waypoints)==0:
                    unique_waypoints.append(wp) # first waypoint is added regardless to start the list
                else:
                    found = False
                    for uwp in unique_waypoints: # check for same located waypoints and ignore if found
                        if abs(uwp.transform.location.x - wp.transform.location.x) < 0.1 \
                                    and abs(uwp.transform.location.y - wp.transform.location.y) < 0.1 \
                                    and abs(uwp.transform.rotation.yaw -uwp.transform.rotation.yaw) < 20:
                            found = True
                            break
                    if not found:
                        unique_waypoints.append(wp)

        # draw all point in the sim for 60s
        if draw:
            for wp in unique_waypoints:
                self.world.debug.draw_string(wp.transform.location, '^', draw_shadow=False,
                    color=carla.Color(r=0, g=0, b=225), life_time=5.0,
                    persistent_lines=True)
            
        return unique_waypoints
    
    def distance_from_my_waypoint(self, t):
        # this takes less than 0.0 seconds, i.e. it happens in something like 0.001 or similar
        my_waypoint = t.location
        curr_distance = 1000
        for wp in self.unique_waypoints:
            dist = my_waypoint.distance(wp.transform.location)
            if dist < curr_distance:
                curr_distance = dist
                selected_wp = wp
        # drawn the waypoint
        #self.world.debug.draw_string(selected_wp.transform.location, '^', draw_shadow=False,
        #        color=carla.Color(r=0, g=0, b=255), life_time=60.0,
        #        persistent_lines=True)
        # check the distance
        player_transform = self.player.get_transform()
        player_transform.location.z = 0.0
        distance_to_wp = selected_wp.transform.location.distance(player_transform.location)
        direction_difference = (player_transform.rotation.yaw - selected_wp.transform.rotation.yaw)
        direction_difference = clamp_to_direction( clamp_to_range(direction_difference, -180, 180) )
        #print('deviation from waypoint:', distance_to_wp, 'meters, angle discrepancy:', 
        #      direction_difference, 'degrees', end='\r')
        return distance_to_wp, direction_difference

    def destroy(self):
        if self.run is not None:
            self.run.destroy()
            if self.checkpoint_list is not None:
                for checkpoint in self.checkpoint_list:
                    checkpoint.check = False
            if isinstance(self.player, carla.Vehicle):
                sensors = [
                    self.camera_manager.sensor,
                    self.collision_sensor.sensor,
                    self.lane_invasion_sensor.sensor,
                    self.gnss_sensor.sensor]
            elif isinstance(self.player, carla.Walker):
                sensors = [
                    self.camera_manager.sensor,
                    self.collision_sensor.sensor,
                    self.gnss_sensor.sensor]
            for sensor in sensors:
                if sensor is not None:
                    sensor.stop()
                    sensor.destroy()
            if self.player is not None:
                self.player.destroy()
                self.player = None