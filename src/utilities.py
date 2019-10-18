import pygame as pg
import json

import settings as st



vec = pg.math.Vector2


def clamp(var, lower, upper):
    # restrains a variable's value between two values
    return max(lower, min(var, upper))


def collide_hitbox(one, two):
    return one.hitbox.colliderect(two.hitbox)


def collide_with_walls(sprite, group, dir_):
    if dir_ == 'x':
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hitbox)
        if hits:
            wall = hits[0]
            # hit from left
            if wall.hitbox.centerx > sprite.hitbox.centerx:
                sprite.pos.x = wall.hitbox.left - sprite.hitbox.w / 2
            # hit from right
            elif wall.hitbox.centerx < sprite.hitbox.centerx:
                sprite.pos.x = wall.hitbox.right + sprite.hitbox.w / 2
                            
            sprite.vel.x = 0
            sprite.hitbox.centerx = sprite.pos.x
            return True
            
    elif dir_ == 'y':
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hitbox)
        if hits:
            wall = hits[0]
            # hit from top
            if wall.hitbox.centery > sprite.hitbox.centery:
                sprite.pos.y = wall.hitbox.top - sprite.hitbox.h / 2
            # hit from bottom
            elif wall.hitbox.centery < sprite.hitbox.centery:
                sprite.pos.y = wall.hitbox.bottom + sprite.hitbox.h / 2
                
            sprite.vel.y = 0
            sprite.hitbox.centery = sprite.pos.y
            return True
    return False


def difference(list1, list2):
    return [1 if elem and not list1[i] else 0 for i, elem in enumerate(list2)]


def draw_text(surface, text, file, size, color, pos, align='topleft'):
    '''
    draws the text string at a given position with the given text file
    (might be too performance intensive?)
    '''
    font = pg.font.Font(file, size)
    font.set_bold(False)
    text_surface = font.render(text, False, color)
    text_rect = text_surface.get_rect()
    setattr(text_rect, align, pos)
    surface.blit(text_surface, text_rect)


def grid_to_pos(grid, cellsize, offset):
    return (grid[0] * cellsize + offset[0], grid[1] * cellsize + offset[1])


def is_jsonable(x):
    try:
        json.dumps(x)
        return True
    except:
        return False


def pos_to_grid(pos, cellsize, offset):
    return (int((pos[0] - offset[0]) / cellsize), int((pos[1] - offset[0]) / cellsize))


class Camera():
    '''
    modified from http://kidscancode.org/lessons/
    modes are
        FOLLOW: player is always in the middle of the screen
        CUT: camera pans as soon as the player leaves the screen
        SLIDE: like pan, but with a sliding animation
    '''
    def __init__(self, game, map_width, map_height, mode='FOLLOW'):
        self.game = game
        self.rect = pg.Rect(0, 0, map_width, map_height)
        self.map_width = map_width
        self.map_height = map_height
        self.mode = mode

        self.is_sliding = False
        self.target_pos = vec()
        self.prev_pos = vec()
        # previous quadrant
        self.prev_qw = 0
        self.prev_qh = 0
        
        self.slide_speed = 0.05 # percent, change this to dt
        self.slide_amount = 0


    def apply(self, entity):
        return entity.rect.move(self.rect.x, self.rect.y)


    def apply_rect(self, rect):
        return rect.move(self.rect.x, self.rect.y)
    
    
    def apply_bg(self, rect):
        return rect.move(self.rect.x, self.rect.y)
    

    def apply_pos(self, point):
        return point + vec(self.rect.x, self.rect.y)
    
    
    def apply_point_int(self, point):
        v = point + vec(self.rect.x, self.rect.y)
        return (int(v.x), int(v.y))


    def update(self, target):
        if target == None:
            return
        
        if self.mode == 'FOLLOW':
            x = -target.rect.x + self.game.world_screen_rect.w // 2
            y = -target.rect.y + self.game.world_screen_rect.h // 2
        elif self.mode == 'CUT':
            # divide into quadrants
            quads_w = self.rect.w // self.game.world_screen_rect.w
            quads_h = self.rect.h // self.game.world_screen_rect.h
            # which quadrant the target is in.
            qw = target.rect.x // (self.rect.w // quads_w)
            qh = target.rect.y // (self.rect.h // quads_h)
            
            x = (self.game.world_screen_rect.w) * qw * -1
            y = (self.game.world_screen_rect.h) * qh * -1
            
        elif self.mode == 'SLIDE':
            # divide into quadrants
            quads_w = self.rect.w // self.game.world_screen_rect.w
            quads_h = self.rect.h // self.game.world_screen_rect.h
            # which quadrant the target is in 
            qw = target.rect.x // (self.rect.w // quads_w)
            qh = target.rect.y // (self.rect.h // quads_h)
            
            # limit the quadrants to the map
            qw = min(max(qw, 0), quads_w - 1)
            qh = min(max(qh, 0), quads_h - 1)
            
            self.target_pos.x = (self.game.world_screen_rect.w) * qw * -1
            self.target_pos.y = (self.game.world_screen_rect.h) * qh * -1

            if qw != self.prev_qw or qh != self.prev_qh:
                self.is_sliding = True
                
                self.slide_amount += self.slide_speed
                self.slide_amount = min(self.slide_amount, 1)
                between = self.prev_pos.lerp(self.target_pos, self.slide_amount)
                
                x = int(between.x)
                y = int(between.y)
                
                if self.target_pos.x == x and self.target_pos.y == y:
                    self.prev_qw = qw
                    self.prev_qh = qh
                    self.slide_amount = 0
                
            else:
                self.is_sliding = False
                
                x = self.target_pos.x
                y = self.target_pos.y
                
                self.prev_pos.x = self.target_pos.x
                self.prev_pos.y = self.target_pos.y

                self.prev_qw = qw
                self.prev_qh = qh

        # limit scrolling to map size
        x = min(0, x) # left
        x = max(-(self.map_width - self.game.world_screen_rect.w), x) # right
        y = min(0, y) # top
        y = max(-(self.map_height - self.game.world_screen_rect.h), y) # bottom
        
        self.rect = pg.Rect(x, y, self.map_width, self.map_height)
        

