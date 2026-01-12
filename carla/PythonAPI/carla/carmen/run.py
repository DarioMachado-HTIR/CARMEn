#!/usr/bin/env python

# CARMEnRun module for CARMEn
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.


# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================

import carla

from carmen.vehicle import CARMEnVehicle 
from carmen.utils import CARMEnRoute 

import random


# ==============================================================================
# -- Classes -------------------------------------------------------------------
# ==============================================================================


class CARMEnRun(object):

    def __init__(self, road_width=3.4, directions_pool=None, is_demo=False):
        self.directions_pool = None
        if directions_pool is not None:
            self.directions_pool = directions_pool
            random.shuffle(self.directions_pool)
        self.spawn_direction = ''
        self.current_checkpoint = ''
        self.vehicles_list = []
        self.start = False
        self.stop = False
        self.wait = False
        self.t = 0
        self.t_start = 0
        self.t_total = 0
        self.t_wait = 2.0
        self.t_next_spawn = 0
        self.offset = road_width
        self.waiting = False
        self.is_demo = is_demo

    def create_new_route(self, session, desired_route_start_point, desired_route_end_point, name, target_speed, offset=None):
        #print("Creating new route...")
        route_start_point_transform = desired_route_start_point.get_valid_transform(session.spawn_points)
        route_end_point_transform = desired_route_end_point.get_valid_transform(session.spawn_points)
        if route_start_point_transform is not None and route_end_point_transform is not None:
            route = CARMEnRoute(route_start_point_transform, route_end_point_transform, name, target_speed, offset)
            print(f"Created Route {route.name}, starting in {route_start_point_transform.location} and ending in {route_end_point_transform.location} with offset {offset}!")
        else:
            print("Could not create Route!\n")
        #self.routes_list.append(route)
        return route

    def spawn_new_agent_vehicle(self, session, model, color, route, current_speed=None, offset=None, draw_route=False):
        vehicle = CARMEnVehicle(session.world, model, color, route, current_speed, offset, draw_route)
        self.vehicles_list.append(vehicle)

    def decide_checkpoint_start_and_end(self, checkpoint):
        if self.directions_pool is None:
            direction_dice_roll = random.randrange(1,10)
            # 80% front
            if direction_dice_roll <= 8: 
                # 50% front-left (without offest) or front-right (with offset)
                offset = random.choice([0, self.offset])
                desired_start_point = checkpoint.desired_spawn_front_left
                desired_end_point = checkpoint.desired_spawn_back_left
            # 20% back
            else: 
                # 50% back-left (with offest) or back-right (without offset)
                offset = random.choice([0, self.offset])
                desired_start_point = checkpoint.desired_spawn_back_right
                desired_end_point = checkpoint.desired_spawn_front_right
        else:
            print(f"Direction Pool is {self.directions_pool}")
            # Remove and Get last element of list
            self.spawn_direction = self.directions_pool.pop()
            self.current_checkpoint = checkpoint.name
            print(f"Choosen direction: {self.spawn_direction}")
            if self.spawn_direction == "FL":
                # front-left (without offest)
                offset = 0
                desired_start_point = checkpoint.desired_spawn_front_left
                desired_end_point = checkpoint.desired_spawn_back_left
            elif self.spawn_direction == "FR":
                # front-right (with offest)
                offset = self.offset
                desired_start_point = checkpoint.desired_spawn_front_left
                #print(desired_start_point.location)
                desired_end_point = checkpoint.desired_spawn_back_left
            elif self.spawn_direction == "BL":
                # back-left (with offest)
                offset = self.offset
                desired_start_point = checkpoint.desired_spawn_back_right
                desired_end_point = checkpoint.desired_spawn_front_right
            elif self.spawn_direction == "BR":
                # back-right (without offest)
                offset = 0
                desired_start_point = checkpoint.desired_spawn_back_right
                desired_end_point = checkpoint.desired_spawn_front_right

        #print(f"Chosen route {desired_start_point.name} -> {desired_end_point.name} with offset {offset}")
        return desired_start_point, desired_end_point, offset

    def tick(self, session):
        if not self.start:
            #start timer
            self.t_start = session.hud.simulation_time
            self.t_total = 0
            self.start = True
            if self.is_demo:
                print('\n--- Start Demo ---\n')
            else:
                print('\n--- Start Run ---\n')

        # count timer
        #if not self.start:
        #    self.t = session.hud.simulation_time
        #    self.t_total = self.t - self.t_start

        if isinstance(session.player, carla.Walker) and session.checkpoint_list is not None:
            player = session.player.get_transform()
            for checkpoint in session.checkpoint_list:
                if checkpoint.check:
                    continue
                else:
                    distance = checkpoint.distance_from_player(player)
                    #print(distance)
                if distance > 2:
                    break
                else:
                    if checkpoint == session.checkpoint_list[-1]:
                        self.stop = True
                    else:
                        if checkpoint.spawns_vehicle_when_reached and not self.is_demo:
                            r_start, r_stop, offset = self.decide_checkpoint_start_and_end(checkpoint)
                            chosen_model = random.choice(session.model_list)
                            chosen_color = random.choice(session.color_scheme)
                            r = self.create_new_route(session
                                            , r_start
                                            , r_stop
                                            , 'route_'+checkpoint.name
                                            , 20
                                            , offset)
                            self.spawn_new_agent_vehicle(session
                                                , model = chosen_model
                                                , color = chosen_color
                                                , route = r
                                                , draw_route=False)
                            print(f"Spawned {chosen_model}, {chosen_color}\n")
                        checkpoint.check = True
                        print(f"Checkpoint {self.current_checkpoint} passed!\n")

        for v in self.vehicles_list:
            if v.agent.done():
                v.id.destroy()
                self.vehicles_list.remove(v)
                self.spawn_direction = ''
                self.current_checkpoint = ''
            else:
                #v.agent.update_information(session)
                control = v.agent.run_step()
                control.manual_gear_shift = False
                v.id.apply_control(control)

    def destroy(self):
        print('\ndestroying %d vehicles' % len(self.vehicles_list))
        for v in self.vehicles_list:
            v.id.destroy()
        print('\n--- Stop Run ---\n')