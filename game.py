import arcade
from random import *
import matplotlib.pyplot as plt
import pickle
import math
from os.path import exists

# RADAR ?
# Direction de la sortie : 0...7
# Murs en connexitÃ© 4 (H, B, G, D) : Rien, mur ou goal


REWARD_WALL = -128
REWARD_DEFAULT = -1
REWARD_BAD_SHOOT = -0.8
REWARD_GOAL = 64

MAP_START = '.'
MAP_GOAL = '*'
MAP_WALL = '#'

ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT = 'U', 'D', 'L', 'R'
ACTION_SHOOT = 'S'
ACTIONS = [ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT, ACTION_SHOOT]

MOVES = {ACTION_UP: (-1, 0),
         ACTION_DOWN: (1, 0),
         ACTION_LEFT: (0, -1),
         ACTION_RIGHT: (0, 1)}

SPRITE_SCALE = 0.4
SPRITE_SIZE = int(SPRITE_SCALE * 128)

AGENT_FILE = 'agent.qtable'


def sign(x):
    return 1 if x > 0 else -1 if x < 0 else 0


class Environment:
    def __init__(self):
        row, col = 0, 0
        self.map = {}
        self.goal = []
        self.angle = 180.0
        self.map[0, 0] = " "
        for col in range(0, 28):
            for row in range(0, 15):
                chance = random()
                if chance < 0.05 and col != 0 and row != 0:
                    self.map[row, col] = MAP_GOAL
                    self.goal.append((row, col))
                else:
                    self.map[row, col] = " "
                ##if char == MAP_START:
                ##    
                ##elif char == MAP_GOAL:
                ##   

        self.start = (0, 0)
        self.height = 15
        self.width = 28

    def get_radar(self, state):
        row, col = state[0], state[1]
        neighbors = [(row - 1, col), (row, col - 1), (row + 1, col), (row, col + 1)]
        radar = []
        for n in neighbors:
            if n in self.map:
                radar.append(self.map[n])
            else:
                radar.append(MAP_WALL)
        delta_row = sign(self.goal[0] - row[0]) + 1
        delta_col = sign(self.goal[1] - row[1]) + 1
        radar_goal = [0] * 9

        position = delta_row * 3 + delta_col
        radar_goal[position] = 1

        return radar + radar_goal

    def do(self, state, action):
        shoot = False
        if (action == 'S'):
            print("shoot")
            shoot = True
            move = state
        elif action == ACTION_UP or action == ACTION_DOWN:
            if self.angle == 90:
                action = ACTION_RIGHT
            if self.angle == 270:
                action = ACTION_LEFT
            move = MOVES[action]
        else:
            if action == ACTION_RIGHT and self.angle < 360:
                self.angle = self.angle + 90
            if action == ACTION_LEFT and self.angle > 0:
                self.angle = self.angle - 90
            move = state
        new_state = (state[0] + move[0], state[1] + move[1])

        if shoot == True:
            print(move)       
            if self.is_destroyed(move):
                reward = REWARD_GOAL
            else :
                reward = REWARD_DEFAULT
        else :
            if self.is_allowed(new_state):
                reward = REWARD_WALL
            else:
                state = new_state
                if new_state == self.goal:
                    reward = REWARD_GOAL
                else:
                    reward = REWARD_DEFAULT

        return state, reward

    def is_destroyed(self, move):
        print('passage dans la fonction, angle de : ' + str(self.angle))
        if (self.angle%360 == 90):
            i = move[0]
            while i > 0:
                if self.map[i, move[1]] == MAP_GOAL:
                    self.map[i, move[1]] = " "
                    print("GG")
                    return True
                i = i - 1
        if (self.angle%360 == 270):
            i = move[0]
            while i < 15:
                if self.map[i, move[1]] == MAP_GOAL:
                    self.map[i, move[1]] = " "
                    print("GG")
                    return True
                i = i + 1
        if (self.angle%360 == 0 ):
            i = move[1]
            while i > 0:
                if self.map[move[0], i] == MAP_GOAL:
                    self.map[move[0], i] = " "
                    print("GG")
                    return True
                i = i - 1
        if (self.angle%360 == 180):
            i = move[0]
            while i < 28:
                if self.map[move[0], i] == MAP_GOAL:
                    self.map[move[0], i] = " "
                    print("GG")
                    return True
                i = i + 1
        
        return False

    def is_allowed(self, state):
        return state not in self.map \
            or self.map[state] in [MAP_START, MAP_WALL]


