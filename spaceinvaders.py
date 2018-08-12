import sys, time, random, pygame
from pygame.locals import *

ALIENROWS = 6
ALIENCOLS = 11
ALIENMAXWIDTH = 24
ALIENMAXHEIGHT = 16
ALIENGAPX = 10
ALIENGAPY = 10

PLAYERWIDTH = 26
PLAYERHEIGHT = 16
PLAYERSPEED = 3
BULLETSPEED = 6
ALIENBULLETSPEED = 3
EXPLOSIONDELAY = 0.15

TOPMARGIN = 50
BOTTOMMARGIN = PLAYERHEIGHT * 2
SCREENWIDTH = 454
SCREENHEIGHT = TOPMARGIN + (ALIENMAXHEIGHT * ALIENROWS + (ALIENGAPY * (ALIENROWS - 1))) * 3
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BGCOLOR = BLACK

ALIEN1 = 0
ALIEN2 = 1
ALIEN3 = 2
ALIENSPECIAL = 3
ALIENSIZES = {ALIEN1: (16, 16), ALIEN2: (22, 16), ALIEN3: (24, 16), ALIENSPECIAL: (48, 21)}
ALIENSCORES = {ALIEN1: 30, ALIEN2: 20, ALIEN3: 10, ALIENSPECIAL: 50}
ALIENSPEED = 5

LEFT = "left"
RIGHT = "right"

