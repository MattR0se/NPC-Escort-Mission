import pygame as pg
import traceback
import datetime

import game


if __name__ == '__main__':
    try:
        g = game.Game()
        g.run()
    except Exception:
        e = traceback.format_exc()
        print(e)
        with open('log/errors.txt', 'a') as f:
            f.write(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')+ '\n')
            f.write(e + '\n')
        pg.quit()