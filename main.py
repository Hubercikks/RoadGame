import os
import pygame
import random

pygame.init()
pygame.display.set_caption("RoadRide")

SIZESCREEN = WIDTH, HEIGHT = 1000, 800
DARKRED = pygame.color.THECOLORS['darkred']
BLUE = pygame.color.THECOLORS['lightblue']

path = "textures"
path2 = os.path.join(os.getcwd(), 'music')
print("PATH: ", path)
if not os.path.exists(path):
    raise FileNotFoundError("The 'textures' folder does not exist.")
file_names = os.listdir(path)
if 'background.png' not in file_names:
    raise FileNotFoundError("The 'background.png' file is missing in the textures folder.")
screen = pygame.display.set_mode(SIZESCREEN)
BACKGROUND = pygame.image.load(os.path.join(path, 'background.png')).convert()
BACKGROUND = pygame.transform.scale(BACKGROUND, (WIDTH, HEIGHT))
file_names.remove('background.png')

IMAGES = {file_name[:-4].upper(): pygame.image.load(os.path.join(path, file_name)).convert_alpha() for file_name in
          file_names}

OTHER_CAR_IMAGES = [IMAGES[name] for name in IMAGES if 'OTHERCAR' in name]


if os.path.exists('score.txt'):
    try:
        with open('score.txt', 'r') as file:
            highest_score = int(file.read().strip())
    except ValueError as e:
        print(f"Error reading highest score from file: {e}")
        highest_score = 0
else:
    highest_score = 0

game_over_sound = pygame.mixer.Sound(os.path.join(path2, 'game_over.ogg'))
crash_sound = pygame.mixer.Sound(os.path.join(path2, 'crash.ogg'))
game_music_loop = pygame.mixer.Sound(os.path.join(path2, 'game_music_loop.ogg'))
button_sound = pygame.mixer.Sound(os.path.join(path2, 'button.ogg'))
game_music_loop.set_volume(0.01)
pygame.font.init()