def main():
    global SCREEN, FPSCLOCK, SPRITES, PSFONT, SOUNDS

    pygame.mixer.pre_init(44100, -16, 10, 512)
    pygame.mixer.init()
    pygame.init()
    #pygame.mixer.set_num_channels(20)

    SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
    pygame.display.set_caption("Space Invaders")
    FPSCLOCK = pygame.time.Clock()
    SPRITES = {}
    PSFONT = pygame.font.Font("prstart.ttf", 14)
    SOUNDS = {}
    random.seed()
    gameOver = False

    loadMedia()
    aliens = generateAliens()
    walls = generateWalls()

    playerRect = SPRITES["player"].get_rect()
    playerRect.topleft = ((SCREENWIDTH / 2) - (playerRect.width / 2), SCREENHEIGHT - BOTTOMMARGIN - playerRect.height - 50)
    bulletRect = pygame.Rect(0, 0, 2, 8)

    specialRect = SPRITES["aliens"][ALIENSPECIAL].get_rect()
    specialRect.topleft = (-specialRect.width, TOPMARGIN)

    nextLevel = False
    playerMoveLeft = False
    playerMoveRight = False
    fireBullet = False
    bulletFired = False
    alienBullets = []

    alienFrame = 0 # frame of animation; each alien has two animation frames except for special alien
    alienDirection = 1 # 1 when moving left, -1 when moving right
    collision = False # True when a collision is detected; pauses the execution of entities for effect
    showSpecialAlien = False # randomly spawn special alien and move across top of screen
    lastMoveTime = time.time()
    lastSpecialTime = time.time()
    lastShotTime = time.time()
    explosionTime = time.time()
    moveDelay = 1.0 # start with 1 second delay between moving aliens
    delayDecr = moveDelay / len(aliens) # how much faster the aliens move after one is defeated

    note = 0
    score = 0
    hiscore = 0
    level = 0
    lives = 3

    showStartScreen()
    while True:
        spawnAnimation(aliens, score, hiscore, lives)
        pygame.time.set_timer(USEREVENT+3, int(moveDelay * 1000)) # event timer for playing bg music notes
        while not gameOver:
            # Event handling
            for event in pygame.event.get():
                if event.type == QUIT:
                    terminate()
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        terminate()
                    elif event.key == K_f:
                        if SCREEN.get_flags() & FULLSCREEN:
                            pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
                        else:
                            pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT), FULLSCREEN)
                    elif event.key == K_LEFT:
                        playerMoveLeft = True
                        playerMoveRight = False
                    elif event.key == K_RIGHT:
                        playerMoveRight = True
                        playerMoveLeft = False
                    elif event.key == K_SPACE and not bulletFired:
                        fireBullet = True
                elif event.type == KEYUP:
                    if event.key == K_LEFT:
                        playerMoveLeft = False
                    elif event.key == K_RIGHT:
                        playerMoveRight = False
                elif event.type == USEREVENT+3:
                    pygame.mixer.Channel(0).stop()
                    delay = int(moveDelay * 1000)
                    if note == 0:
                        if delay < 106:
                            if len(aliens) == 1:
                                delay = 90
                            else:
                                delay = 106
                        pygame.time.set_timer(USEREVENT+3, delay)
                    pygame.mixer.Channel(0).play(SOUNDS["notes"][note])
                    note = (note + 1) % 4
            
            if not collision:
                # Move aliens
                if time.time() - lastMoveTime > moveDelay:
                    # move aliens and change alien sprite
                    alienDirection = moveAliens(aliens, alienDirection)
                    if time.time() - lastShotTime > 0.75: # alien fires a bullet every 750 ms
                        alienFire(aliens, alienBullets)
                        lastShotTime = time.time()
                    if not showSpecialAlien and random.randint(0, 99) < 5 and (time.time() - lastSpecialTime > 20): # 5% chance of spawning special alien 20 seconds after the previous alien
                        showSpecialAlien = True
                        pygame.mixer.Channel(1).play(SOUNDS["special"])
                    alienFrame = ~alienFrame
                    lastMoveTime = time.time()
                if showSpecialAlien:
                    if specialRect.left > SCREENWIDTH:
                        specialRect.topleft = (-specialRect.width, TOPMARGIN)
                        showSpecialAlien = False
                        lastSpecialTime = time.time()
                    else:
                        specialRect.move_ip(3, 0)
                # Move player
                if playerMoveLeft:
                    playerRect.move_ip(-PLAYERSPEED, 0)
                elif playerMoveRight:
                    playerRect.move_ip(PLAYERSPEED, 0)
                if playerRect.left < 0:
                    playerRect.left = 0
                if playerRect.right > SCREENWIDTH:
                    playerRect.right = SCREENWIDTH
                
                # Move player bullet
                if fireBullet:
                    pygame.mixer.Channel(2).play(SOUNDS["fire"])
                    bulletFired = True
                    fireBullet = False
                    bulletRect.topleft = (playerRect.centerx - (bulletRect.width / 2), playerRect.top - bulletRect.height)
                if bulletFired:
                    bulletRect.move_ip(0, -BULLETSPEED)
                    if bulletRect.bottom < TOPMARGIN: # bullet went past top of the screen
                        bulletFired = False
                else:
                    pygame.mixer.Channel(2).stop()
                # Move alien bullets
                for bullet in alienBullets:
                    bullet.move_ip(0, ALIENBULLETSPEED)
                    if bullet.bottom >= SCREENHEIGHT - BOTTOMMARGIN:
                        alienBullets.remove(bullet)
                
                # Check collisions
                if bulletFired:
                    colIndex = -1
                    for i in range(len(aliens)): # alien - bullet collision
                        if bulletRect.colliderect(aliens[i]["rect"]):
                            colIndex = i
                            break
                    if colIndex >= 0:
                        collision = True
                        score += ALIENSCORES[aliens[colIndex]["type"]]
                        explosionCenter = aliens[colIndex]["rect"].center
                        del aliens[colIndex]
                        bulletFired = False
                        numAliens = len(aliens)
                        if numAliens == 0:
                            nextLevel = True
                        elif numAliens == 1:
                            moveDelay = 0.0
                        else:
                            moveDelay -= delayDecr
                        explosionTime = time.time()
                        pygame.mixer.Channel(3).play(SOUNDS["aliendeath"])
                    elif bulletRect.colliderect(specialRect): # special alien - bullet collision
                        collision = True
                        explosionCenter = specialRect.center
                        showSpecialAlien = False
                        specialRect.topleft = (-specialRect.width, TOPMARGIN)
                        bulletFired = False
                        explosionTime = time.time()
                        pygame.mixer.Channel(3).play(SOUNDS["aliendeath"])
                    elif collideWalls(walls, bulletRect): # bullet - wall collision
                        bulletFired = False
                    elif len(alienBullets) > 0:
                        colIndex = bulletRect.collidelist(alienBullets) # bullet - alien bullet collision
                        if colIndex >= 0:
                            collision = True
                            explosionCenter = alienBullets[colIndex].center
                            del alienBullets[colIndex]
                            bulletFired = False
                            explosionTime = time.time()
                            pygame.mixer.Channel(3).play(SOUNDS["aliendeath"])
                colIndex = playerRect.collidelist(alienBullets) # player - alien bullet collision
                if colIndex >= 0:
                    collision = True
                    bulletFired = False
                    explosionCenter = playerRect.center
                    alienBullets.clear()
                    lives -= 1
                    explosionTime = time.time()
                    pygame.time.set_timer(USEREVENT+3, 0)
                    pygame.mixer.pause()
                    pygame.mixer.Channel(4).play(SOUNDS["playerdeath"])
                    if lives == 0:
                        gameOver = True
                for bullet in alienBullets: # alien bullet - wall collision
                    if collideWalls(walls, bullet):
                        alienBullets.remove(bullet)
                for alien in aliens: # player - alien collision
                    alienRect = alien["rect"]
                    collideWalls(walls, alienRect)
                    if playerRect.colliderect(alienRect):
                        collision = True
                        explosionCenter = playerRect.center
                        explosionTime = time.time()
                        pygame.time.set_timer(USEREVENT+3, 0)
                        pygame.mixer.pause()
                        pygame.mixer.Channel(4).play(SOUNDS["playerdeath"])
                        gameOver = True
            
            
            # Draw
            SCREEN.fill(BGCOLOR)
            drawScoreAndLives(score, hiscore, lives)
            drawWalls(walls)
            SCREEN.blit(SPRITES["player"], playerRect)
            drawAliens(aliens, alienFrame)
            if collision:
                explosionRect = SPRITES["explosion"].get_rect()
                explosionRect.center = explosionCenter
                SCREEN.blit(SPRITES["explosion"], explosionRect)
                if explosionCenter == playerRect.center:
                    if time.time() - explosionTime > SOUNDS["playerdeath"].get_length():
                        collision = False
                        note = 0
                        pygame.time.set_timer(USEREVENT+3, 100)
                        pygame.mixer.unpause()
                elif time.time() - explosionTime > EXPLOSIONDELAY:
                    collision = False
            if showSpecialAlien:
                SCREEN.blit(SPRITES["aliens"][ALIENSPECIAL], specialRect)
            if bulletFired:
                pygame.draw.rect(SCREEN, GREEN, bulletRect)
            for bullet in alienBullets:
                pygame.draw.rect(SCREEN, WHITE, bullet)

            pygame.display.update()
            FPSCLOCK.tick(FPS)

            if nextLevel:
                break

        # reset
        aliens = generateAliens()
        alienBullets.clear()
        alienFrame = 0
        alienDirection = 1
        bulletFired = False
        showSpecialAlien = False
        playerMoveLeft = False
        playerMoveRight = False
        playerRect.topleft = ((SCREENWIDTH / 2) - (playerRect.width / 2), SCREENHEIGHT - BOTTOMMARGIN - playerRect.height - 50)
        specialRect.topleft = (-specialRect.width, TOPMARGIN)
        note = 0
        if not gameOver:
            level += 1
            nextLevel = False
        else:
            if score > hiscore:
                hiscore = score
            showGameOverScreen(score, hiscore)
            level = 0
            score = 0
            lives = 3
            gameOver = False
            walls = generateWalls()
            showStartScreen()
        moveDelay = 1.0 - (level * 0.1)
        if moveDelay < 0.5:
            moveDelay = 0.5
        delayDecr = moveDelay / len(aliens)
        lastMoveTime = time.time()
        lastSpecialTime = time.time()
        lastShotTime = time.time()
        explosionTime = time.time()
        pygame.mixer.stop()

