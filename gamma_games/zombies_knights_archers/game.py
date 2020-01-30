#!usr/bin/env python3

# Importing Libraries
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import sys
sys.dont_write_bytecode = True
import pygame
import random
import pygame.gfxdraw
from src.players import Knight, Archer
from src.zombie import Zombie
from src.weapons import Arrow, Sword
from src.variables import *
import numpy as np
import skimage
from skimage import measure

# class env(MultiAgentEnv):
class Game():
    def __init__(self, num_archers=2, num_knights=2):
        # Game Constants
        self.ZOMBIE_SPAWN = 20
        self.SPAWN_STAB_RATE = 20
        self.FPS = 15
        self.WIDTH = 1280
        self.HEIGHT = 720

        # Dictionaries for holding new players and their weapons
        self.archer_dict = {}
        self.knight_dict = {}
        self.arrow_dict = {}
        self.sword_dict = {}

        # Game Variables
        self.frame_count = 0
        self.score = 0
        self.run = True
        self.arrow_spawn_rate = self.sword_spawn_rate = self.zombie_spawn_rate = 0
        self.knight_player_num = self.archer_player_num = 0
        self.archer_killed = False
        self.knight_killed = False
        self.sword_killed = False

        # Creating Sprite Groups
        self.all_sprites = pygame.sprite.Group()
        self.zombie_list = pygame.sprite.Group()
        self.arrow_list = pygame.sprite.Group()
        self.sword_list = pygame.sprite.Group()
        self.archer_list = pygame.sprite.Group()
        self.knight_list = pygame.sprite.Group()

        self.num_archers = num_archers
        self.num_knights = num_knights
        
        # Initializing Pygame
        pygame.init()
        self.WINDOW = pygame.display.set_mode([self.WIDTH, self.HEIGHT])
        pygame.display.set_caption("Zombies, Knights, Archers")
        self.clock = pygame.time.Clock()
        self.left_wall = pygame.image.load(os.path.join('img', 'left_wall.png'))
        self.right_wall = pygame.image.load(os.path.join('img', 'right_wall.png'))
        self.right_wall_rect = self.right_wall.get_rect()
        self.right_wall_rect.left = self.WIDTH - self.right_wall_rect.width

        self.agent_list = []
        self.agent_ids = []
        self.num_agents = num_archers + num_knights
        
        # TODO: add zombie spawn rate parameter? and add max # of timesteps parameter?
        for i in range(num_archers):
            self.archer_dict["archer{0}".format(self.archer_player_num)] = Archer()
            self.archer_dict["archer{0}".format(self.archer_player_num)].offset(i * 50, 0)
            self.archer_list.add(self.archer_dict["archer{0}".format(self.archer_player_num)])
            self.all_sprites.add(self.archer_dict["archer{0}".format(self.archer_player_num)])
            self.agent_list.append(self.archer_dict["archer{0}".format(self.archer_player_num)])
            if i != num_archers - 1:
                self.archer_player_num += 1

        for i in range(num_knights):
            self.knight_dict["knight{0}".format(self.knight_player_num)] = Knight()
            self.knight_dict["knight{0}".format(self.knight_player_num)].offset(i * 50, 0)
            self.knight_list.add(self.knight_dict["knight{0}".format(self.knight_player_num)])
            self.all_sprites.add(self.knight_dict["knight{0}".format(self.knight_player_num)])
            self.agent_list.append(self.knight_dict["knight{0}".format(self.knight_player_num)])
            if i != num_knights - 1:
                self.knight_player_num += 1

        for i in range(num_archers + num_knights):
            self.agent_ids.append(i)

    # Controls the Spawn Rate of Weapons
    def check_weapon_spawn(self, sword_spawn_rate, arrow_spawn_rate):
        if sword_spawn_rate > 0:
            sword_spawn_rate += 1
        if sword_spawn_rate > 3:
            sword_spawn_rate = 0

        if arrow_spawn_rate > 0:
            arrow_spawn_rate += 1
        if arrow_spawn_rate > 3:
            arrow_spawn_rate = 0
        return sword_spawn_rate, arrow_spawn_rate

    # Spawn New Players
    class spawnPlayers(pygame.sprite.Sprite):
        def __init__(self, event, knight_player_num, archer_player_num, knight_list, archer_list, all_sprites, knight_dict, archer_dict):
            super().__init__()
            self.event = event
            self.knight_player_num = knight_player_num
            self.archer_player_num = archer_player_num
            self.knight_dict = knight_dict
            self.archer_dict = archer_dict
            self.knight_list = knight_list
            self.archer_list = archer_list
            self.all_sprites = all_sprites

        # Spawn New Knight
        def spawnKnight(self):
            # if self.event.key == pygame.K_m:
            #     self.knight_player_num += 1
            #     self.knight_dict['knight{0}'.format(self.knight_player_num)] = Knight()
            #     self.knight_list.add(self.knight_dict['knight{0}'.format(self.knight_player_num)])
            #     self.all_sprites.add(self.knight_dict['knight{0}'.format(self.knight_player_num)])
            return self.knight_player_num, self.knight_list, self.all_sprites, self.knight_dict

        # Spawn New Archer
        def spawnArcher(self):
            # if self.event.key == pygame.K_x:
            #     self.archer_player_num += 1
            #     self.archer_dict['archer{0}'.format(self.archer_player_num)] = Archer()
            #     self.archer_list.add(self.archer_dict['archer{0}'.format(self.archer_player_num)])
            #     self.all_sprites.add(self.archer_dict['archer{0}'.format(self.archer_player_num)])
            return self.archer_player_num, self.archer_list, self.all_sprites, self.archer_dict
                
    # Spawn New Weapons
    class spawnWeapons(pygame.sprite.Sprite):
        def __init__(self, action, sword_spawn_rate, arrow_spawn_rate, knight_killed, archer_killed,
                    knight_dict, archer_dict, knight_list, archer_list, knight_player_num, archer_player_num,
                    all_sprites, sword_dict, arrow_dict, sword_list, arrow_list):
            super().__init__()
            self.action = action
            self.sword_spawn_rate = sword_spawn_rate
            self.arrow_spawn_rate = arrow_spawn_rate
            self.knight_killed = knight_killed
            self.archer_killed = archer_killed
            self.knight_dict = knight_dict
            self.archer_dict = archer_dict
            self.knight_list = knight_list
            self.archer_list = archer_list
            self.knight_player_num = knight_player_num
            self.archer_player_num = archer_player_num
            self.all_sprites = all_sprites
            self.sword_dict = sword_dict
            self.arrow_dict = arrow_dict
            self.sword_list = sword_list
            self.arrow_list = arrow_list

        # Spawning Swords for Players
        def spawnSword(self):
            if (self.action == 5 and self.sword_spawn_rate == 0):
                if not self.sword_list:      # Sword List is Empty
                    if not self.knight_killed:
                        for i in range(0, self.knight_player_num + 1):
                            self.sword_dict['sword{0}'.format(i)] = Sword((self.knight_dict['knight{0}'.format(i)]))
                            self.sword_list.add(self.sword_dict[('sword{0}'.format(i))])
                            self.all_sprites.add(self.sword_dict[('sword{0}'.format(i))])
                        self.sword_spawn_rate = 1
                        self.knight_killed = False
                    else:
                        for knight in self.knight_list:
                            temp = Sword(knight)
                            self.sword_list.add(temp)
                            self.all_sprites.add(temp)
                        self.sword_spawn_rate = 1
            return self.sword_spawn_rate, self.knight_killed, self.knight_dict, self.knight_list, self.knight_player_num, self.all_sprites, self.sword_dict, self.sword_list

        # Spawning Arrows for Players
        def spawnArrow(self):
            if (self.action == 5 and self.arrow_spawn_rate == 0):
                if not self.archer_killed:
                    for i in range(0, self.archer_player_num + 1):
                        self.arrow_dict[('arrow{0}'.format(i))] = Arrow(self.archer_dict[('archer{0}'.format(i))])
                        self.arrow_list.add(self.arrow_dict[('arrow{0}'.format(i))])
                        self.all_sprites.add(self.arrow_dict[('arrow{0}'.format(i))])
                    self.arrow_spawn_rate = 1
                    self.archer_killed = False   
                else:
                    for archer in self.archer_list:
                        temp = Arrow(archer)
                        self.arrow_list.add(temp)
                        self.all_sprites.add(temp)
                    self.arrow_spawn_rate = 1
            return self.arrow_spawn_rate, self.archer_killed, self.archer_dict, self.archer_list, self.archer_player_num, self.all_sprites, self.arrow_dict, self.arrow_list

    # Stab the Sword
    def sword_stab(self, sword_list, all_sprites):
        try:
            for sword in sword_list:
                sword_active = sword.update()
                if not sword_active: # remove the sprite
                    sword_list.remove(sword)
                    all_sprites.remove(sword)
        except:
            pass
        return sword_list, all_sprites

    # Spawning Zombies at Random Location at every 100 iterations
    def spawn_zombie(self, zombie_spawn_rate, zombie_list, all_sprites):
        zombie_spawn_rate += 1
        zombie = Zombie()

        if zombie_spawn_rate >= self.ZOMBIE_SPAWN:
            zombie.rect.x = random.randrange(self.WIDTH)
            zombie.rect.y = 5

            zombie_list.add(zombie)
            all_sprites.add(zombie)
            zombie_spawn_rate = 0
        return zombie_spawn_rate, zombie_list, all_sprites

    # Zombie Kills the Knight
    def zombie_knight(self, zombie_list, knight_list, all_sprites, knight_killed, sword_list, sword_killed):
        for zombie in zombie_list:
            zombie_knight_list = pygame.sprite.spritecollide(zombie, knight_list, True)

            for knight in zombie_knight_list:
                knight.alive = False
                knight_list.remove(knight)
                all_sprites.remove(knight)
                sword_killed = True
                knight_killed = True
        return zombie_list, knight_list, all_sprites, knight_killed, sword_list, sword_killed

    # Kill the Sword when Knight dies
    def kill_sword(self, sword_killed, sword_list, all_sprites):
        for sword in sword_list:
            if sword_killed == True:
                sword_list.remove(sword)
                all_sprites.remove(sword)
                sword_killed = False
        return sword_killed, sword_list, all_sprites

    # Zombie Kills the Archer
    def zombie_archer(self, zombie_list, archer_list, all_sprites, archer_killed):
        for zombie in zombie_list:
            zombie_archer_list = pygame.sprite.spritecollide(zombie, archer_list, True)

            for archer in zombie_archer_list:
                archer.alive = False
                archer_list.remove(archer)
                all_sprites.remove(archer)
                archer_killed = True
        return zombie_list, archer_list, all_sprites, archer_killed

    # Zombie Kills the Sword
    def zombie_sword(self, zombie_list, sword_list, all_sprites, score):
        for sword in sword_list:
            zombie_sword_list = pygame.sprite.spritecollide(sword, zombie_list, True)

            # For each zombie hit, remove the sword and add to the score
            for zombie in zombie_sword_list:
                sword_list.remove(sword)
                all_sprites.remove(sword)
                zombie_list.remove(zombie)
                all_sprites.remove(zombie)
                score += 1
        return zombie_list, sword_list, all_sprites, score

    # Zombie Kills the Arrow
    def zombie_arrow(self, zombie_list, arrow_list, all_sprites, score):
        for arrow in arrow_list:
            zombie_arrow_list = pygame.sprite.spritecollide(arrow, zombie_list, True)

            # For each zombie hit, remove the arrow, zombie and add to the score
            for zombie in zombie_arrow_list:
                arrow_list.remove(arrow)
                all_sprites.remove(arrow)
                zombie_list.remove(zombie)
                all_sprites.remove(zombie)
                score += 1

            # Remove the arrow if it flies up off the screen
            if arrow.rect.y < 0:
                arrow_list.remove(arrow)
                all_sprites.remove(arrow)
        return zombie_list, arrow_list, all_sprites, score

    # Zombie reaches the End of the Screen
    def zombie_endscreen(self, run, zombie_list):
        for zombie in zombie_list:
            if zombie.rect.y > 690:
                run = False
        return run

    # Zombie Kills all Players
    def zombie_all_players(self, knight_list, archer_list, run):
        if not knight_list and not archer_list:
            run = False
        return run

    # Advance game state by 1 timestep
    def step(self, actions):
        if self.run:
            # Controls the Spawn Rate of Weapons
            self.sword_spawn_rate, self.arrow_spawn_rate = self.check_weapon_spawn(self.sword_spawn_rate, self.arrow_spawn_rate)

            for event in pygame.event.get():
                # Quit Game
                if event.type == pygame.QUIT:
                    self.run = False

                elif event.type == pygame.KEYDOWN:
                    # Quit Game            
                    if event.key == pygame.K_ESCAPE:
                        self.run = False

                    # Reset Environment
                    if event.key == pygame.K_BACKSPACE:
                        env.reset() # TODO: should "env" be "self"???

                    # TODO: FIXME:
                    # The following commented block is old code from when I controleld the agents with the keyboard
                    # It should probably be deleted, but I have kept it here just in case I need it soon for something
                    # # Spawn Players
                    # sp = self.spawnPlayers(event, self.knight_player_num, self.archer_player_num, self.knight_list, self.archer_list, self.all_sprites, self.knight_dict, self.archer_dict)
                    # # Knight
                    # self.knight_player_num, self.knight_list, self.all_sprites, self.knight_dict = sp.spawnKnight()
                    # # Archer
                    # self.archer_player_num, self.archer_list, self.all_sprites, self.archer_dict = sp.spawnArcher()

                    # # Spawn Weapons
                    # sw = self.spawnWeapons(event, self.sword_spawn_rate, self.arrow_spawn_rate, self.knight_killed, self.archer_killed, self.knight_dict, self.archer_dict, self.knight_list, self.archer_list, self.knight_player_num, self.archer_player_num, self.all_sprites, self.sword_dict, self.arrow_dict, self.sword_list, self.arrow_list)
                    # # Sword
                    # self.sword_spawn_rate, self.knight_killed, self.knight_dict, self.knight_list, self.knight_player_num, self.all_sprites, self.sword_dict, self.sword_list = sw.spawnSword()
                    # # Arrow
                    # self.arrow_spawn_rate, self.archer_killed, self.archer_dict, self.archer_list, self.archer_player_num, self.all_sprites, self.arrow_dict, self.arrow_list = sw.spawnArrow()

            # Handle agent control
            for i, agent in enumerate(self.agent_list):
                # Spawn Players
                sp = self.spawnPlayers(actions[i], self.knight_player_num, self.archer_player_num, self.knight_list, self.archer_list, self.all_sprites, self.knight_dict, self.archer_dict)
                # Knight
                self.knight_player_num, self.knight_list, self.all_sprites, self.knight_dict = sp.spawnKnight()
                # Archer
                self.archer_player_num, self.archer_list, self.all_sprites, self.archer_dict = sp.spawnArcher()

                # Spawn Weapons
                sw = self.spawnWeapons(actions[i], self.sword_spawn_rate, self.arrow_spawn_rate, self.knight_killed, self.archer_killed, self.knight_dict, self.archer_dict, self.knight_list, self.archer_list, self.knight_player_num, self.archer_player_num, self.all_sprites, self.sword_dict, self.arrow_dict, self.sword_list, self.arrow_list)
                # Sword
                self.sword_spawn_rate, self.knight_killed, self.knight_dict, self.knight_list, self.knight_player_num, self.all_sprites, self.sword_dict, self.sword_list = sw.spawnSword()
                # Arrow
                self.arrow_spawn_rate, self.archer_killed, self.archer_dict, self.archer_list, self.archer_player_num, self.all_sprites, self.arrow_dict, self.arrow_list = sw.spawnArrow()
                
                agent.update(actions[i])

            # Spawning Zombies at Random Location at every 100 iterations
            self.zombie_spawn_rate, self.zombie_list, self.all_sprites = self.spawn_zombie(self.zombie_spawn_rate, self.zombie_list, self.all_sprites)

            # Stab the Sword
            self.sword_list, self.all_sprites = self.sword_stab(self.sword_list, self.all_sprites)

            # Zombie Kills the Arrow
            self.zombie_list, self.arrow_list, self.all_sprites, self.score = self.zombie_arrow(self.zombie_list, self.arrow_list, self.all_sprites, self.score)

            # Zombie Kills the Sword
            self.zombie_list, self.sword_list, self.all_sprites, self.score = self.zombie_sword(self.zombie_list, self.sword_list, self.all_sprites, self.score)

            # Zombie Kills the Archer
            self.zombie_archer(self.zombie_list, self.archer_list, self.all_sprites, self.archer_killed)

            # Zombie Kills the Knight
            self.zombie_list, self.knight_list, self.all_sprites, self.knight_killed, self.sword_list, self.sword_killed = self.zombie_knight(self.zombie_list, self.knight_list, self.all_sprites, self.knight_killed, self.sword_list, self.sword_killed)

            # Kill the Sword when Knight dies
            self.sword_killed, self.sword_list, self.all_sprites = self.kill_sword(self.sword_killed, self.sword_list, self.all_sprites)

            # Call the update() method on sprites
            for zombie in self.zombie_list:
                zombie.update()
            arrows_to_delete = []

            for arrow in self.arrow_list:
                arrow.update()
                if not arrow.is_active():
                    arrows_to_delete.append(arrow)
            # delete arrows so they don't get rendered
            for arrow in arrows_to_delete:
                self.arrow_list.remove(arrow)
                self.all_sprites.remove(arrow)

            self.WINDOW.fill((66, 40, 53))
            self.WINDOW.blit(self.left_wall, self.left_wall.get_rect())
            self.WINDOW.blit(self.right_wall, self.right_wall_rect)
            self.all_sprites.draw(self.WINDOW)       # Draw all the sprites
            pygame.display.update()
            pygame.display.flip()                    # update screen
            self.clock.tick(self.FPS)                # FPS

            self.check_game_end()
        else:
            pass
            # TODO: End game/training here!!

        reward_dict = dict(zip(self.agent_ids, [self.score/self.num_agents]*self.num_agents)) # FIXME: change this so that each agent has its own reward

        agent_done = [agent.is_done() for agent in self.agent_list]
        done_dict = dict(zip(self.agent_ids, agent_done))
        done_dict['__all__'] = not self.run 

        # TODO: this
        # observation
        #  TODO: 
        #   - i will need to pull the red channel instead, most likely
        #   - scale down the obs for each agent so that after scaling (lambda function and skimage blokc_reduce) its 50x50
        #   - then scale from 0 to 1 and use float32


        # return observation, reward_dict, done_dict, {}

    def check_game_end(self):
        # Zombie reaches the End of the Screen
        self.run = self.zombie_endscreen(self.run, self.zombie_list)

        # Zombie Kills all Players
        self.run = self.zombie_all_players(self.knight_list, self.archer_list, self.run)

        # Condition to Check 900 Frames
        self.frame_count += 1
        if self.frame_count > 900:
            self.run = False

    def reset(self):
        # Dictionaries for holding new players and their weapons
        self.archer_dict = {}
        self.knight_dict = {}
        self.arrow_dict = {}
        self.sword_dict = {}

        # Game Variables
        self.frame_count = 0
        self.score = 0
        self.run = True
        self.arrow_spawn_rate = self.sword_spawn_rate = self.zombie_spawn_rate = 0
        self.knight_player_num = self.archer_player_num = 0
        self.archer_killed = False
        self.knight_killed = False
        self.sword_killed = False

        # Creating Sprite Groups
        self.all_sprites = pygame.sprite.Group()
        self.zombie_list = pygame.sprite.Group()
        self.arrow_list = pygame.sprite.Group()
        self.sword_list = pygame.sprite.Group()
        self.archer_list = pygame.sprite.Group()
        self.knight_list = pygame.sprite.Group()

        # Initializing Pygame
        pygame.init()
        self.WINDOW = pygame.display.set_mode([self.WIDTH, self.HEIGHT])
        pygame.display.set_caption("Zombies, Knights, Archers")
        self.clock = pygame.time.Clock()

        self.agent_list = []
        self.agent_ids = []
        
        for i in range(self.num_archers):
            self.archer_dict["archer{0}".format(self.archer_player_num)] = Archer()
            self.archer_dict["archer{0}".format(self.archer_player_num)].offset(i * 50, 0)
            self.archer_list.add(self.archer_dict["archer{0}".format(self.archer_player_num)])
            self.all_sprites.add(self.archer_dict["archer{0}".format(self.archer_player_num)])
            self.agent_list.append(self.archer_dict["archer{0}".format(self.archer_player_num)])
            if i != self.num_archers - 1:
                self.archer_player_num += 1

        for i in range(self.num_knights):
            self.knight_dict["knight{0}".format(self.knight_player_num)] = Knight()
            self.knight_dict["knight{0}".format(self.knight_player_num)].offset(i * 50, 0)
            self.knight_list.add(self.knight_dict["knight{0}".format(self.knight_player_num)])
            self.all_sprites.add(self.knight_dict["knight{0}".format(self.knight_player_num)])
            self.agent_list.append(self.knight_dict["knight{0}".format(self.knight_player_num)])
            if i != self.num_knights - 1:
                self.knight_player_num += 1

        for i in range(self.num_archers + self.num_knights):
            self.agent_ids.append(i)

if __name__ == "__main__":
    g = Game()
    # for i in range(40):
    #     actions = [random.randint(1, 5), random.randint(1, 5), random.randint(1, 5), random.randint(1, 5)]
    #     actions = [random.randint(1, 5), random.randint(1, 5), random.randint(1, 5), random.randint(1, 5)]
    #     print(actions)
    #     g.step(actions)
    # g.reset()
    for i in range(40000):
        actions = [random.randint(1, 5), random.randint(1, 5), random.randint(1, 5), random.randint(1, 5)]
        # actions = [1,1,1,1,1]
        g.step(actions)