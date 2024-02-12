import arcade
from random import *
import matplotlib.pyplot as plt
import pickle
import math
import time
from os.path import exists

# RADAR ?
# Direction de la sortie : 0...7
# Murs en connexitÃ© 4 (H, B, G, D) : Rien, mur ou goal

# J'ai modifié les valeurs pour essayer d'améliorer
REWARD_WALL = -5  # Moins sévère pour encourager l'exploration
REWARD_DEFAULT = -1  # Légère pénalité pour chaque pas, encourage la recherche de chemin optimal
#REWARD_BAD_SHOOT = -2  # Pénalité pour un tir inutile
REWARD_GOAL = 100  # Récompense significative pour atteindre l'objectif
ALL_DESTROY = 1000
REWARD_ALL_SHOOT = 500

MAP_START = '.'
MAP_GOAL = '*'
MAP_WALL = '#'

NB_SHOOT = 50000

ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT = 'U', 'D', 'L', 'R'
ACTION_SHOOT = 'S'
ACTIONS = [ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT, ACTION_SHOOT]

MOVES = {ACTION_UP: (-1, 0),
         ACTION_DOWN: (1, 0),
         ACTION_LEFT: (0, -1),
         ACTION_RIGHT: (0, 1),
        }

SPRITE_SCALE = 0.4
SPRITE_SIZE = int(SPRITE_SCALE * 128)

AGENT_FILE = 'agent.qtable'


def sign(x):
    return 1 if x > 0 else -1 if x < 0 else 0


class Environment:
    def __init__(self):     
        self.map = {}
        self.nb_shoot = NB_SHOOT
        self.goal = []
        self.angle = 180.0
        self.init_map()
        self.start = (0, 0)
        self.height = 15
        self.width = 28

    def init_map(self):
        self.nb_shoot = NB_SHOOT
        nbAsteriod = 0
        self.map.clear()
        self.goal = []
        row, col = 0, 0
        for col in range(0, 28):
            for row in range(0, 15):
                chance = random()
                if chance < 0.05 and col != 0 and row != 0 and nbAsteriod < 15:
                    self.map[row, col] = MAP_GOAL
                    self.goal.append((row, col))
                    nbAsteriod = nbAsteriod + 1
                else:
                    self.map[row, col] = " "
        print(self.count_asteroids())

    def get_radar(self, state):
        row, col = state
        next_target = self.find_closet_tuple(state)
        radar_direction = [0] * 8  # Initialise toutes les directions à 0
        
        if next_target is not None:
            # Calculez la direction vers la cible la plus proche
            delta_row = next_target[0] - row
            delta_col = next_target[1] - col
            direction = math.atan2(delta_row, delta_col)
            direction_degrees = math.degrees(direction) % 360

            # Ajustez la direction en fonction de l'angle du vaisseau
            adjusted_direction_degrees = (direction_degrees - self.angle) % 360

            # Utilisez l'angle ajusté pour déterminer la direction du radar
            if 337.5 < adjusted_direction_degrees or adjusted_direction_degrees <= 22.5:
                radar_direction[1] = 1  # N
            elif 22.5 < adjusted_direction_degrees <= 67.5:
                radar_direction[0] = 1  # NE
            elif 67.5 < adjusted_direction_degrees <= 112.5:
                radar_direction[3] = 1  # E
            elif 112.5 < adjusted_direction_degrees <= 157.5:
                radar_direction[5] = 1  # SE
            elif 157.5 < adjusted_direction_degrees <= 202.5:
                radar_direction[6] = 1  # S
            elif 202.5 < adjusted_direction_degrees <= 247.5:
                radar_direction[7] = 1  # SO
            elif 247.5 < adjusted_direction_degrees <= 292.5:
                radar_direction[4] = 1  # O
            elif 292.5 < adjusted_direction_degrees <= 337.5:
                radar_direction[2] = 1  # NO
        return tuple(radar_direction)


    def count_asteroids(self): 
        return sum(1 for cle, valeur in self.map.items() if valeur == "*")
    
    def find_closet_tuple(self, pos):
        closest = None
        min_distance = float('inf')

        for point in self.goal:
            distance = math.sqrt((point[0] - pos[0])**2 + (point[1] -  pos[1])**2)
            if distance < min_distance:
                min_distance = distance
                closest = point

        return closest

    #a changer 
    def do(self, state, action):
        reward = 0

        directions = {
            0: (-1, 0),  # Haut
            90: (0, 1),  # Droite
            180: (1, 0),  # Bas
            270: (0, -1),  # Gauche
            45: (-1, 1),  # Haut Droite
            135: (1, 1),  # Bas Droite
            225: (1, -1),  # Bas Gauche
            315: (-1, -1),  # Haut Gauche
        }
        shoot = False
        if (action == 'S'):
            #print("shoot")
            shoot = True
            move = state
        elif action == ACTION_UP or action == ACTION_DOWN:
            test = directions[self.angle % 360]
            move = test
        else:
            if action == ACTION_RIGHT:
                self.angle = (self.angle + 45) % 360
            elif action == ACTION_LEFT:
                self.angle = (self.angle - 45) % 360
            move = state
        new_state = (state[0] + move[0], state[1] + move[1])

        if shoot: 
            self.nb_shoot = self.nb_shoot - 1    
            if self.is_destroyed(move):
                if self.count_asteroids() != 0:
                    reward = REWARD_GOAL
                else:
                    reward = ALL_DESTROY
            else :
                if self.nb_shoot <= 0:
                    reward = REWARD_ALL_SHOOT
        else :
            if self.is_allowed(new_state):
                reward = REWARD_WALL
            else:
                state = new_state
                reward = REWARD_DEFAULT

       
        #print(self.nb_shoot)
        return self.get_radar(state), state, reward

    def is_destroyed(self, position):
        row, col = position
        destroyed = False

        #liste des directions de vérification basée sur l'angle
        directions = {
            0: (-1, 0),  # Haut
            90: (0, 1),  # Droite
            180: (1, 0),  # Bas
            270: (0, -1),  # Gauche
            45: (-1, 1),  # Haut Droite
            135: (1, 1),  # Bas Droite
            225: (1, -1),  # Bas Gauche
            315: (-1, -1),  # Haut Gauche
        }

        #la on obtient la direction de vérification basé sur l'angle actuel
        dir_row, dir_col = directions[self.angle % 360]

        #je vérifie de la destruction dans la direction jusqu'à la première occurrence d'un astéroïde
        check_row, check_col = row + dir_row, col + dir_col
        while 0 <= check_row < self.height and 0 <= check_col < self.width:
            if self.map.get((check_row, check_col)) == MAP_GOAL:
                #on dit que l'astéroide est détruit 
                self.map[check_row, check_col] = " "
                self.goal.remove((check_row, check_col))
                destroyed = True
                break
            check_row += dir_row
            check_col += dir_col

        if destroyed:
            print("Astéroïde détruit. Nombre restant :", self.count_asteroids())
            print(self.goal)

        return destroyed


    def is_allowed(self, state):
        return state not in self.map \
            or self.map[state] in [MAP_START, MAP_WALL] or state in self.goal