def showStartScreen():
    spaceFont = pygame.font.Font("prstart.ttf", 24)
    infoFont = pygame.font.Font("prstart.ttf", 14)

    titleSurf = spaceFont.render("SPACE INVADERS", 0, GREEN)
    titleRect = titleSurf.get_rect()
    titleRect.center = (SCREENWIDTH / 2, 100)

    alien3 = infoFont.render("= 10 POINTS", 0, WHITE)
    alienRect3 = alien3.get_rect()
    alienRect3.topleft = (200, 180)
    alienSprite3 = pygame.Rect(alienRect3.left - ALIENMAXWIDTH - 75, 180, ALIENMAXWIDTH, ALIENMAXHEIGHT)

    alien2 = infoFont.render("= 20 POINTS", 0, WHITE)
    alienRect2 = alien2.get_rect()
    alienRect2.topleft = (200, 230)
    alienSprite2 = (alienRect3.left - ALIENMAXWIDTH - 75 + 1, 230, ALIENMAXWIDTH, ALIENMAXHEIGHT)

    alien1 = infoFont.render("= 30 POINTS", 0, WHITE)
    alienRect1 = alien3.get_rect()
    alienRect1.topleft = (200, 280)
    alienSprite1 = (alienRect3.left - ALIENMAXWIDTH - 75 + 4, 280, ALIENMAXWIDTH, ALIENMAXHEIGHT)

    special = infoFont.render("= 50 POINTS", 0, WHITE)
    specialRect = special.get_rect()
    specialRect.topleft = (200, 330)
    alienSpriteSpecial = (alienRect3.left - ALIENMAXWIDTH - 75 - 12, 330, ALIENMAXWIDTH, ALIENMAXHEIGHT)

    enter = infoFont.render("PRESS ENTER TO PLAY", 0, WHITE)
    enterRect = enter.get_rect()
    enterRect.center = (SCREENWIDTH / 2, SCREENHEIGHT - 50)

    showAlien1 = False
    showAlien2 = False
    showAlien3 = False
    showSpecialAlien = False
    showEnter = False

    pygame.time.set_timer(USEREVENT+1, 1000)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()
                elif event.key == K_RETURN:
                    running = False
                    pygame.time.set_timer(USEREVENT+1, 0)
                    pygame.time.set_timer(USEREVENT+2, 0)
                elif event.key == K_f:
                    if SCREEN.get_flags() & FULLSCREEN:
                        pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
                    else:
                        pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT), FULLSCREEN)
            elif event.type == USEREVENT+1:
                if not showAlien3:
                    showAlien3 = True
                elif not showAlien2:
                    showAlien2 = True
                elif not showAlien1:
                    showAlien1 = True
                elif not showSpecialAlien:
                    showSpecialAlien = True
                    if showEnter:
                        pygame.time.set_timer(USEREVENT+1, 5000)
                elif not showEnter:
                    showEnter = True
                    pygame.time.set_timer(USEREVENT+1, 5000)
                    pygame.time.set_timer(USEREVENT+2, 500)
                else:
                    showAlien1 = False
                    showAlien2 = False
                    showAlien3 = False
                    showSpecialAlien = False
                    pygame.time.set_timer(USEREVENT+1, 1000)
            elif event.type == USEREVENT+2:
                showEnter = not showEnter
        
        SCREEN.fill(BGCOLOR)
        SCREEN.blit(titleSurf, titleRect)
        if showAlien3:
            SCREEN.blit(SPRITES["aliens"][ALIEN3][0], alienSprite3)
            SCREEN.blit(alien3, alienRect3)
        if showAlien2:
            SCREEN.blit(SPRITES["aliens"][ALIEN2][0], alienSprite2)
            SCREEN.blit(alien2, alienRect2)
        if showAlien1:
            SCREEN.blit(SPRITES["aliens"][ALIEN1][0], alienSprite1)
            SCREEN.blit(alien1, alienRect1)
        if showSpecialAlien:
            SCREEN.blit(SPRITES["aliens"][ALIENSPECIAL], alienSpriteSpecial)
            SCREEN.blit(special, specialRect)
        if showEnter:
            SCREEN.blit(enter, enterRect)
        pygame.display.update()
        FPSCLOCK.tick(FPS)

