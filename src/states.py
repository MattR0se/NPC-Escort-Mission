import pygame as pg
from itertools import cycle

import tilemaps
import sprites as spr
import utilities as utils
import settings as st


'''
Based on the state machine tutorial by metulburr
https://python-forum.io/Thread-PyGame-Creating-a-state-machine
'''


class State(object):
    '''parent class for all states'''
    def __init__(self, game):
        self.game = game
        self.next = None # what comes after if this is done
        self.done = False # if true, the next state gets executed
        self.previous = None # the state that was executed before
    
    def startup(self):
        pass
    
    def cleanup(self):
        pass
    
    def get_event(self, event):
        pass
    
    def update(self, dt):
        pass
    
    def draw(self):
        pass
    


class Game_start(State):
    '''
    This state is called once at the beginning of the game
    it initialises all persistent objects (like the player, inventory etc)
    '''
    def __init__(self, game):
        State.__init__(self, game)
        self.next = 'In_game'
    
    
    def startup(self):
        self.game.map = tilemaps.Map(self.game, self.game.map_files[0])
        self.game.map.create_map()
        self.game.map.rect.topleft = (0, 0)
        
        self.game.camera = utils.Camera(self.game, self.game.map.size.x, 
                                        self.game.map.size.y, 'FOLLOW')
        
        # just instantiates some stuff and then it's done
        self.done = True


class In_game(State):
    '''
    This is the default in game state where the user can control the 
    player sprite
    '''
    def __init__(self, game):
        State.__init__(self, game)
    
    
    def startup(self):
        pass
        # start playing backround music for this state
        #self.game.asset_loader.play_music('dungeon1')
        
        self.game.maze = []
        for x in range(self.game.map.rect.w // st.CELL_SIZE):
            self.game.maze.append([])
            for y in range(self.game.map.rect.h // st.CELL_SIZE):
                point = utils.grid_to_pos((x, y), st.CELL_SIZE, st.CELL_OFFSET)
                intersects = False
                for w in self.game.walls:
                    rect = w.hitbox.inflate((st.CELL_SIZE, st.CELL_SIZE))
                    #rect = w.hitbox #TODO: not optimal
                    if rect.collidepoint(point):
                        intersects = True
                self.game.maze[x].append(1 if intersects else -1)
        
        self.camera_targets = cycle([self.game.player, self.game.npc])
        self.current_camera_target = next(self.camera_targets)
    
    
    def cleanup(self):
        self.game.save('test.json')
    
    
    def get_event(self, event):
        # toggle the camera target
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_F1:
                self.current_camera_target = next(self.camera_targets)
    
    
    def update(self, dt):
        if not self.game.camera.is_sliding:
            self.game.all_sprites.update(dt)
        self.game.camera.update(self.current_camera_target)
              
        
    def draw(self):
        self.game.screen.fill(pg.Color('black'))
        
        # draw map layers
        for layer in range(self.game.map.max_layer + 1):
            # TODO: this is not optimal since it has to loop through all of the
            # layers and sprites for each layer...
            for i, tiles in self.game.map.layers.items():
                if i == layer:
                    self.game.screen.blit(tiles, 
                                          self.game.camera.apply_bg(self.game.map.rect))
            for sprite in self.game.all_sprites:
                if sprite.layer == layer:
                    sprite.draw(self.game.screen, self.game.camera.apply(sprite))
                    
                    if self.game.debug_mode:
                        if hasattr(sprite, 'hitbox'):
                            pg.draw.rect(self.game.screen, pg.Color('Red'), 
                                         self.game.camera.apply_rect(sprite.hitbox), 1)
                        if hasattr(sprite, 'line_to_target'):
                            sprite.line_to_target.draw(self.game.screen, camera=self.game.camera)
                        if hasattr(sprite, 'path'):
                            if sprite.path:
                                path_points = [self.game.camera.apply_pos(utils.grid_to_pos(p, 
                                                                 st.CELL_SIZE,
                                                                 st.CELL_OFFSET)) 
                                               for p in sprite.path]
                                if len(path_points) > 1:
                                    pg.draw.lines(self.game.screen, pg.Color('Blue'), 
                                                  False, path_points)
        
        for wall in self.game.walls:
            wall.draw(self.game.screen, self.game.camera.apply(wall))
        
        
# =============================================================================
#         if self.game.debug_mode:
#             # draw cells of grid
#             for x, col in enumerate(self.game.maze):
#                 for y, cell in enumerate(col):
#                     if cell == -1:
#                         pos = utils.grid_to_pos((x, y),
#                                                 st.CELL_SIZE,
#                                                 st.CELL_OFFSET)
#                         pg.draw.circle(self.game.screen,
#                                        pg.Color('Blue'), 
#                                        self.game.camera.apply_point_int(pos), 
#                                        1)
#         
# =============================================================================


class Title_screen(State):
    def __init__(self, game):
        State.__init__(self, game)
        self.next = 'Game_start'
    
    def startup(self):
        self.texts = []
        
        strings = [
                'NPC Escort Mission Demo',
                'Move with WASD',
                'Toggle Debug Mode with F12',
                ' ',
                ' ',
                'Press any key to start'
                ]
                    
        for y, s in enumerate(strings):
            txt, txt_rect = self.game.fonts['default'].render(s, 
                                                    fgcolor=pg.Color('White'),
                                                    bgcolor=None)
                                                    
            txt_rect.centerx = self.game.screen_rect.centerx
            txt_rect.centery = (y + 1) * self.game.screen_rect.h / (len(strings) + 2)
            self.texts.append((txt, txt_rect))
            
        
        player = spr.Player(self.game, {'x':0, 'y':120, 'width':16, 'height':28})
        player.speed = 10
        self.npc = spr.NPC(self.game, {'x':-48, 'y':120, 'width':16, 'height':28})
        self.npc.speed = 10
    
    
    def cleanup(self):
        self.game.player.kill()
        self.npc.kill()
    

    def get_event(self, event):
        # press any key to continue
        if event.type == pg.KEYDOWN or self.game.gamepad_controller.any_key():
            self.done = True
                       
    
    def update(self, dt):
        self.game.player.move_cutscene(dt)
        self.npc.move_cutscene(dt)
              
        
    def draw(self):
        self.game.screen.fill(pg.Color('Black'))
        
        for t in self.texts:
            self.game.screen.blit(*t)
        player = self.game.player
        player.draw(self.game.screen, player.rect)
        if player.pos.x >= self.game.screen_rect.w + 16:
            player.pos.x = -16
            
        self.npc.draw(self.game.screen, self.npc.rect)
        if self.npc.pos.x >= self.game.screen_rect.w + 16:
            self.npc.pos.x = -16
        