class Player(pygame.sprite.Sprite):
    def __init__(self, image, c_x, c_y):
        super().__init__()
        self.original_image = image
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(c_x, c_y))
        self.lives = 3
        self.points = 0
        self.speed = 5
        self.invincible = False
        self.invincible_start_time = 0
        self.blink = False
        self.blink_start_time = 0

    def draw(self, surface):
        if not self.blink or (pygame.time.get_ticks() // 250) % 2 == 0:
            surface.blit(self.image, self.rect)

    def update(self, key_pressed):
        self._get_event(key_pressed)
        self.rect.top = max(self.rect.top, 0)
        self.rect.bottom = min(self.rect.bottom, 750)
        self.rect.centerx = max(min(self.rect.centerx, 800), 250)
        if self.invincible and pygame.time.get_ticks() - self.invincible_start_time > 3000:
            self.invincible = False
        if self.blink and pygame.time.get_ticks() - self.blink_start_time > 2000:
            self.blink = False

    def _get_event(self, key_pressed):
        if key_pressed[pygame.K_LEFT]:
            self.rect.move_ip(-self.speed, 0)
        if key_pressed[pygame.K_RIGHT]:
            self.rect.move_ip(self.speed, 0)
        if key_pressed[pygame.K_UP]:
            self.rect.move_ip(0, -self.speed)
        if key_pressed[pygame.K_DOWN]:
            self.rect.move_ip(0, self.speed)


class Road:
    def __init__(self, image):
        self.image = image
        self.scroll_y = 0
        self.speed = 10

    def update(self):
        self.scroll_y = (self.scroll_y + self.speed) % HEIGHT

    def draw(self, surface):
        surface.blit(self.image, (0, self.scroll_y))
        surface.blit(self.image, (0, self.scroll_y - HEIGHT))


class Othercars(pygame.sprite.Sprite):
    def __init__(self, image, movement_y, name, all_sprites_group):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.movement_y = movement_y
        self.name = name
        self.all_sprites_group = all_sprites_group
        self.collision_rect = self.rect.inflate(-self.rect.width * 0.2,
                                                -self.rect.height * 0.2)
        self.reset_position()

    def reset_position(self):
        self.rect.centerx = random.randint(250, 800)
        self.rect.y = random.randint(-HEIGHT, -100)
        self.collision_rect.center = self.rect.center

    def update(self):
        self.rect.y += self.movement_y
        self.collision_rect.center = self.rect.center

        collided_sprites = pygame.sprite.spritecollide(self, self.all_sprites_group, False)
        if len(collided_sprites) > 1:
            self.reset_position()
            print("Collided, resetting")
            return

        if self.rect.top > HEIGHT:
            print(f"{self.name} off screen, resetting position.")
            self.reset_position()


class Text:
    def __init__(self, text, color, cx, cy, font_size=36, font_family=None):
        self.rect = None
        self.image = None
        self.text = str(text)
        self.color = color
        self.cx = cx
        self.cy = cy
        self.font = pygame.font.SysFont(font_family, font_size)
        self.update()

    def update(self):
        self.image = self.font.render(self.text, 1, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = self.cx, self.cy

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Level:
    def __init__(self, player_s):
        self.player = player_s
        self.set_of_bonus = pygame.sprite.Group()

    def draw(self, surface):
        for i in range(self.player.lives):
            surface.blit(IMAGES['PLAYERLIFE'], (20 + i * 50, 20))
        font_s = pygame.font.Font(None, 36)
        text_s = font_s.render(f"Points: {self.player.points}", True, BLUE)
        surface.blit(text_s, (WIDTH - 150, 20))

    def update(self):
        self.set_of_bonus.update()


class Obstacle(Othercars):
    def speed_difference(self):
        self.movement_y = self.movement_y//2


class Button:
    def __init__(self, text, text_color, background_color, cx, cy, width, height, font_size=36, font_family=None):
        self.text = Text(text, text_color, cx, cy, font_size, font_family)
        self.background_color = background_color
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = self.text.rect.center

    def draw(self, surface):
        surface.fill(self.background_color, self.rect)
        self.text.update()
        self.text.draw(surface)


player_image_key = next((name for name in IMAGES if 'CAR' in name), None)
if player_image_key:
    player_image = IMAGES[player_image_key]
else:
    raise ValueError("No 'CAR' image found in textures folder.")

player_image = pygame.transform.scale(player_image, (player_image.get_width(), player_image.get_height()))
player = Player(player_image, WIDTH // 2, 600)
player.image = pygame.transform.rotate(player.image, -90)
player.rect = player.image.get_rect(center=player.rect.center)

end_text = Text('KONIEC GRY', BLUE, WIDTH // 2, HEIGHT // 2, font_size=128, font_family='Arial')
final_score_text = Text(f'WYNIK: {player.points}', BLUE, WIDTH // 2, HEIGHT // 2 + 100, font_size=64,
                        font_family='Arial')
othercars_sprites = pygame.sprite.Group()
start_button = Button('START', 'white', BLUE, WIDTH // 2, HEIGHT // 2 - 300, 500, 150, font_size=72,
                      font_family='Arial')
quit_button = Button('QUIT', 'white', BLUE, WIDTH // 2, HEIGHT // 2 + 100, 500, 150, font_size=72, font_family='Arial')
show_score_button = Button('HIGHEST SCORE', 'white', BLUE, WIDTH // 2, HEIGHT // 2 - 100, 500, 150, font_size=72,
                           font_family='Arial')
all_sprites = pygame.sprite.Group()
highest_score_text = Text(f'NAJWYŻSZY WYNIK: {highest_score}', BLUE, WIDTH // 2, HEIGHT // 2, font_size=63,
                          font_family='Arial')

road = Road(BACKGROUND)
level = Level(player)
clock = pygame.time.Clock()
a = 11
if player.points > 1000:
    a = 13
elif player.points > 2000:
    a = 15
elif player.points > 3000:
    a = 17
for _ in range(a):
    othercar_image = random.choice(OTHER_CAR_IMAGES)
    othercar_image1 = pygame.transform.scale(othercar_image,
                                             (othercar_image.get_width() // 1.5, othercar_image.get_height() // 1.5))
    othercar_image2 = pygame.transform.rotate(othercar_image1, 90)
    othercar = Othercars(othercar_image2, 5, "OTHERCAR", all_sprites)

    if not pygame.sprite.spritecollideany(othercar, all_sprites):
        all_sprites.add(othercar)
        othercars_sprites.add(othercar)

    else:
        othercar.reset_position()
running = True
active = True
game_over_time = None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            active = not active
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if start_button.rect.collidepoint(event.pos):
                game_music_loop.stop()
                button_sound.play()
                player.lives = 3
                player.points = 0
                player.rect.center = (WIDTH // 2, 600)
                active = True
                game_over_time = None
                pygame.time.delay(200)
            if show_score_button.rect.collidepoint(event.pos):
                game_music_loop.stop()
                button_sound.play()
                screen.fill('white')
                with open('score.txt', 'r') as file:
                    highest_score = int(file.read().strip())
                    print("Reading file")
                highest_score_text = Text(f'NAJWYŻSZY WYNIK: {highest_score}', BLUE, WIDTH // 2, HEIGHT // 2,
                                              font_size=63,
                                              font_family='Arial')
                highest_score_text.draw(screen)
                pygame.display.flip()
                pygame.time.delay(2000)
                print("Showing highest score")

            elif quit_button.rect.collidepoint(event.pos):
                game_music_loop.stop()
                button_sound.play()
                running = False
    if active:
        pygame.display.flip()
        road.update()
        road.draw(screen)

        player.update(pygame.key.get_pressed())
        player.draw(screen)

        othercars_sprites.update()
        othercars_sprites.draw(screen)

        level.draw(screen)
        game_music_loop.play()
        player.points += 1
        collided_car = pygame.sprite.spritecollideany(player, othercars_sprites)
        if collided_car and not player.invincible:
            player.lives -= 1
            game_music_loop.stop()
            crash_sound.play()
            player.invincible = True
            player.invincible_start_time = pygame.time.get_ticks()
            player.blink = True
            player.blink_start_time = pygame.time.get_ticks()

            othercars_sprites.remove(collided_car)
            all_sprites.remove(collided_car)

            if player.lives <= 0:
                pygame.display.flip()
                game_over_time = pygame.time.get_ticks()
                active = False
                end_text.draw(screen)
                if player.points > highest_score:
                    screen.fill('white')
                    new_highest_score = player.points
                    new_highest_score_text = Text(f'NOWY NAJWYŻSZY WYNIK: {new_highest_score}', BLUE, WIDTH // 2,
                                                  HEIGHT // 2, font_size=63,
                                                  font_family='Arial')
                    new_highest_score_text.draw(screen)
                    pygame.display.flip()
                    pygame.time.delay(2000)
                    with open('score.txt', 'w') as file:
                        file.write(str(player.points))
                        print("Writing to file")
                else:
                    print("Points smaller than highest score")
                final_score_text = Text(f'WYNIK: {player.points}', BLUE, WIDTH // 2, HEIGHT // 2 + 100, font_size=64,
                                        font_family='Arial')
                final_score_text.draw(screen)

    else:
        current_time = pygame.time.get_ticks()
        if game_over_time:
            if current_time - game_over_time < 5000:
                road.draw(screen)
                end_text.draw(screen)
                final_score_text.draw(screen)
                game_music_loop.stop()
                game_over_sound.play()
                pygame.time.delay(500)
            else:
                game_over_time = None
                active = False
        else:
            screen.fill('white')
            start_button.draw(screen)
            show_score_button.draw(screen)
            quit_button.draw(screen)

    pygame.display.flip()
    clock.tick(60)
pygame.quit()