def showGameOverScreen(score, hiscore):
    gameOverFont = pygame.font.Font("prstart.ttf", 20)
    infoFont = pygame.font.Font("prstart.ttf", 14)

    gameOverSurf = gameOverFont.render("GAME OVER", 0, RED)
    gameOverRect = gameOverSurf.get_rect()
    gameOverRect.center = (SCREENWIDTH / 2, ((SCREENHEIGHT - BOTTOMMARGIN) / 2) - 50)

    scoreSurf = infoFont.render("SCORE: %s" % str(score), 0, WHITE)
    scoreRect = scoreSurf.get_rect()
    scoreRect.center = (SCREENWIDTH / 2, ((SCREENHEIGHT - BOTTOMMARGIN) / 2))

    enterSurf = infoFont.render("PRESS ENTER TO CONTINUE", 0, WHITE)
    enterRect = enterSurf.get_rect()
    enterRect.center = (SCREENWIDTH / 2, SCREENHEIGHT - BOTTOMMARGIN - 50)

    showScore = False
    showEnter = False

    running = True
    pygame.time.set_timer(USEREVENT+1, 1000)
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()
                elif event.key == K_RETURN:
                    running = False
                    pygame.time.set_timer(USEREVENT+1, 0)
                elif event.key == K_f:
                    if SCREEN.get_flags() & FULLSCREEN:
                        pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
                    else:
                        pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT), FULLSCREEN)
            elif event.type == USEREVENT+1:
                if not showScore:
                    showScore = True
                else:
                    showEnter = ~showEnter
                    pygame.time.set_timer(USEREVENT+1, 500)
        
        SCREEN.fill(BGCOLOR)
        drawScoreAndLives(score, hiscore, 0)
        SCREEN.blit(gameOverSurf, gameOverRect)
        if showScore:
            SCREEN.blit(scoreSurf, scoreRect)
        if showEnter:
            SCREEN.blit(enterSurf, enterRect)
        pygame.display.update()
        FPSCLOCK.tick(FPS)

