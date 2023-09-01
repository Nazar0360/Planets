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

def is_rectangle_on_screen(pos1, pos2, surface_size):
    x1, y1 = pos1
    x2, y2 = pos2

    if x1 > surface_size[0] and x2 > screen_size[0]:
        return False
    if x1 < 0 and x2 < 0:
        return False
    if y1 > surface_size[1] and y2 > screen_size[1]:
        return False
    if y1 < 0 and y2 < 0:
        return False
    return True

class Game:
    def __init__(self, screen_size=(800, 600), fps=60, speed=1):
        pg.init()
        self.screen = pg.display.set_mode(screen_size)
        self.clock = pg.time.Clock()
        self.fps = fps
        self.speed = speed
        
        self.space_system = Game.SpaceSystem(screen_size)
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
            self.space_system.add(self.body_to_launch)
            self.body_to_launch = None

    def handle_mousewheel(self, y):
        if self.body_to_launch:
            if pg.key.get_mods() & pg.KMOD_ALT:
                self.body_to_launch.density = max(self.body_to_launch.density + y, 1)
                return
            self.body_to_launch.radius = max(self.body_to_launch.radius + y, 1)

    def update_screen(self):
        self.screen.fill((0, 0, 0))
        self.space_system.draw(self.screen)
        if self.body_to_launch:
            pg.draw.line(self.screen, (255, 255, 255), self.body_to_launch.position, self.body_to_launch.position * 2 - pg.mouse.get_pos())
        if self.body_to_launch:
            self.body_to_launch.draw(self.screen)

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
            elif radius is not None and density is not None and mass is not None:
                raise ValueError("Invalid combination of parameters: radius, density, and mass cannot all be provided simultaneously")
            else:
                radius = 10 if radius is None else radius
                density = 1 if density is None else density
            self.radius = float(radius)
            self.density = float(density)
            self.velocity = np.array(velocity, dtype=np.float64)
            self.position = np.array(position, dtype=np.float64)
            self.recoil = np.array([0, 0], dtype=np.float64)

        def move(self, dt: float):
            self.position += self.velocity * dt * 60
            self.position -= self.recoil
            self.recoil *= 0

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
                if distance < (body.radius + self.radius):
                    overlap = self.radius + body.radius - distance
                    total_mass = self.mass + body.mass
                    mass_proportion = self.mass / total_mass
                    distance = np.linalg.norm(self.position - body.position)
                    self.recoil = direction_vector * overlap * (1 - mass_proportion)
                    self.velocity -= acceleration_vector * (1 - mass_proportion)
                    body.recoil = -direction_vector * overlap * mass_proportion
                    body.velocity += acceleration_vector * mass_proportion
                    continue
                self.velocity += acceleration_vector

        def draw(self, surface: pg.SurfaceType):
            surface_size = surface.get_size()
            pos1 = self.position - (self.radius, self.radius)
            pos2 = self.position + (self.radius, self.radius)
            if is_rectangle_on_screen(pos1, pos2, surface_size):
                pg.draw.circle(surface, self.color, self.position, self.radius)

        @property
        def mass(self):
            return self.density * (4 / 3) * np.pi * self.radius ** 3
        
        @mass.setter
        def mass(self, mass):
            mass = max(mass, 0)
            self.radius = (mass * 3 / (self.density * 4 * np.pi)) ** (1/3)
    
    class SpaceSystem:
        def __init__(self, screen_size=None, *bodies):
            self.bodies = set()
            if bodies:
                self.bodies |= set(bodies)
            
            if screen_size is None:
                screen_size = pg.display.get_window_size()
            self.surface = pg.Surface(screen_size, flags=pg.SRCALPHA)
        
        def tick(self, dt):
            bodies = self.bodies.copy()
            for body in bodies:
                body: Game.Body
                body.apply_gravity_acceleration(self, dt)
            for body in bodies:
                body: Game.Body
                body.move(dt)
        
        def draw(self, surface: pg.SurfaceType):
            overlay_surface = pg.Surface(self.surface.get_size(), pg.SRCALPHA)
            overlay_surface.fill((0,0,0,15))
            self.surface.blit(overlay_surface, (0,0))
            for body in self.bodies:
                body: Game.Body
                body.draw(self.surface)
            surface.blit(self.surface, (0, 0))

        def add(self, *bodies):
            for body in bodies:
                self.bodies.add(body)
        
        def remove(self, *bodies):
            for body in bodies:
                self.bodies -= {body}
        
        def spawn_bodies_on_circle(self, num_bodies, center, radius, velocity_magnitude):
            bodies = []
            angle_increment = 360 / num_bodies

            for i in range(num_bodies):
                angle = i * angle_increment
                hue = angle % 360
                x = center[0] + radius * np.cos(np.radians(angle))
                y = center[1] + radius * np.sin(np.radians(angle))
                velocity_x = -velocity_magnitude * np.sin(np.radians(angle))
                velocity_y = velocity_magnitude * np.cos(np.radians(angle))
                color = hsv_to_rgb(hue, 1, 1)
                body = Game.Body(position=(x, y), velocity=(velocity_x, velocity_y), color=color)
                bodies.append(body)
            
            self.add(*bodies)
        
        def resize_surface(self, new_size):
            new_surface = pg.Surface(new_size, flags=pg.SRCALPHA)
            new_surface.blit(self.surface, (0, 0))
            self.surface = new_surface


if __name__ == "__main__":
    screen_size = np.array([1000, 1000])
    game = Game(screen_size)
    game.space_system.spawn_bodies_on_circle(10, screen_size / 2, 200, 1.5)
    game.run()
