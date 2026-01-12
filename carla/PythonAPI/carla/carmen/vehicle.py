#!/usr/bin/env python

# CARMEnVehicle module for CARMEn
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.


# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================

from agents.navigation.basic_agent import BasicAgent  # pylint: disable=import-error

import math



# ==============================================================================
# -- Classes -------------------------------------------------------------------
# ==============================================================================


class CARMEnVehicle:
    """Creates a CARMEnVehicle instance which contains all the info of the vehicle, including id for spawn/destriuction \
        and agent for control. Colors can be grey, red, dark_blue, cyan, black and white. Models can be audi_a2, citroen_c3, \
        lincoln_mkz, mercedes_coupe, mini_cooper, nissan_patrol"""

    def __init__(self, world, model, color, route, speed_at_spawn=None, offset_at_spawn=None, draw_route=False):

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
        self.speed = route.target_speed if speed_at_spawn is None else speed_at_spawn
        self.offset = route.offset if offset_at_spawn is None else offset_at_spawn
        self.blueprint = self.get_blueprint(world)
        self.id = self.spawn_vehicle(world)
        self.agent = self.set_agent(self.id, draw_route)

    def get_blueprint(self, world):
        # Get blueprint.
        blueprint = world.get_blueprint_library().find(self.model)
        blueprint.set_attribute('role_name', 'hero')
        if blueprint.has_attribute('color'):
            blueprint.set_attribute('color', self.color)
        
        return blueprint
    
    def spawn_vehicle(self, world):

        if self.offset is not None:
            start_point = self.relative_offset(self.route.start_point_transfom)
        else:
            start_point = self.route.start_point_transfom
        vehicle = world.spawn_actor(self.blueprint, start_point)
        #print(f"Created a {self.model} in start point {start_point} with offset of {self.offset}")
        
        return vehicle
    
    def set_agent(self, vehicle, draw = False):

        if self.offset is not None:
            opt_dict = {'offset': -self.offset}
        else:
            opt_dict = {}
        agent = BasicAgent(vehicle, self.speed, opt_dict)
        agent.set_target_speed(self.speed)
        agent.follow_speed_limits(False)
        agent.ignore_traffic_lights(True)
        agent.ignore_stop_signs(True)

        if self.offset is not None:
            start_point = self.remove_offset(self.route.start_point_transfom)
        else:
            start_point = self.route.start_point_transfom
        start_location = start_point.location
        end_location = self.route.end_point_transfom.location
        agent.set_destination(end_location, start_location, draw=draw)
        #print(f"Created an agent for vehicle {self.model}, will move at {self.route.target_speed} Km/h with offset {self.offset}")

        return agent
    
    def relative_offset(self, spawn_point_2_offset):
        
        rot = spawn_point_2_offset.rotation.yaw
        
        spawn_point_2_offset.location.x += self.offset * math.sin(math.radians(rot))
        spawn_point_2_offset.location.y -= self.offset * math.cos(math.radians(rot))
        
        return spawn_point_2_offset
    
    def remove_offset(self, offset_spawn_point):
        
        rot = offset_spawn_point.rotation.yaw
        
        offset_spawn_point.location.x -= self.offset * math.sin(math.radians(rot))
        offset_spawn_point.location.y += self.offset * math.cos(math.radians(rot))
        
        return offset_spawn_point
    