def arg_max(table):
    return max(table, key=table.get)

## Tourne un sprit
class TurningSprite(arcade.Sprite):
    def update(self):
        super().update()
        self.angle = math.degrees(math.atan2(self.change_y, self.change_x))


class Agent:
    def __init__(self, env, learning_rate=1, discount_factor=0.9):
        self.env = env
        self.reset()
        self.qtable = {}
        for state in env.map:
            self.qtable[state] = {}
            for action in ACTIONS:
                self.qtable[state][action] = 0.0

        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.history = []
        self.noise = 0

    def reset(self):
        self.state = env.start
        self.score = 0
        self.iteration = 0

    def best_action(self):
        if random() < self.noise:
            return choice(ACTIONS)
        else:
            return arg_max(self.qtable[self.state])

    def do(self):
        action = self.best_action()
        new_state, reward = self.env.do(self.state, action)
        self.score += reward
        self.iteration += 1

        # Q-learning
        self.qtable[self.state][action] += reward
        maxQ = max(self.qtable[new_state].values())
        delta = self.learning_rate * (reward + self.discount_factor * maxQ \
                                      - self.qtable[self.state][action])
        self.qtable[self.state][action] += delta
        self.state = new_state

        if self.state in self.env.goal:
            self.history.append(self.score)
            self.noise *= 1 - 1E-1

        return action, reward

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
        self.env = agent.env
        self.agent = agent

    def state_to_xy(self, state):
        return (state[1] + 0.5) * SPRITE_SIZE, \
               (self.env.height - state[0] - 0.5) * SPRITE_SIZE

    def setup(self):
        self.goal = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        for state in self.env.goal:
            i = randint(1, 4)
            exit = arcade.Sprite(":resources:images/space_shooter/meteorGrey_big"+str(i)+".png", SPRITE_SCALE)
            exit.center_x, exit.center_y = self.state_to_xy(state)
            self.goal.append(exit)

        self.player = arcade.Sprite(":resources:images/space_shooter/playerShip1_green.png", SPRITE_SCALE)
        self.update_player()


    def on_draw(self):
        arcade.start_render()
        self.goal.draw()
        self.player.draw()
        self.bullet_list.draw()
        self.player.angle = self.env.angle
        arcade.draw_text(f'{self.agent.iteration} Score: {self.agent.score} Noise: {self.agent.noise}',
                         10, 10, arcade.color.RED, 24, bold=True)

    def on_update(self, delta_time):
        nombre = sum(1 for cle, valeur in self.env.map.items() if valeur == "*")
        print(nombre)
        if nombre != 0:
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

    

    def shoot(self):
        bullet_sprite = TurningSprite(":resources:images/space_shooter/laserBlue01.png", SPRITE_SCALE)
        bullet_sprite.center_x, bullet_sprite.center_y = self.state_to_xy(self.agent.state)
        bullet_sprite.angle = self.env.angle

        bullet_speed = 13
        bullet_sprite.change_y = \
                math.cos(math.radians(self.env.angle)) * bullet_speed
        bullet_sprite.change_x = \
                -math.sin(math.radians(self.env.angle)) \
                * bullet_speed
        bullet_sprite.update()
        self.bullet_list.append(bullet_sprite)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            self.agent.reset()
        elif key == arcade.key.X:
            self.agent.noise = 1
            self.agent.reset()
        self.update_player()

    def update_player(self):
        self.player.center_x, self.player.center_y = self.state_to_xy(self.agent.state)
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