def terminate():
    pygame.quit()
    sys.exit()

def loadMedia():
    SPRITES["player"] = pygame.image.load("player.png").convert()
    aliens = {}
    aliens[ALIEN1] = [pygame.image.load("alien1_1.png").convert(), pygame.image.load("alien1_2.png").convert()]
    aliens[ALIEN2] = [pygame.image.load("alien2_1.png").convert(), pygame.image.load("alien2_2.png").convert()]
    aliens[ALIEN3] = [pygame.image.load("alien3_1.png").convert(), pygame.image.load("alien3_2.png").convert()]
    aliens[ALIENSPECIAL] = pygame.image.load("special.png").convert()
    SPRITES["aliens"] = aliens
    SPRITES["explosion"] = pygame.image.load("explosion.png").convert()

    SOUNDS["fire"] = pygame.mixer.Sound("fire.wav")
    notes = []
    notes.append(pygame.mixer.Sound("note1.wav"))
    notes.append(pygame.mixer.Sound("note2.wav"))
    notes.append(pygame.mixer.Sound("note3.wav"))
    notes.append(pygame.mixer.Sound("note4.wav"))
    SOUNDS["notes"] = notes
    SOUNDS["aliendeath"] = pygame.mixer.Sound("aliendeath.wav")
    SOUNDS["playerdeath"] = pygame.mixer.Sound("playerdeath.wav")
    SOUNDS["special"] = pygame.mixer.Sound("special.wav")

def createAlien(type, x, y):
    alien = {"type": type, "rect": pygame.Rect(x, y, ALIENSIZES[type][0], ALIENSIZES[type][1])}
    alien["rect"].centerx += (ALIENMAXWIDTH - ALIENSIZES[type][0]) / 2
    return alien

def generateAliens():
    aliens = []
    startx = 5 # leave width of five pixels between edges of screen
    starty = TOPMARGIN + 21 + ALIENGAPY # leave room for special aliens

    for i in range(ALIENROWS):
        alienType = int(i / 2) # two rows for every alien type
        for j in range(ALIENCOLS):
            aliens.append(createAlien(alienType, startx, starty))
            startx += ALIENMAXWIDTH + ALIENGAPX
        startx = 5
        starty += ALIENMAXHEIGHT + ALIENGAPY
    
    remainder = (SCREENWIDTH - ((ALIENMAXWIDTH * ALIENCOLS) + (ALIENGAPX * (ALIENCOLS - 1)))) / 2
    for alien in aliens: # centering all aliens
        alien["rect"].move_ip(remainder, 0)
    
    return aliens

