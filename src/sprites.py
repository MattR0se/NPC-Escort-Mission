import pygame as pg
import pygame.freetype
from collections import deque

from astar import StepPathing, Vector
import settings as st
import utilities as utils


vec = Vector


RIGHT = 0
DOWN = 1
LEFT = 2
UP = 3


class BaseSprite(pg.sprite.Sprite):
    def __init__(self, game, groups, **kwargs):
        '''
        kwargs have to be at least:
            x: x position
            y: y position
            width: rect.w
            height: rect.h
        '''
        self.game = game
        super().__init__(groups)
        
        for key, value in kwargs.items():
            setattr(self, key, value)
        # set additional custom properties (from Tiled 'properties' dict)
        if hasattr(self, 'properties'):
            for key, value in self.properties.items():
                setattr(self, key, value)
        
        self.anim_timer = 0
        self.anim_frame = 0
        self.anim_delay = 0.2 # overwrite this in child class
    
    
    def animate(self, dt):
        # loop through all of self.images and set self.image to the next
        # image if the time exceeds the delay
        self.anim_timer += dt
        if self.anim_timer >= self.anim_delay:
            # reset the timer
            self.anim_timer = 0
            # advance the frame
            self.anim_frame = (self.anim_frame + 1) % len(self.images[self.image_state])
            # set the image and adjust the rect
            self.image = self.images[self.image_state][self.anim_frame]
            self.rect = self.image.get_rect()
            self.rect.midbottom = self.hitbox.midbottom
    
    
    def draw(self, screen, pos_or_rect):
        screen.blit(self.image, pos_or_rect)
        
                

class Player(BaseSprite):
    def __init__(self, game, kwargs):
        super().__init__(game, game.all_sprites, **kwargs)
        
        self.game.player = self
        images = self.game.graphics['knight']
        self.images = {
                'hit': images[0:1],
                'idle_right': images[1:5],
                'idle_left': [pg.transform.flip(i, True, False) for i in images[1:5]],
                'run_right': images[5:8],
                'run_left': [pg.transform.flip(i, True, False) for i in images[5:8]]
                }
        
        #print(self.images)
        self.image_state = 'idle_right'
        self.image = self.images[self.image_state][0]
        
        self.rect = self.image.get_rect()
        self.hitbox = pg.Rect(0, 0, 12, 12)
        
        self.pos = vec(self.x, self.y)
        self.hitbox.center = self.pos
        self.rect.midbottom = self.hitbox.midbottom
        
        # physics properties
        self.acc = vec()
        self.vel = vec()
        self.speed = 20
        self.friction = 0.8
        
        # animation
        self.lastdir = RIGHT
        self.anim_delay = 0.15
        
        # A_star variables
        self.grid_pos = utils.pos_to_grid(self.pos, 
                                          st.CELL_SIZE, 
                                          st.CELL_OFFSET)
        self.last_grid_pos = self.grid_pos
        
    
    def move_cutscene(self, dt):
        self.acc *= 0
        self.acc.x = 1
        
        if self.acc.length() > 1:
            # prevent faster diagnoal movement
            self.acc.scale_to_length(1)
        # laws of motion
        self.vel += self.acc * self.speed * dt
        self.vel *= self.friction
        
        speed = self.vel.length()
        
        if speed < 0.05:
            self.vel *= 0
            if self.lastdir == RIGHT:
                self.image_state = 'idle_right'
            else:
                self.image_state = 'idle_left'
        else:
            if self.acc.x > 0:
                self.image_state = 'run_right'
                self.lastdir = RIGHT
            elif self.acc.x < 0:
                self.image_state = 'run_left'
                self.lastdir = LEFT
        
        self.pos += self.vel
        
        self.hitbox.center = self.pos
        self.rect.midbottom = self.hitbox.midbottom
        
        self.animate(dt)
        
    
    def update(self, dt):
        keys = pg.key.get_pressed() #TODO use game key controller
        
        self.acc *= 0
        self.acc.x = keys[pg.K_d] - keys[pg.K_a]
        self.acc.y = keys[pg.K_s] - keys[pg.K_w]
        
        if self.acc.length() > 1:
            # prevent faster diagnoal movement
            self.acc.scale_to_length(1)
        # laws of motion
        self.vel += self.acc * self.speed * dt
        self.vel *= self.friction
        
        speed = self.vel.length()
        
        if speed < 0.05:
            self.vel *= 0
            if self.lastdir == RIGHT:
                self.image_state = 'idle_right'
            else:
                self.image_state = 'idle_left'
        else:
            if self.acc.x > 0:
                self.image_state = 'run_right'
                self.lastdir = RIGHT
            elif self.acc.x < 0:
                self.image_state = 'run_left'
                self.lastdir = LEFT
        
        self.pos += self.vel
        
        # collision detection
        # the center of the hitbox is always at the sprite's position
        self.hitbox.centerx = self.pos.x
        utils.collide_with_walls(self, self.game.walls, 'x')
        self.hitbox.centery = self.pos.y
        utils.collide_with_walls(self, self.game.walls, 'y')
        # the rect(where the image is drawn)'s bottom is aligned with the hitbox's bottom
        self.rect.midbottom = self.hitbox.midbottom
        
        self.animate(dt)
        
        # pathfinding stuff
        self.grid_pos = utils.pos_to_grid(self.pos, 
                                          st.CELL_SIZE, 
                                          st.CELL_OFFSET)
        try:
            maze_value = self.game.maze[self.grid_pos[0]][self.grid_pos[1]]
        except IndexError:
            maze_value = 1
        # store grid pos if not on wall
        if maze_value == -1:
            self.last_grid_pos = self.grid_pos
        
        
