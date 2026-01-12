#!/usr/bin/env python

# Miscelaneous module for CARMEn
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.


# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================

import math


# ==============================================================================
# -- Classes -------------------------------------------------------------------
# ==============================================================================


class CARMEnRoute:
    """Creates a CARMEnRoute instance with defined start point, end point and target speed"""

    def __init__(self, start_point_transfom, end_point_transfom, name, target_speed, offset=None):
        
        self.start_point_transfom = start_point_transfom
        self.end_point_transfom = end_point_transfom
        self.name = name
        self.target_speed = target_speed
        self.offset = offset



class CARMEnCheckpoint:
    """Creates a CARMEnCheckpoint instance with defined spawn points for vehicles"""
    def __init__(self, session, desired_point, spawns_vehicle_when_reached=False 
                 , desired_spawn_back_left=None, desired_spawn_back_right=None
                 , desired_spawn_front_left=None, desired_spawn_front_right=None 
    ):
        self.name = desired_point.name
        self.transform = desired_point.get_valid_transform(session.spawn_points)
        self.spawns_vehicle_when_reached = spawns_vehicle_when_reached
        self.desired_spawn_back_left = desired_spawn_back_left
        self.desired_spawn_back_right = desired_spawn_back_right
        self.desired_spawn_front_left = desired_spawn_front_left
        self.desired_spawn_front_right = desired_spawn_front_right
        self.check = False

    def distance_from_player(self, player_transform):
        return math.sqrt( (self.transform.location.x - player_transform.location.x)**2 + \
                         (self.transform.location.y - player_transform.location.y)**2 + \
                         (self.transform.location.z - player_transform.location.z)**2 )


class CARMEnPoint:
    """Creates a CARMEnPoint instance that located in the map"""

    def __init__(self, x, y, name, lane_id=0):
        
        self.x = x
        self.y = y
        self.name = name
        self.lane_id = lane_id

    def get_valid_transform(self, session_spawn_points):

        # Check trough all spawn points for the desired point
        for n, transform in enumerate(session_spawn_points):
            if abs(self.x - transform.location.x) < 0.5 and abs(self.y - transform.location.y) < 0.5:
                #print(f"Spawn point {self.name} found in spawn point {n}, in location {transform.location}")
                spawn_point = transform
                return spawn_point
                
        print("Desired point not found among Spawn Points!")
        return None