def generateWalls():
    # Walls are composed of lots of small Rects that can be deleted when a bullet collides with them
    wall1 = []
    wall2 = []
    wall3 = []
    wall4 = []

    for k in range(4):
        for i in range(5, 13):
            wallTile = pygame.Rect(2 * i, 0, 2, 2)
            if k == 0:
                wall1.append(wallTile)
            elif k == 1:
                wall2.append(wallTile)
            elif k == 2:
                wall3.append(wallTile)
            elif k == 3:
                wall4.append(wallTile)
        for i in range(3, 14):
            wallTile = pygame.Rect(2 * i, 2, 2, 2)
            if k == 0:
                wall1.append(wallTile)
            elif k == 1:
                wall2.append(wallTile)
            elif k == 2:
                wall3.append(wallTile)
            elif k == 3:
                wall4.append(wallTile)
        for i in range(2, 15):
            wallTile = pygame.Rect(2 * i, 4, 2, 2)
            if k == 0:
                wall1.append(wallTile)
            elif k == 1:
                wall2.append(wallTile)
            elif k == 2:
                wall3.append(wallTile)
            elif k == 3:
                wall4.append(wallTile)
        for i in range(1, 16):
            wallTile = pygame.Rect(2 * i, 6, 2, 2)
            if k == 0:
                wall1.append(wallTile)
            elif k == 1:
                wall2.append(wallTile)
            elif k == 2:
                wall3.append(wallTile)
            elif k == 3:
                wall4.append(wallTile)
        startTop = 8
        for i in range(8):
            for j in range(17):
                wallTile = pygame.Rect(2 * j, startTop, 2, 2)
                if k == 0:
                    wall1.append(wallTile)
                elif k == 1:
                    wall2.append(wallTile)
                elif k == 2:
                    wall3.append(wallTile)
                elif k == 3:
                    wall4.append(wallTile)
            startTop += 2
        for i in range(17):
            if i < 6 or i >= 11:
                wallTile = pygame.Rect(2 * i, 24, 2, 2)
                if k == 0:
                    wall1.append(wallTile)
                elif k == 1:
                    wall2.append(wallTile)
                elif k == 2:
                    wall3.append(wallTile)
                elif k == 3:
                    wall4.append(wallTile)
        for i in range(17):
            if i < 5 or i >= 12:
                wallTile = pygame.Rect(2 * i, 26, 2, 2)
                if k == 0:
                    wall1.append(wallTile)
                elif k == 1:
                    wall2.append(wallTile)
                elif k == 2:
                    wall3.append(wallTile)
                elif k == 3:
                    wall4.append(wallTile)
        for i in range(17):
            if i < 4 or i >= 13:
                wallTile = pygame.Rect(2 * i, 28, 2, 2)
                if k == 0:
                    wall1.append(wallTile)
                elif k == 1:
                    wall2.append(wallTile)
                elif k == 2:
                    wall3.append(wallTile)
                elif k == 3:
                    wall4.append(wallTile)
        for i in range(17):
            if i < 4 or i >= 13:
                wallTile = pygame.Rect(2 * i, 30, 2, 2)
                if k == 0:
                    wall1.append(wallTile)
                elif k == 1:
                    wall2.append(wallTile)
                elif k == 2:
                    wall3.append(wallTile)
                elif k == 3:
                    wall4.append(wallTile)
    
    # Move walls into place
    offset = SCREENWIDTH / 8
    currentOffset = offset
    for i in range(4):
        if i == 0:
            for tile in wall1:
                tile.move_ip(currentOffset - 17, SCREENHEIGHT - BOTTOMMARGIN - 2 * PLAYERHEIGHT - 100)
        elif i == 1:
            for tile in wall2:
                tile.move_ip(currentOffset - 17, SCREENHEIGHT - BOTTOMMARGIN - 2 * PLAYERHEIGHT - 100)
        elif i == 2:
            for tile in wall3:
                tile.move_ip(currentOffset - 17, SCREENHEIGHT - BOTTOMMARGIN - 2 * PLAYERHEIGHT - 100)
        elif i == 3:
            for tile in wall4:
                tile.move_ip(currentOffset - 17, SCREENHEIGHT - BOTTOMMARGIN - 2 * PLAYERHEIGHT - 100)
        currentOffset += 2 * offset

    return [wall1, wall2, wall3, wall4]

