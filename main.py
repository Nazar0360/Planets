from typing import Any
import pygame as pg
import numpy as np
import random
import sys

def hsv_to_rgb(h, s, v):
    if s == 0:
        r, g, b = v, v, v
    else:
        h /= 60
        i = int(h)
        f = h - i
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))

        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q

    return int(r * 255), int(g * 255), int(b * 255)

def is_rectangle_on_screen(pos1, pos2, screen_width, screen_height):
    x1, y1 = pos1
    x2, y2 = pos2

    if x1 > screen_width and x2 > screen_width:
        return False
    if x1 < 0 and x2 < 0:
        return False
    if y1 > screen_height and y2 > screen_height:
        return False
    if y1 < 0 and y2 < 0:
        return False
    return True

class Game:
    def __init__(self, screen_width=800, screen_height=600, fps=60, speed=1):
        pg.init()
        self.width = screen_width
        self.height = screen_height
        self.screen = pg.display.set_mode((self.width, self.height))
        self.clock = pg.time.Clock()
        self.fps = fps
        self.speed = speed
        
        self.space_system = Game.SpaceSystem()
        self.body_to_launch = None

    def run(self):
        pg.display.set_caption("Game")
        dt = self.clock.tick(self.fps) / 1000
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_mouse_button_down()
                elif event.type == pg.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.handle_mouse_button_up()
                elif event.type == pg.MOUSEWHEEL:
                    self.handle_mousewheel(event.y)
            pg.display.set_caption(f"FPS: {self.clock.get_fps()}")
            self.space_system.tick(dt)
            self.update_screen()
            dt = self.clock.tick(self.fps) / 1000 * self.speed

    def handle_mouse_button_down(self):
        if not self.body_to_launch:
            self.body_to_launch = Game.Body(position=pg.mouse.get_pos())

    def handle_mouse_button_up(self):
        if self.body_to_launch:
            self.body_to_launch.velocity = (self.body_to_launch.position - pg.mouse.get_pos()) * 0.1
            self.space_system.add_body(self.body_to_launch)
            self.body_to_launch = None

    def handle_mousewheel(self, y):
        if self.body_to_launch:
            if pg.key.get_mods() & pg.KMOD_ALT:
                self.body_to_launch.density = max(self.body_to_launch.density + y, 1)
                return
            self.body_to_launch.radius = max(self.body_to_launch.radius + y, 1)

    def update_screen(self):
        self.screen.fill((0, 0, 0))
        if self.body_to_launch:
            pg.draw.line(self.screen, (255, 255, 255), self.body_to_launch.position, self.body_to_launch.position * 2 - pg.mouse.get_pos())
        for body in self.space_system.bodies:
            body.draw(self.screen, self.width, self.height)
        if self.body_to_launch:
            self.body_to_launch.draw(self.screen, self.width, self.height)

        pg.display.flip()

    class Body:
        def __repr__(self) -> str:
            return f'{self.__class__.__name__}(color={self.color}, radius={self.radius}, density={self.density})'

        def __init__(self, *, color=None, radius=None, density=None, mass=None, velocity=(0, 0), position=(0, 0)):
            self.color = list(color if color else hsv_to_rgb(random.randint(0, 360), random.uniform(0.5, 1.0), random.uniform(0.7, 1.0)))
            if radius is None and density is not None and mass is not None:
                radius = (mass * 3 / (density * 4 * np.pi)) ** (1/3)
            elif radius is not None and density is None and mass is not None:
                density = mass / ((4 / 3) * np.pi * radius ** 3)
            else:
                radius = 10 if radius is None else radius
                density = 1 if density is None else density
            self.radius = float(radius)
            self.density = float(density)
            self.velocity = np.array(velocity, dtype=np.float64)
            self.position = np.array(position, dtype=np.float64)

        def move(self, dt: float):
            self.position += self.velocity * dt * 60

        def apply_gravity_acceleration(self, space_system, dt):
            if self.mass == 0:
                return
            space_system: Game.SpaceSystem
            bodies = space_system.bodies - {self}
            for body in bodies:
                body: Game.Body
                distance = np.linalg.norm(self.position - body.position)
                direction_vector = (body.position - self.position) / distance
                force = 0.1 * self.mass * body.mass / distance ** 2
                acceleration_vector = direction_vector * force / self.mass * dt * 60
                collision_handling_system = 2
                if distance < (body.radius + self.radius):
                    overlap = self.radius + body.radius - distance
                    total_mass = self.mass + body.mass
                    mass_proportion = self.mass / total_mass
                    distance = np.linalg.norm(self.position - body.position)
                    if collision_handling_system == 0:
                        continue
                    elif collision_handling_system == 1: # FIXME
                        self.position -= direction_vector * overlap * (1 - mass_proportion)
                        self.velocity -= acceleration_vector * (1 - mass_proportion)
                        body.position += direction_vector * overlap * mass_proportion
                        body.velocity += acceleration_vector * mass_proportion

                        direction_vector = (body.position - self.position) / distance
                        force = 0.1 * self.mass * body.mass / distance ** 2
                        acceleration_vector = direction_vector * force / self.mass * dt * 60

                        body.velocity += acceleration_vector
                        continue
                    elif collision_handling_system == 2:
                        space_system.remove_body(self, body)
                        new_color = mass_proportion * np.array(self.color) + (1 - mass_proportion) * np.array(body.color)
                        new_color = tuple(new_color.astype(int))
                        new_density = mass_proportion * self.density + (1 - mass_proportion) * body.density
                        new_position = self.position + direction_vector * distance / 2 * (1 - mass_proportion)
                        new_body = Game.Body(color=new_color, density=new_density, mass=total_mass, position=new_position)
                        space_system.add_body(new_body)
                        del self, body
                        return
                self.velocity += acceleration_vector

        def draw(self, surface, screen_width, screen_height):
            pos1 = self.position - (self.radius, self.radius)
            pos2 = self.position + (self.radius, self.radius)
            if is_rectangle_on_screen(pos1, pos2, screen_width, screen_height):
                pg.draw.circle(surface, self.color, self.position, self.radius)
        
        @property
        def mass(self):
            return self.density * (4 / 3) * np.pi * self.radius ** 3
        
        @mass.setter
        def mass(self, mass):
            mass = max(mass, 0)
            self.radius = (mass * 3 / (self.density * 4 * np.pi)) ** (1/3)
    
    class SpaceSystem:
        def __init__(self, bodies=None):
            self.bodies = set()
            if bodies:
                self.bodies |= set(bodies)
        
        def tick(self, dt):
            for body in self.bodies.copy():
                body: Game.Body
                body.apply_gravity_acceleration(self, dt)
                body.move(dt)
        
        def add_body(self, *bodies):
            for body in bodies:
                self.bodies.add(body)
        
        def remove_body(self, *bodies):
            for body in bodies:
                self.bodies -= {body}


if __name__ == "__main__":
    game = Game(speed=1)
    game.space_system.add_body(Game.Body(color=(255, 0, 0), position=(100, 100), radius=20))
    game.space_system.add_body(Game.Body(color=(0, 0, 255), position=(500, 500)))
    game.run()
