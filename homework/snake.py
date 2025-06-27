import pygame
import random
import time

# 初始化pygame
pygame.init()

# 定义颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# 游戏设置
GRID_SIZE = 20
GRID_WIDTH = 20
GRID_HEIGHT = 20
SCREEN_WIDTH = GRID_SIZE * GRID_WIDTH
SCREEN_HEIGHT = GRID_SIZE * GRID_HEIGHT + 40  # 额外空间用于显示分数
INITIAL_SPEED = 10  # 初始速度
SPEED_INCREMENT = 1  # 每5分速度增加量

# 创建游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("贪吃蛇游戏")

# 游戏时钟
clock = pygame.time.Clock()

# 字体设置
font = pygame.font.SysFont('SimHei', 20)  # 使用黑体显示中文
large_font = pygame.font.SysFont('SimHei', 30)

class Snake:
    def __init__(self):
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]  # 初始位置在中心
        self.length = 3  # 初始长度
        self.direction = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])  # 随机初始方向
        self.color = GREEN
        self.score = 0
        self.speed = INITIAL_SPEED
        
    def get_head_position(self):
        return self.positions[0]
    
    def update(self):
        head = self.get_head_position()
        x, y = self.direction
        new_head = ((head[0] + x) % GRID_WIDTH, (head[1] + y) % GRID_HEIGHT)
        
        # 检查是否撞到自己
        if new_head in self.positions[1:]:
            return True  # 游戏结束
        
        self.positions.insert(0, new_head)
        if len(self.positions) > self.length:
            self.positions.pop()
        
        return False  # 游戏继续
    
    def reset(self):
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.length = 3
        self.direction = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
        self.score = 0
        self.speed = INITIAL_SPEED
    
    def render(self, surface):
        for p in self.positions:
            rect = pygame.Rect((p[0] * GRID_SIZE, p[1] * GRID_SIZE), (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, WHITE, rect, 1)  # 白色边框

class Food:
    def __init__(self):
        self.position = (0, 0)
        self.color = RED
        self.randomize_position()
    
    def randomize_position(self, snake_positions=None):
        if snake_positions is None:
            snake_positions = []
        while True:
            self.position = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if self.position not in snake_positions:
                break
    
    def render(self, surface):
        rect = pygame.Rect((self.position[0] * GRID_SIZE, self.position[1] * GRID_SIZE), (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, WHITE, rect, 1)  # 白色边框

def draw_grid(surface):
    for y in range(0, GRID_HEIGHT):
        for x in range(0, GRID_WIDTH):
            rect = pygame.Rect((x * GRID_SIZE, y * GRID_SIZE), (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(surface, BLACK, rect)
            pygame.draw.rect(surface, (50, 50, 50), rect, 1)  # 网格线

def show_start_screen():
    screen.fill(BLACK)
    title = large_font.render("贪吃蛇游戏", True, WHITE)
    instruction1 = font.render("按任意键开始", True, WHITE)
    instruction2 = font.render("使用方向键控制移动", True, WHITE)
    instruction3 = font.render("空格键暂停/继续", True, WHITE)
    
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 4))
    screen.blit(instruction1, (SCREEN_WIDTH // 2 - instruction1.get_width() // 2, SCREEN_HEIGHT // 2))
    screen.blit(instruction2, (SCREEN_WIDTH // 2 - instruction2.get_width() // 2, SCREEN_HEIGHT // 2 + 30))
    screen.blit(instruction3, (SCREEN_WIDTH // 2 - instruction3.get_width() // 2, SCREEN_HEIGHT // 2 + 60))
    
    pygame.display.update()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            if event.type == pygame.KEYDOWN:
                waiting = False
    return True

def show_game_over_screen(score):
    screen.fill(BLACK)
    game_over = large_font.render("游戏结束！", True, WHITE)
    final_score = font.render(f"最终得分：{score}", True, WHITE)
    restart = font.render("按回车键重新开始", True, WHITE)
    
    screen.blit(game_over, (SCREEN_WIDTH // 2 - game_over.get_width() // 2, SCREEN_HEIGHT // 4))
    screen.blit(final_score, (SCREEN_WIDTH // 2 - final_score.get_width() // 2, SCREEN_HEIGHT // 2))
    screen.blit(restart, (SCREEN_WIDTH // 2 - restart.get_width() // 2, SCREEN_HEIGHT // 2 + 40))
    
    pygame.display.update()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                waiting = False
    return True

def main():
    # 游戏状态
    game_over = False
    paused = False
    running = True
    
    # 创建蛇和食物
    snake = Snake()
    food = Food()
    
    # 显示开始界面
    if not show_start_screen():
        return
    
    # 主游戏循环
    while running:
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif not paused and not game_over:
                    if event.key == pygame.K_UP and snake.direction != (0, 1):
                        snake.direction = (0, -1)
                    elif event.key == pygame.K_DOWN and snake.direction != (0, -1):
                        snake.direction = (0, 1)
                    elif event.key == pygame.K_LEFT and snake.direction != (1, 0):
                        snake.direction = (-1, 0)
                    elif event.key == pygame.K_RIGHT and snake.direction != (-1, 0):
                        snake.direction = (1, 0)
        
        if not game_over and not paused:
            # 更新蛇的位置
            game_over = snake.update()
            
            # 检查是否吃到食物
            if snake.get_head_position() == food.position:
                snake.length += 1
                snake.score += 1
                # 每得5分增加速度
                if snake.score % 5 == 0:
                    snake.speed += SPEED_INCREMENT
                food.randomize_position(snake.positions)
        
        # 绘制游戏
        screen.fill(BLACK)
        draw_grid(screen)
        snake.render(screen)
        food.render(screen)
        
        # 显示分数
        score_text = font.render(f"得分：{snake.score}", True, WHITE)
        screen.blit(score_text, (5, SCREEN_HEIGHT - 30))
        
        # 显示暂停状态
        if paused:
            pause_text = font.render("已暂停", True, WHITE)
            screen.blit(pause_text, (SCREEN_WIDTH - pause_text.get_width() - 5, SCREEN_HEIGHT - 30))
        
        pygame.display.update()
        
        # 游戏结束处理
        if game_over:
            if not show_game_over_screen(snake.score):
                running = False
            else:
                # 重置游戏
                snake.reset()
                food.randomize_position()
                game_over = False
                paused = False
        
        # 控制游戏速度
        clock.tick(snake.speed)
    
    pygame.quit()

if __name__ == "__main__":
    main()