class Line:
    '''
    custom Line class that represents a line with a start and end vector
    and provides a method for intersection checking
    '''
    def __init__(self, start, end):
        self.start = vec(start)
        self.end = vec(end)
        self.color = pg.Color('White')
    
    
    def draw(self, screen, width=1, camera=None):
        if camera:
            pg.draw.line(screen, self.color, camera.apply_pos(self.start), 
                         camera.apply_pos(self.end), width)
        else:
            pg.draw.line(screen, self.color, self.start, self.end, width)
        
        
    def intersects_line(self, other, displacement):
        # http://www.jeffreythompson.org/collision-detection/line-rect.php
        # check if two Line objects intersect
        # if true, change the displacement vector by the distance between
        # this line's end and the intersection
        denA = ((other.end.y - other.start.y) * (self.end.x - self.start.x) - 
                (other.end.x - other.start.x) * (self.end.y - self.start.y))
        denB = ((other.end.y - other.start.y) * (self.end.x - self.start.x) - 
                (other.end.x - other.start.x) * (self.end.y - self.start.y))
        if denA == 0 or denB == 0:
            return False
        else:
            numA = ((other.end.x - other.start.x) * (self.start.y - other.start.y) - 
                    (other.end.y - other.start.y) * (self.start.x - other.start.x))
            numB = ((self.end.x - self.start.x) * (self.start.y - other.start.y) - 
                    (self.end.y - self.start.y) * (self.start.x - other.start.x))
            uA = numA / denA
            uB = numB / denB
            if (uA >= 0 and uA <= 1 and uB >= 0 and uB <= 1):
                displacement.x -= (1.0 - uA) * (self.end.x - self.start.x)
                displacement.y -= (1.0 - uA) * (self.end.y - self.start.y)
                return True
            else:
                return False
            
            
    def get_lines_from_rect(self, rect):
        l1 = Line(rect.topleft, rect.topright)
        l2 = Line(rect.topright, rect.bottomright)
        l3 = Line(rect.bottomright, rect.bottomleft)
        l4 = Line(rect.bottomleft, rect.topleft)
        return [l1, l2, l3, l4]
    
    
    def intersects_rect(self, rect):
        lines = self.get_lines_from_rect(rect)
        lines_intersect = []
        displacements = []
        for line in lines:
            displacement = vec()
            if self.intersects_line(line, displacement):
                lines_intersect.append(line)
                displacements.append(displacement)
        return lines_intersect, displacements