class NPC(BaseSprite):
    def __init__(self, game, kwargs):
        super().__init__(game, game.all_sprites, **kwargs)
        
        game.npc = self
        
        images = self.game.graphics['elf']
        self.images = {
                'hit': images[0:1],
                'idle_right': images[1:5],
                'idle_left': [pg.transform.flip(i, True, False) for i in images[1:5]],
                'run_right': images[5:8],
                'run_left': [pg.transform.flip(i, True, False) for i in images[5:8]]
                }
        
        #print(self.images)
        self.image_state = 'idle_right'
        self.image = self.images[self.image_state][0]
        
        self.rect = self.image.get_rect()
        self.hitbox = pg.Rect(0, 0, 7, 7)
        
        self.pos = vec(self.x, self.y)
        self.hitbox.center = self.pos
        self.rect.midbottom = self.hitbox.midbottom
        
        # physics properties
        self.acc = vec()
        self.vel = vec()
        self.speed = self.game.player.speed * 0.5
        self.friction = 0.8
        
        # path following variables
        self.target = vec()
        self.pathfinding_interval = 0.5 # seconds
        self.counter = self.pathfinding_interval
        self.max_path_length = 100
        self.path = []
        self.is_lost = False
        
        # animation
        self.lastdir = RIGHT
        self.anim_delay = 0.15
    
    
    def move_cutscene(self, dt):
        self.acc *= 0
        self.acc.x = 1
        
        if self.acc.length() > 1:
            # prevent faster diagnoal movement
            self.acc.scale_to_length(1)
        # laws of motion
        self.vel += self.acc * self.speed * dt
        self.vel *= self.friction
        
        speed = self.vel.length()
        
        if speed < 0.05:
            self.vel *= 0
            if self.lastdir == RIGHT:
                self.image_state = 'idle_right'
            else:
                self.image_state = 'idle_left'
        else:
            if self.acc.x > 0:
                self.image_state = 'run_right'
                self.lastdir = RIGHT
            elif self.acc.x < 0:
                self.image_state = 'run_left'
                self.lastdir = LEFT
        
        self.pos += self.vel
        
        self.hitbox.center = self.pos
        self.rect.midbottom = self.hitbox.midbottom
        
        self.animate(dt)
        
    
    def find_path(self, target, dt):
        self.counter += dt
        if self.counter >= self.pathfinding_interval:
            self.counter = 0
            # translate position to grid
            start = utils.pos_to_grid(self.pos, st.CELL_SIZE, st.CELL_OFFSET)
            end = target.last_grid_pos # set target to last known player information
            
            grid_size = vec(len(self.game.maze), 
                            len(self.game.maze[0]))
            self.path_step = StepPathing(vec(start), 
                                         vec(end),
                                         self.game.maze, 
                                         grid_size, 
                                         '*', 
                                         1)
            self.path = self.path_step.get_path()[1:-1]
            self.path_to_follow = deque([vec(utils.grid_to_pos(p, st.CELL_SIZE,
                                         st.CELL_OFFSET)) for p in self.path])
    
    
    def follow_path(self):
        if hasattr(self, 'path_to_follow') and len(self.path_to_follow) > 0:
            target = self.path_to_follow[-1]
            vec_to_target = target - self.pos
            if vec_to_target.length() > st.TILE_WIDTH:
                self.acc = vec_to_target.normalize()
            else:
                self.path_to_follow.pop()
                self.acc = vec((0, 0))
        else:
            self.acc = vec((0, 0))
    
    
    def update(self, dt):
        # check if line between self and target intersects walls
        player = self.game.player
        self.line_to_target = utils.Line(self.pos, player.pos)
        intersects = False
        for wall in self.game.walls:
            hit, _ = self.line_to_target.intersects_rect(wall.hitbox)
            if hit:
                intersects = True

        if intersects:
            self.line_to_target.color = pg.Color('Red')
            if not self.is_lost:
                self.find_path(player, dt)
                self.follow_path()
            
            if len(self.path) >= self.max_path_length:
                self.is_lost = True
                self.path_to_follow.clear()
                self.acc = vec((0, 0))
            else:
                self.image_index = -1
        else:
            self.is_lost = False
            self.image_index = -1
            self.target = player.pos
            self.line_to_target.color = pg.Color('White')
            vec_to_target = self.target - self.pos
            if vec_to_target.length() > st.TILE_WIDTH * 2:
                self.acc = vec_to_target.normalize()
            else:
                self.acc = vec((0, 0))
            
            # reset pathfinding counter
            self.counter = self.pathfinding_interval
            self.path = []
        
        if self.acc.length() > 1:
            self.acc.scale_to_length(1)
        self.vel += self.acc * self.speed * dt
        self.vel *= self.friction
        
        speed = self.vel.length()
        
        if speed < 0.05:
            self.vel *= 0
            if self.lastdir == RIGHT:
                self.image_state = 'idle_right'
            else:
                self.image_state = 'idle_left'
        else:
            if self.acc.x > 0:
                self.image_state = 'run_right'
                self.lastdir = RIGHT
            elif self.acc.x < 0:
                self.image_state = 'run_left'
                self.lastdir = LEFT
                
        self.pos += self.vel
        
        # collision detection
        # the center of the hitbox is always at the sprite's position
        self.hitbox.centerx = self.pos.x
        utils.collide_with_walls(self, self.game.walls, 'x')
        self.hitbox.centery = self.pos.y
        utils.collide_with_walls(self, self.game.walls, 'y')
        # the rect(where the image is drawn)'s bottom is aligned with the hitbox's bottom
        self.rect.midbottom = self.hitbox.midbottom
        
        self.animate(dt)
        


class Wall(BaseSprite):
    ''' Invisible Wall object for collisions
    '''
    def __init__(self, game, kwargs):
        super().__init__(game, game.walls, **kwargs)
        
        self.image = pg.Surface((self.width, self.height), pg.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x, self.y)
        self.hitbox = self.rect.copy()
    
    
    def update(self, dt):
        pass
    
    
    def draw(self, screen, rect):
        if self.game.debug_mode:
            pg.draw.rect(screen, pg.Color('Red'), rect, 1)
        