def arg_max(table):
    return max(table, key=table.get)

## Tourne un sprit
class TurningSprite(arcade.Sprite):
    def update(self):
        super().update()
        self.angle = math.degrees(math.atan2(self.change_y, self.change_x))


class Agent:
    def __init__(self, env, learning_rate = 0.5, discount_factor = 0.9):
        self.env = env
        self.reset()
        self.qtable = {}
        self.add_state(self.state)
                
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.history = []
        self.noise = 0

    def reset(self):
        self.position = env.start
        self.env.init_map()
        self.score = 0
        self.iteration = 0
        self.state = self.env.get_radar(self.position)

    def best_action(self):
        if random() < self.noise:
            return choice(ACTIONS)
        else:
            return arg_max(self.qtable[self.state])

    def do(self):
        action = self.best_action()
        new_state, position, reward = self.env.do(self.position, action)
        #new_state, reward = self.env.do(self.state, action)
        self.score += reward
        self.iteration += 1
        self.position = position

        #Q-learning
        self.add_state(new_state)        
        maxQ = max(self.qtable[new_state].values())
        delta = self.learning_rate * (reward + self.discount_factor * maxQ \
                              - self.qtable[self.state][action])
        self.qtable[self.state][action] += delta
        self.state = new_state

        if self.env.count_asteroids() == 0 :
            self.history.append(self.score)
            self.noise *= 1 - 1E-1
        
        return action, reward
    
    def add_state(self, state):
        if state not in self.qtable:
            self.qtable[state] = {}
            for action in ACTIONS:
                self.qtable[state][action] = 0.0

    def load(self, filename):
        if exists(filename):
            with open(filename, 'rb') as file:
                self.qtable = pickle.load(file)
            self.reset()

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self.qtable, file)


