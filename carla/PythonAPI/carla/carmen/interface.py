#!/usr/bin/env python

# Interface module for CARMEn
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.



# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================

import carla

from carmen.global_functions import get_actor_display_name

import carmen.opensignals as opensignals
import PyGameWidgets.widgets as widgets
import PyGameWidgets.core as core

import os
import math
import datetime
import csv

try:
    import pygame          
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')


# ==============================================================================
# -- Classes -------------------------------------------------------------------
# ==============================================================================


class CARMEnHUD(object):
    def __init__(self, width, height, doc, panel):
        self.dim = (width, height)
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        font_name = 'courier' if os.name == 'nt' else 'mono'
        fonts = [x for x in pygame.font.get_fonts() if font_name in x]
        default_font = 'ubuntumono'
        mono = default_font if default_font in fonts else fonts[0]
        mono = pygame.font.match_font(mono)
        self._font_mono = pygame.font.Font(mono, 12 if os.name == 'nt' else 14)
        self._notifications = FadingText(font, (width, 40), (0, height - 40))
        self.help = HelpText(pygame.font.Font(mono, 24), width, height, doc)
        self.server_fps = 0
        self.frame = 0
        self.simulation_time = 0
        self._show_info = True
        self._info_text = []
        self._server_clock = pygame.time.Clock()
        self.panel = panel
        self.buttons = []
        self.buttons.append( widgets.TextButton(panel, (0, 0), core.Text("   Connect Biosignals", 14)) )
        self.buttons.append( widgets.TextButton(panel, (0, 7), core.Text("        Start Run", 14)) )
        self.buttons.append( widgets.TextButton(panel, (0, 9), core.Text("       End Session", 14)) )
        if self.buttons is not None:
            for b in self.buttons:
                b.set_image("../carla/PyGameWidgets/gfx/bg1.bmp")
        self.opts = []
        self.opts.append( widgets.OptionChooser(panel, (0, 1), ["       Recording OFF", "       Recording ON"], 14) )
        self.opts.append( widgets.OptionChooser(panel, (0, 2), ["        Real Trial", "          Demo"], 14) )
        self.opts.append( widgets.OptionChooser(panel, (0, 3), ["        70% Front", "        70% Back"], 14) )
        if self.opts is not None:
            for opt in self.opts:
                opt.set_span((0, 0))
                opt.set_border(core.BLACK, 16)
                #opt.text_color = core.RED
                opt.bold = True
                #opt.italic = True
                opt.update_text()
        self.biosignals_client = opensignals.OpenSignalsTCPClient()
        self.rec_biosignals = False
        self.file = None
        self.writer = None
        self.rec = False
        self.pool_idx = 0
        self.is_demo = False

    def on_world_tick(self, timestamp):
        self._server_clock.tick()
        self.server_fps = self._server_clock.get_fps()
        self.frame = timestamp.frame
        self.simulation_time = timestamp.elapsed_seconds

    def tick(self, session, clock, args):
        self._notifications.tick(session, clock)
        if not self._show_info:
            return
        self._info_text = [
            'Server:  % 16.0f FPS' % self.server_fps,
            'Client:  % 16.0f FPS' % clock.get_fps(),
            '',
            'Map:     % 20s' % session.world.get_map().name.split('/')[-1],
            'Simulation time: % 12s' % datetime.timedelta(seconds=int(self.simulation_time)),
            '']
        if session.run is not None:
            t = session.player.get_transform()
            v = session.player.get_velocity()
            c = session.player.get_control()
            heading = 'N' if abs(t.rotation.yaw) < 89.5 else ''
            heading += 'S' if abs(t.rotation.yaw) > 90.5 else ''
            heading += 'E' if 179.5 > t.rotation.yaw > 0.5 else ''
            heading += 'W' if -0.5 > t.rotation.yaw > -179.5 else ''
            colhist = session.collision_sensor.get_collision_history()
            collision = [colhist[x + self.frame - 200] for x in range(0, 200)]
            max_col = max(1.0, max(collision))
            collision = [x / max_col for x in collision]
            vehicles = session.world.get_actors().filter('vehicle.*')
            lat_dev = session.lat_dev
            ang_dev = session.ang_dev
            checkpoint = session.run.current_checkpoint
            spawn_direction = session.run.spawn_direction
            self._info_text += [
                'Vehicle: % 20s' % get_actor_display_name(session.player, truncate=20),
                'Speed:   % 15.0f km/h' % (3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2)),
                u'Heading:% 16.0f\N{DEGREE SIGN} % 2s' % (t.rotation.yaw, heading),
                'Location:% 20s' % ('(% 5.1f, % 5.1f)' % (t.location.x, t.location.y)),
                'GNSS:% 24s' % ('(% 2.6f, % 3.6f)' % (session.gnss_sensor.lat, session.gnss_sensor.lon)),
                'Height:  % 18.0f m' % t.location.z,
                '']
            if session.lat_dev is not None and session.ang_dev is not None:
                self._info_text += [
                'Lat Deviation:   % 10.2f m' % lat_dev,
                'Ang Deviation:   % 11.2f\N{DEGREE SIGN}' % ang_dev,
                '']
            if isinstance(c, carla.VehicleControl):
                self._info_text += [
                    ('Throttle:', c.throttle, 0.0, 1.0),
                    ('Steer:', c.steer, -1.0, 1.0),
                    ('Brake:', c.brake, 0.0, 1.0),
                    ('Reverse:', c.reverse),
                    ('Hand brake:', c.hand_brake),
                    ('Manual:', c.manual_gear_shift),
                    'Gear:        %s' % {-1: 'R', 0: 'N'}.get(c.gear, c.gear)]

            elif isinstance(c, carla.WalkerControl):
                self._info_text += [
                    ('Speed:', c.speed, 0.0, 5.556)]

            self._info_text += [
                '',
                'Collision:',
                collision,
                '',
                'Number of vehicles: % 8d' % len(vehicles)]
            if len(vehicles) > 0:
                self._info_text += ['Nearby vehicles:']
                distance = lambda l: math.sqrt((l.x - t.location.x)**2 + (l.y - t.location.y)**2 + (l.z - t.location.z)**2)
                vehicles = [(distance(x.get_location()), x) for x in vehicles if x.id != session.player.id]
                for d, vehicle in sorted(vehicles):
                    if d > 200.0:
                        break
                    vehicle_type = get_actor_display_name(vehicle, truncate=22)
                    self._info_text.append('% 4dm %s' % (d, vehicle_type))
                
                self._info_text += [
                    'Current Checkpoint:',
                    checkpoint,
                    ('Spawn Direction: %s' % spawn_direction)]

            if self.rec:
                # write data
                self.record_data(t, lat_dev, ang_dev, checkpoint, spawn_direction, vehicles)

    def record_data(self, t, lat_dev, ang_dev, checkpoint='', spawn_direction='', vehicles=[]):
            # Getting the current date and time
            time = datetime.datetime.now()
            _now = time.strftime('%Y-%m-%d %H:%M:%S')
            if self.first_tick == True:
                print("Started Recording") 
                self.t_rec_start = time.timestamp() * 1000
                self.first_tick = False
            _t_rec = ( time.timestamp() * 1000 - self.t_rec_start ) / 1000
            _t_rec = round(_t_rec, 3)
            #print(_t_rec, end='\r')
            _locationX = round(t.location.x, 2)
            _locationY = round(t.location.y, 2)
            _locationZ = round(t.location.z, 2)
            _yaw = round(t.rotation.yaw, 2)
            # lateral and angular deviations from lane
            _lat_dev = round(lat_dev, 2)
            _ang_dev = round(ang_dev, 1)
            # Vehicle Distance and Position
            if len(vehicles) > 0:
                for d, vehicle in vehicles:
                    _vehicle_name = get_actor_display_name(vehicle, truncate=22)
                    _v_distance = d
                    _v_loc = vehicle.get_location()
                    _v_locationX = round(_v_loc.x, 2)
                    _v_locationY = round(_v_loc.y, 2)
                    _v_locationZ = round(_v_loc.z, 2)
            else:
                _vehicle_name = ''
                _v_distance = None
                _v_locationX = None
                _v_locationY = None
                _v_locationZ = None
            
            data = [
                _now, _t_rec, 
                _locationX, _locationY, _locationZ, _yaw, 
                _lat_dev, _ang_dev, 
                checkpoint, spawn_direction, 
                _vehicle_name,
                _v_distance, _v_locationX, _v_locationY, _v_locationZ]
            
            self.writer.writerow(data)

    def toggle_info(self):
        self._show_info = not self._show_info

    def notification(self, text, seconds=2.0):
        self._notifications.set_text(text, seconds=seconds)

    def error(self, text):
        self._notifications.set_text('Error: %s' % text, (255, 0, 0))

    def button_pressed(self, button):
        if button.text.value != "           Armed!":
            button.set_image("../carla/PyGameWidgets/gfx/bg0.bmp")

    def button_released(self, button, session, dualcontrol):
        button.set_image("../carla/PyGameWidgets/gfx/bg1.bmp")
        if button.text.value == "   Connect Biosignals":
            try:
                self.biosignals_client.connect()
                self.biosignals_client.start()
                self.rec_biosignals = True
                button.set_text(core.Text("   Disconnect Biosignals", 14))
                print("SUCESS: Connected to Biosignals!")
            except:
                print("ERROR: Could not connect to Biosignals! Check if socket is open!")
        elif button.text.value == "   Disconnect Biosignals":
            self.biosignals_client.stop()
            self.rec_biosignals = False
            button.set_text(core.Text("   Connect Biosignals", 14))
        elif button.text.value == "        Start Run":
            if self.rec:
                print("Started Recording") 
                self.create_write_file(session.subject, session.experiment, session.directory)
                if self.rec_biosignals and not self.biosignals_client.isAcquiring:
                    self.biosignals_client.setIsAcquiring(True)
                    self.biosignals_client.addMsgToSend('start')
                    while not self.biosignals_client.deviceStarted:
                        pass
            if session.set_new_run(self.is_demo, self.pool_idx):
                dualcontrol.set_new_player_controller(session)
                button.set_text(core.Text("        Stop Run", 14))
        elif button.text.value == "        Stop Run":
            if self.rec:
                print("Stopped Recording") 
                self.file.close()
                if self.rec_biosignals:
                    self.biosignals_client.setIsAcquiring(False)
                    self.biosignals_client.addMsgToSend('stop')
                    self.biosignals_client.deviceStarted = False
            if session.end_new_run():
                dualcontrol._control = None
                button.set_text(core.Text("        Start Run", 14))
        elif button.text.value == "       End Session":
            if session.run is not None:
                if session.end_new_run():
                    dualcontrol._control = None
            if self.rec_biosignals:
                self.biosignals_client.setIsAcquiring(False)
                self.biosignals_client.addMsgToSend('stop')
                self.biosignals_client.deviceStarted = False
            if self.rec and self.file is not None:
                print("Stopped Recording") 
                self.file.close()
                #self.rec = False
            session.destroy()
            dualcontrol.end_session = True


    def option_changed(self, option_choser):
        if option_choser.current_value == "        70% Front":
            self.pool_idx = 0
        elif option_choser.current_value == "        70% Back":
            self.pool_idx = 1
        elif option_choser.current_value == "        Real Trial":
            self.is_demo = False
        elif option_choser.current_value == "          Demo":
            self.is_demo = True
        elif option_choser.current_value == "       Recording OFF":
            self.rec = False
            print("OFF!")
        elif option_choser.current_value == "       Recording ON":
            self.rec = True
            print("ON!")
            

    def create_write_file(self, subject, experiment, directory):
        date = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
        # open the file in the write mode
        filename = subject + '_' + experiment + '_' + date + '.csv'
        self.file = open(directory + filename, 'w', newline='')
        print('Created file ', self.file)

        title = ['subject: ' + subject + ' -- created: ' + date]
        header = [
            'datetime', 't_rec', 
            'locationX', 'locationY', 'locationZ', 'yaw', 
            'lateral_deviation', 'angular_deviation',
            'checkpoint', 'spawn_direction',  
            'vehicle_model',
            'vehicle_distance', 'vehicleX', 'vehicleY', 'vehicleZ']

        # create the csv writer
        self.writer = csv.writer(self.file)

        # write the title and header
        self.writer.writerow(title)
        self.writer.writerow('')
        self.writer.writerow(header)

        self.rec = True

        self.first_tick = True
        self.t_rec_start = 0.0


    def render(self, display):
        self.panel.draw(display)
        if self.buttons is not None:
            for b in self.buttons:
                b.draw(display)
        if self.opts is not None:
            for opt in self.opts:
                opt.draw(display)
        if self._show_info:
            info_surface = pygame.Surface((220, self.dim[1]))
            info_surface.set_alpha(100)
            display.blit(info_surface, (0, 0))
            h_offset = 220
            v_offset = 4
            bar_h_offset = 100
            bar_width = 106
            for item in self._info_text:
                if v_offset + 18 > self.dim[1]:
                    break
                if isinstance(item, list):
                    if len(item) > 1:
                        points = [(h_offset + x + 8, v_offset + 8 + (1.0 - y) * 30) for x, y in enumerate(item)]
                        pygame.draw.lines(display, (255, 136, 0), False, points, 2)
                    item = None
                    v_offset += 18
                elif isinstance(item, tuple):
                    if isinstance(item[1], bool):
                        rect = pygame.Rect((h_offset + bar_h_offset, v_offset + 8), (6, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect, 0 if item[1] else 1)
                    else:
                        rect_border = pygame.Rect((h_offset + bar_h_offset, v_offset + 8), (bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect_border, 1)
                        f = (item[1] - item[2]) / (item[3] - item[2])
                        if item[2] < 0.0:
                            rect = pygame.Rect((h_offset + bar_h_offset + f * (bar_width - 6), v_offset + 8), (6, 6))
                        else:
                            rect = pygame.Rect((h_offset + bar_h_offset, v_offset + 8), (f * bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect)
                    item = item[0]
                if item:  # At this point has to be a str.
                    surface = self._font_mono.render(item, True, (255, 255, 255))
                    display.blit(surface, (h_offset + 8, v_offset))
                v_offset += 18
        self._notifications.render(display)
        self.help.render(display)



class FadingText(object):
    def __init__(self, font, dim, pos):
        self.font = font
        self.dim = dim
        self.pos = pos
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)

    def set_text(self, text, color=(255, 255, 255), seconds=2.0):
        text_texture = self.font.render(text, True, color)
        self.surface = pygame.Surface(self.dim)
        self.seconds_left = seconds
        self.surface.fill((0, 0, 0, 0))
        self.surface.blit(text_texture, (10, 11))

    def tick(self, _, clock):
        delta_seconds = 1e-3 * clock.get_time()
        self.seconds_left = max(0.0, self.seconds_left - delta_seconds)
        self.surface.set_alpha(500.0 * self.seconds_left)

    def render(self, display):
        display.blit(self.surface, self.pos)



class HelpText(object):
    def __init__(self, font, width, height, doc):
        lines = doc.split('\n')
        self.font = font
        self.dim = (680, len(lines) * 22 + 12)
        self.pos = (0.5 * width - 0.5 * self.dim[0], 0.5 * height - 0.5 * self.dim[1])
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)
        self.surface.fill((0, 0, 0, 0))
        for n, line in enumerate(lines):
            text_texture = self.font.render(line, True, (255, 255, 255))
            self.surface.blit(text_texture, (22, n * 22))
            self._render = False
        self.surface.set_alpha(220)

    def toggle(self):
        self._render = not self._render

    def render(self, display):
        if self._render:
            display.blit(self.surface, self.pos)