def drawWalls(walls):
    for wall in walls:
        for tile in wall:
            pygame.draw.rect(SCREEN, GREEN, tile)

def collideWalls(walls, entity):
    for wall in walls:
        colIndices = entity.collidelistall(wall)
        if len(colIndices) > 0:
            removeList = []
            for index in colIndices:
                removeList.append(wall[index])
            for item in removeList:
                wall.remove(item)
            return True

def drawAliens(aliens, frame):
    for alien in aliens:
        alienType = alien["type"]
        if alienType == ALIENSPECIAL:
            frame = 0
        SCREEN.blit(SPRITES["aliens"][alienType][frame], alien["rect"])

def moveAliens(aliens, direction):
    newDirection = direction
    offscreen = False
    
    # Move all aliens
    for alien in aliens:
        alien["rect"].move_ip(direction * ALIENSPEED, 0)

    # Check if any alien is now beyond the sides of the screen
    for alien in aliens:
        if (alien["rect"].left <= 0 or alien["rect"].right >= SCREENWIDTH):
            offscreen = True
            break
    if offscreen: # If an alien was offscreen, move all aliens back and down, and reverse direction
        for alien in aliens:
            alien["rect"].move_ip(direction * -ALIENSPEED, ALIENMAXHEIGHT)
        newDirection = -direction

    return newDirection

def drawScoreAndLives(score, hiscore, lives):
    scoreSurf = PSFONT.render("SCORE: %s" % str(score), 0, WHITE)
    scoreRect = scoreSurf.get_rect()
    scoreRect.topleft = (5, (TOPMARGIN / 2) / (scoreRect.height / 2))

    hiscoreSurf = PSFONT.render("HISCORE: %s" % str(hiscore), 0, WHITE)
    hiscoreRect = hiscoreSurf.get_rect()
    hiscoreRect.topright = (SCREENWIDTH - 5, (TOPMARGIN / 2) / (hiscoreRect.height / 2))

    livesSurf = PSFONT.render("%s" % str(lives), 0, WHITE)
    livesRect = livesSurf.get_rect()
    livesRect.topleft = (5, SCREENHEIGHT - 32 + 2)

    creditSurf = PSFONT.render("CREDIT 00", 0, WHITE)
    creditRect = creditSurf.get_rect()
    creditRect.topright = (SCREENWIDTH - 5, SCREENHEIGHT - 32 + 2)

    SCREEN.blit(scoreSurf, scoreRect)
    SCREEN.blit(hiscoreSurf, hiscoreRect)
    SCREEN.blit(livesSurf, livesRect)
    SCREEN.blit(creditSurf, creditRect)

    startx = PLAYERWIDTH
    for i in range(lives - 1):
        SCREEN.blit(SPRITES["player"], (startx, SCREENHEIGHT - 32, PLAYERWIDTH, PLAYERHEIGHT))
        startx += PLAYERWIDTH + 5
    
    pygame.draw.line(SCREEN, GREEN, (0, SCREENHEIGHT - 32), (SCREENWIDTH, SCREENHEIGHT - 32))

def alienFire(aliens, alienBullets):
    index = random.randint(0, len(aliens) - 1)
    alienRect = aliens[index]["rect"]
    alienBullets.append(pygame.Rect(alienRect.centerx - 2, alienRect.bottom, 2, 8))

def spawnAnimation(aliens, score, hiscore, lives):
    index = 0
    drawList = []
    SCREEN.fill(BGCOLOR)
    while index < len(aliens):
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()
                elif event.key == K_f:
                    if SCREEN.get_flags() & FULLSCREEN:
                        pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
                    else:
                        pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT), FULLSCREEN)
        
        drawList.append(aliens[index])
        index += 1

        drawAliens(drawList, 0)
        drawScoreAndLives(score, hiscore, lives)
        pygame.display.update()
        FPSCLOCK.tick(FPS)

if __name__ == "__main__":
    main()