class MazeWindow(arcade.Window):
    def __init__(self, agent):
        super().__init__(SPRITE_SIZE * env.width,
                         SPRITE_SIZE * env.height, "ESGI Maze")
        self.rate = 0.6
        self.env = agent.env
        self.agent = agent
        self.background = arcade.load_texture("univers.jpg")
        self.set_update_rate(0.01)
        

    def state_to_xy(self, state):
        return (state[1] + 0.5) * SPRITE_SIZE, \
               (self.env.height - state[0] - 0.5) * SPRITE_SIZE

    def setup(self):
        self.goal = arcade.SpriteList()
        self.radar = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.display_meteor()
        self.player = arcade.Sprite(":resources:images/space_shooter/playerShip1_green.png", SPRITE_SCALE)
        self.update_player()

    def display_meteor(self):
        self.goal = arcade.SpriteList()
        print(f"Nombre d'astéroïdes avant initialisation: {len(self.goal)}")
        for state in self.env.goal:
            i = randint(1, 4)
            exit = arcade.Sprite(":resources:images/space_shooter/meteorGrey_big"+str(i)+".png", SPRITE_SCALE)
            exit.center_x, exit.center_y = self.state_to_xy(state)
            self.goal.append(exit)
        print(f"Nombre d'astéroïdes après initialisation: {len(self.goal)}")


    def on_draw(self):
        arcade.start_render()
        arcade.draw_texture_rectangle(self.width // 2, self.height // 2,
                                      self.width, self.height,
                                      self.background)
        self.goal.draw()
        self.player.draw()
        self.bullet_list.draw()
        self.player.angle = self.env.angle
        arcade.draw_text(f'{self.agent.iteration} Score: {self.agent.score} Noise: {self.agent.noise}',
                         10, 10, arcade.color.RED, 24, bold=True)
        
        self.draw_radar()
        

    def draw_radar(self):
        radar_positions = self.env.get_radar(self.agent.position)
        directions = [(-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0)]  # HG, H, HO, E, BG, S, BO, O
        
        for i, radar_state in enumerate(radar_positions):
            sprite_path = ":resources:images/items/gemRed.png" if radar_state == 1 else ":resources:images/items/gemYellow.png"
            sprite = arcade.Sprite(sprite_path, SPRITE_SCALE)
            
            # Calcule la position du sprite basée sur la direction du radar et la position du vaisseau
            dir_x, dir_y = directions[i]
            ship_x, ship_y = self.state_to_xy(self.agent.position)
            sprite.center_x = ship_x + dir_x * SPRITE_SIZE
            sprite.center_y = ship_y + dir_y * SPRITE_SIZE
            print(radar_state)
            print(dir_x, sprite.center_y)
              
            sprite.draw()
        print(radar_positions)
        time.sleep(600)

            


    def on_update(self, delta_time):
        if self.env.nb_shoot <= 0 or self.agent.position in self.env.goal:
            self.bullet_list = arcade.SpriteList()
            self.agent.reset()
            self.display_meteor()
            self.goal.draw()
        elif self.env.count_asteroids() != 0:
            action, reward = self.agent.do()
            if action != "S":
                self.update_player()
            else:
                self.shoot()
            self.bullet_list.update()

            for bullet in self.bullet_list:
                asteroids = arcade.check_for_collision_with_list(bullet, self.goal)
                for asteroid in asteroids:
                    asteroid.remove_from_sprite_lists()
                    bullet.remove_from_sprite_lists()
        else:
            self.bullet_list = arcade.SpriteList()
            self.agent.reset()
            self.display_meteor()
            self.goal.draw()

    def shoot(self):
        bullet_sprite = TurningSprite(":resources:images/space_shooter/laserBlue01.png", SPRITE_SCALE)
        bullet_sprite.center_x, bullet_sprite.center_y = self.state_to_xy(self.agent.position)
        bullet_sprite.angle = self.env.angle

        bullet_speed = 13
        bullet_sprite.change_y = math.cos(math.radians(self.env.angle)) * bullet_speed
        bullet_sprite.change_x = -math.sin(math.radians(self.env.angle)) * bullet_speed
        bullet_sprite.update()
        self.bullet_list.append(bullet_sprite)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            self.bullet_list = arcade.SpriteList()
            self.agent.reset()
            self.display_meteor()
            self.goal.draw()
        elif key == arcade.key.X:
            self.agent.noise = 1
            self.agent.reset()
        elif key == arcade.key.P:
            time.sleep(60)
        elif key == arcade.key.U:
            self.set_update_rate(0.1)
        elif key == arcade.key.I:
            self.set_update_rate(0.01)
        self.update_player()

    def update_player(self): 
        self.player.center_x, self.player.center_y = self.state_to_xy(self.agent.position)
        self.player.angle = self.env.angle


if __name__ == '__main__':
    env = Environment()
    #print(env.start, env.goal)
    #print(len(env.map))
    #print(f'Shape = {env.width} x {env.height}')

    agent = Agent(env)
    agent.load(AGENT_FILE)

    #print(agent.qtable)

    window = MazeWindow(agent)
    window.setup()
    window.run()

    agent.save(AGENT_FILE)

    #print(agent.history)
    plt.plot(agent.history)
    plt.show()
