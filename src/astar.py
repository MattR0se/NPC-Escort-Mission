'''
https://hobby-programmer.com/pygame_astar.php
'''

from pygame import Vector2

# Make pygame.Vector2 hashable
class Vector(Vector2):
    def __hash__(self):
        return int(self.x + self.y)

class StepPathing:
    def __init__(self, start, goal, map_level, map_size, pattern, block_value):
        start = start
        self.goal = goal
        self.break_out = 0
        self.came_from = {}
        self.pattern = pattern
        self.open_set = [start]
        self.gscore = {start: 0}
        self.fscore = {start: start.distance_to(self.goal)}
        self.map_size = map_size
        self.map_level = map_level
        self.block_value = block_value
        self.current = start

    def get_low_score(self):
        low_score = -1
        gvector = None
        for vector in self.open_set:
            if low_score == -1:
                gvector = vector
                low_score = self.fscore[vector]
            elif self.fscore[vector] < low_score:
                gvector = vector
                low_score = self.fscore[vector]

        return gvector

    def get_path(self):
        path = None
        while path is None:
            path = self.step()

        return path

    def get_neighbors(self):
        straight = list(map(Vector, ((0, 1), (0, -1), (1, 0), (-1, 0))))
        neighbors = []

        if self.current is None:
            return []

        for n in straight:
            new_neighbor = self.current + n
            # Is neighbor with in grid
            if self.map_size.x > int(new_neighbor.x) >= 0 and \
               self.map_size.y > int(new_neighbor.y) >= 0:

                if self.map_level[int(new_neighbor.x)][int(new_neighbor.y)] \
                   < self.block_value:
                    if self.map_size.x > new_neighbor.x >= 0 and self.map_size.y \
                       > new_neighbor.y >= 0:
                        neighbors.append(Vector(new_neighbor))

        # moves on angles
        if self.pattern == '*':
            angles = list(map(Vector, ((1, 1), (-1, -1), (1, -1), (-1, 1))))
            for n in angles:
                new_neighbor = self.current + n
                x = int(new_neighbor.x)
                y = int(new_neighbor.y)
                if self.map_size.x > x >= 0 and self.map_size.y > y >= 0:
                    wall = self.map_level[x][y] > self.block_value - 1
                    block = (self.map_level[x][int(self.current.y)] >
                             self.block_value - 1 or
                             self.map_level[int(self.current.x)][y] >
                             self.block_value - 1)

                    # Don't allow angle movement next to wall.
                    if not wall and not block:
                        neighbors.append(Vector(new_neighbor))

        return neighbors

    def step(self):
        if len(self.open_set) > 0:
            self.current = self.get_low_score()
            if self.current == self.goal:
                return self.reconstructed_path()

            self.open_set.remove(self.current)
            neighbors = self.get_neighbors()

            for neighbor in neighbors:
                gscore = self.gscore[self.current] + \
                         neighbor.distance_to(self.current)

                if neighbor not in self.gscore.keys():
                    self.gscore[neighbor] = gscore
                    self.fscore[neighbor] = gscore + \
                        neighbor.distance_to(self.goal)
                    self.came_from[neighbor] = self.current
                    self.open_set.append(neighbor)
                elif gscore < self.gscore[neighbor]:
                    self.gscore[neighbor] = gscore
                    self.fscore[neighbor] = gscore + \
                        neighbor.distance_to(self.goal)
                    self.came_from[neighbor] = self.current
                    self.open_set.append(neighbor)
        else:
            return []

    def reconstructed_path(self):
        current = self.current
        path = [current]
        while current in self.came_from.keys():
            current = self.came_from[current]
            path.append(current)

        return path