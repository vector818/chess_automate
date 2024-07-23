from abc import ABC, abstractmethod

import pyautogui
import cv2
import numpy as np
from PIL import Image
import time
import matplotlib.pyplot as plt
import logging
from operator import itemgetter
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import chess
import chess.engine
from random import random
from datetime import datetime,timedelta
import time

from logging import FileHandler, StreamHandler
from logging.handlers import RotatingFileHandler

handlers = [
    FileHandler('logs/log.log', encoding = 'utf-8'),  # Default mode='a', encoding=None
    StreamHandler(),  # Default stream=sys.stderr
]
logging.basicConfig(handlers=handlers, format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

class new_move_has_occured(object):
  
  def __init__(self, moves):
    self.moves = moves
    self.num_of_moves = len(moves)    

  def __call__(self, driver):
    #//*[@id="main-wrap"]/main/div[1]/rm6/l4x/i5z[1]
    #//*[@id="main-wrap"]/main/div[1]/rm6/l4x/kwdb
    #mon_moves_we = driver.find_elements_by_class_name("move")   # Finding the referenced element
    try:
        element = driver.find_element_by_xpath('//*[@id="main-wrap"]/main/div[1]/rm6/l4x/div/p[2]')
        gameover = element.is_displayed()
        if gameover:
            return driver.find_elements('xpath','//*[@id="main-wrap"]/main/div[1]/rm6/l4x/kwdb')
    except:
        gameover=False
    mon_moves_we = driver.find_elements('xpath','//*[@id="main-wrap"]/main/div[1]/rm6/l4x/kwdb')
    mon_moves = [move.text for move in mon_moves_we]
    if mon_moves and self.moves:
        cond = self.num_of_moves < len(mon_moves) or self.moves[-1] != mon_moves[-1]
    else:
        cond = self.num_of_moves < len(mon_moves)
    if cond:
        return mon_moves_we
    else:
        return False

class BrowserInterface(ABC):

    @abstractmethod
    def configure_browser(self):
        pass

class ChessSiteInterface(ABC):
    
    @abstractmethod
    def open_board(self):
        pass

    @abstractmethod
    def promote_pawn(self, promotion_piece):
        pass        

class ChromeBrowser(BrowserInterface):
    def __init__(self, user_data_dir: str, web_driver_path: str):
        #chromepath = r"C:\Users\MJakimiuk\OneDrive\Documents\py\stockfish\chromedriver.exe"    
        self.user_data_dir = user_data_dir
        self.web_driver_path = web_driver_path
        
    def configure_browser(self):
        options = webdriver.ChromeOptions() 
        #options.add_argument(r"user-data-dir=C:\Users\MJakimiuk\AppData\Local\Google\Chrome\User Data")
        options.add_argument("user-data-dir="+self.user_data_dir)
        self.options = options
        self.driver = webdriver.Chrome()
        return self.driver

class FirefoxBrowser(BrowserInterface):
    def __init__(self):
        pass
    def configure_browser(self):
        pass

class LichessSite(ChessSiteInterface):
    def __init__(self, driver):
        self.driver = driver
        self.site = 'https://www.lichess.org/'
        self.click_colours_keys = {'green' : None,
                                    'blue': ['alt'],
                                    'red': ['shift'],
                                    'yellow': ['alt','shift']
                                    }
        
        self.arrow_colours_keys = {'green' : None,
                                    'blue': ['alt'],
                                    'red': ['shift'],
                                    'yellow': ['alt','shift']
                                    }
        
    def open_board(self):
        self.driver.get(self.site)
        #driver = webdriver.Chrome(executable_path=chromepath)
        waiter = WebDriverWait(self.driver, 600)
        waiter.until(EC.presence_of_element_located((By.XPATH,'//*[@id="main-wrap"]/main/div[1]/rm6/div[1]')))
        if self.driver.find_element('xpath','//*[@id="main-wrap"]/main/div[1]/div[1]/div').get_attribute("class")=='cg-wrap orientation-black manipulable':
            self.color = 'black'
        else:
            self.color = 'white'     
        return self.color, self.driver
    
    def promote_pawn(self, promotion_piece):        
        promotion_order = ['q','n','r','b']
        promotion_no = promotion_order.index(promotion_piece)+1
        promotion_xpath = f'//*[@id="promotion-choice"]/square[{promotion_no}]'
        self.driver.find_element('xpath',promotion_xpath).click()
    
    def wait_for_move(self, moves):
        try:
            element = self.driver.find_element_by_xpath('//*[@id="main-wrap"]/main/div[1]/rm6/l4x/div/p[2]')
            gameover = element.is_displayed()
        except:
            gameover=False
        if gameover:
            return moves, gameover
        else:
            gameover = False
        #waiter.until(EC.presence_of_element_located((By.ID, "logout"))
        #moves = driver.find_elements_by_class_name("move")
        waiter = WebDriverWait(self.driver, 600)
        moves_we = waiter.until(new_move_has_occured(moves))
        #moves=copy.deepcopy(moves_d)
        #moves = driver.find_elements_by_class_name("move")
        moves = [move.text for move in moves_we]
        return moves, gameover

class ChessDotComSite(ChessSiteInterface):
    def __init__(self, driver):
        self.driver = driver
        self.site = 'https://www.chess.com/'
        self.click_colours_keys = {
                                    'red' : None,
                                    'yellow': ['ctrl'],
                                    'green': ['shift'],
                                    'blue': ['alt']   
                                    } 
        self.arrow_colours_keys = {
                                'yellow' : [None],
                                'red': ['ctrl'],
                                'green': ['shift'],
                                'blue': ['alt']
                                }
        
    def open_board(self):
        pass

class Factory:
    
    @staticmethod
    def create_browser(browser_choice: str, user_data_dir: str, web_driver_path: str):
        if browser_choice.lower() == 'chrome':
            return ChromeBrowser(user_data_dir, web_driver_path)
        elif browser_choice.lower() == 'firefox':
            return FirefoxBrowser(user_data_dir, web_driver_path)
        else:
            raise ValueError(f"Unsupported browser: {browser_choice}")
    
    @staticmethod
    def create_chess_site(site_choice, driver):
        if site_choice.lower() == 'chess.com':
            return ChessDotComSite(driver)
        elif site_choice.lower() == 'lichess.org':
            return LichessSite(driver)
        else:
            raise ValueError(f"Unsupported site: {site_choice}")

class ChessBoardClicker:
    def __init__(self, driver: webdriver, site_interface: ChessSiteInterface, debug_mode: bool = True, white_perspective: bool = True, click_colours_keys: dict = None, arrow_colours_keys: dict = None, ):
        self.white_perspective = white_perspective
        self.debug_mode = debug_mode
        self.squares = {}
        self.chessboard_contour = None
        self.click_colours_keys = click_colours_keys
        self.arrow_colours_keys = arrow_colours_keys
        self.driver = driver
        self.site_interface = site_interface         

    def convert_to_chess_notation(self, row_index, column_index, is_white_perspective):
        column_letters = 'abcdefgh' if is_white_perspective else 'hgfedcba'
        row_numbers = '87654321' if is_white_perspective else '12345678'
        
        column_letter = column_letters[column_index]
        row_number = row_numbers[row_index]
        
        return column_letter,row_number
    
    def get_squares(self):
        # Zrób zrzut ekranu
        screenshot = pyautogui.screenshot()
        # Konwertuj zrzut ekranu na obraz OpenCV
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        # Zapisz zrzut ekranu dla celów debugowania (opcjonalne)
        if self.debug_mode:
            cv2.imwrite("screenshot.png", screenshot_cv)
        # Konwertuj obraz na skalę szarości
        gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
        # Wykrywanie krawędzi
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        # Znajdź kontury
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # Szukamy największego prostokątnego konturu, który będzie szachownicą
        max_area = 0
        chessboard_contour = None
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            if len(approx) == 4:
                area = cv2.contourArea(contour)
                if area > max_area:
                    max_area = area
                    chessboard_contour = approx
        # Zakładamy, że szachownica to prostokąt
        if chessboard_contour is not None:
            # Sortujemy punkty konturu, aby ustalić rogi
            chessboard_contour = chessboard_contour.reshape((4, 2))
            self.chessboard_contour = chessboard_contour
            self.top_left = chessboard_contour[0]
            self.bottom_left = chessboard_contour[1]
            self.bottom_right = chessboard_contour[2]
            self.top_right = chessboard_contour[3]   
            # Wyliczenie rozmiaru pola
            self.square_width = (self.bottom_right[0] - self.bottom_left[0]) / 8
            self.square_height = (self.bottom_left[1] - self.top_left[1]) / 8
            # Rysowanie konturu szachownicy na obrazie (opcjonalne)
            if chessboard_contour is not None and self.debug_mode:
                cv2.drawContours(screenshot_cv, [chessboard_contour], -1, (0, 255, 0), 3)
            # Wyliczenie środków pól
            i=0
            for row in range(8):
                for col in range(8):
                    column_letter,row_number = self.convert_to_chess_notation(row,col,self.white_perspective)
                    left = int(self.top_left[0] + col * self.square_width)
                    right = int(left + self.square_width)
                    top = int(self.top_left[1] + row * self.square_height)
                    bottom = int(top + self.square_height)
                    self.squares[column_letter+row_number] = {'column_notation': column_letter, 'row_notation': row_number, 'row': row, 'col': col, 'top_left': (left, top), 'bottom_right': (right, bottom), 'center': (left + self.square_width // 2, top + self.square_height // 2)}
                    i+=1
                    if self.debug_mode:
                        cv2.rectangle(screenshot_cv, (left, top), (right, bottom), (0, 0, 255), 1)
                        #cv2.drawContours(screenshot_cv, [chessboard_contour], -1, (0, 0, 255), 2)
            if self.debug_mode:
                cv2.imwrite("chessboard_detected.png", screenshot_cv)

    def highlight_square(self, square_name, speed: float = 0.3, colour: str = 'red'):
        square = self.squares[square_name]
        center_x, center_y = square['center']        
        keys = self.click_colours_keys[self.site][colour]
        if keys is not None:
            for key in keys:
                pyautogui.keyDown(key)
        pyautogui.moveTo(center_x, center_y, duration=speed)
        pyautogui.mouseDown(button='right')
        time.sleep(0.1)
        pyautogui.mouseUp(button='right')
        if keys is not None:
            for key in keys:
                pyautogui.keyUp(key)

    def draw_arrow(self, move_uci: str, speed: float = 0.2, colour: str = 'red'):
        start_square = move_uci[:2]
        end_square = move_uci[2:4]
        if len(move_uci) > 4:
            promotion_piece = move_uci[4]
        start_square = self.squares[start_square]
        end_square = self.squares[end_square]
        start_x, start_y = start_square['center']
        end_x, end_y = end_square['center']        
        keys = self.arrow_colours_keys[colour]
        if keys is not None:
            for key in keys:
                pyautogui.keyDown(key)
        pyautogui.moveTo(start_x, start_y, duration=speed)
        time.sleep(0.1)
        pyautogui.dragTo(end_x, end_y, duration=speed, button='right')
        if keys is not None:
            for key in keys:
                pyautogui.keyUp(key)
        logging.info(f"Promote to {promotion_piece}")
    
    def make_move(self, move_uci: str, move_speed: float = 0.1, drag_speed: float = 0.2):
        start_square = move_uci[:2]
        end_square = move_uci[2:4]
        promotion_piece = None
        if len(move_uci) > 4:
            promotion_piece = move_uci[4]
        start_square = self.squares[start_square]
        end_square = self.squares[end_square]
        start_x, start_y = start_square['center']
        end_x, end_y = end_square['center']
        pyautogui.moveTo(start_x, start_y, duration=move_speed)
        pyautogui.dragTo(end_x, end_y, duration=drag_speed, button='left')
        if promotion_piece is not None:
            try:
                self.site_interface.promote_pawn(promotion_piece)
            except Exception as e:
                logging.error(e)


class ChessGame:
    def __init__(self, color_perspective, engine_path: str, browser_interface: BrowserInterface, site_interface: ChessSiteInterface, engine_options: dict = None, start_postion: str = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'):
        self.color = color_perspective
        if self.color == 'white':
            self.white_perspective = True
        else:
            self.white_perspective = False
        self.moves = []
        self.gameover = False
        self.board = chess.Board(fen=start_postion)
        self.start_position = start_postion
        self.engine_path = engine_path
        self.engine_options = engine_options
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        if engine_options:
            for option, value in engine_options.items():
                self.engine.configure({option: value})
        self.site = site_interface
        self.browser = browser_interface
        self.clicker = ChessBoardClicker(debug_mode=True, white_perspective=self.white_perspective, click_colours_keys=self.site.click_colours_keys, arrow_colours_keys=self.site.arrow_colours_keys, driver=self.browser.driver, site_interface=self.site)

    def make_move(self, move):
        self.board.push_uci(move)
        self.moves.append(move)
        return self.board
    
    def compare_moves_list(self, moves):
        board_moves = self.board.move_stack
        if len(moves) != len(board_moves):
            return False
        for i,move in enumerate(moves):
            if move != board_moves[i]:
                return False
        return True

    def sync_board(self, moves):  
        self.board = chess.Board(fen=self.start_position)               
        for move in moves:
            self.board.push_san(move)
        self.moves = moves
        return self.board
    
    def find_best_move(self, time_limit: int = 5, multipv: int = 5):
        analysis = self.engine.analyse(self.board, chess.engine.Limit(time=time_limit),multipv=multipv)
        if multipv == 1:
            return analysis
        best_cp = -1e10
        for i in range(multipv):
            if self.color == 'white':
                cp = analysis[i]['score'].white().cp
            else:
                cp = analysis[i]['score'].black().cp
            if cp > best_cp:
                best_cp = cp
                best_variant = analysis[i]
        return best_variant

def main():
    browser_choice = 'chrome'
    site_choice = 'lichess.org'
    browser_driver_path = r"C:\Users\MJakimiuk\OneDrive\Documents\py\stockfish\chromedriver.exe"
    user_data_dir = r"C:\Users\MJakimiuk\AppData\Local\Google\Chrome\User Data"
    engine_path = r"C:\Users\micha\OneDrive\Documents\py\chess_engines\lc0\lc0.exe"
    engine_wieghts_path = r"C:\Users\micha\OneDrive\Documents\py\chess_engines\maia-1900.pb.gz"
    engine_options = {
        "WeightsFile": engine_wieghts_path,
        "Backend": "cuda-auto",  # lub inna odpowiednia opcja backendu
        "MinibatchSize": "1",
        "MaxPrefetch": "4"
    }
    browser = Factory.create_browser(browser_choice, user_data_dir, browser_driver_path)
    driver = browser.configure_browser()
    site = Factory.create_chess_site(site_choice, driver)
    color, driver = site.open_board()
    game = ChessGame(color, engine_path, browser, site, engine_options=engine_options, start_postion='7K/8/8/8/8/8/pk6/8 w - - 0 1')
    game.clicker.get_squares()
    moves = []
    while not game.gameover:
        on_move = 'white' if game.board.turn else 'black'
        if on_move != game.color:
            moves, gameover = site.wait_for_move(moves)
        if gameover:
            game.gameover = True
            break                
        game.sync_board(moves)
        if on_move != game.color:
            continue
        analysis = game.find_best_move(time_limit=5, multipv=1)
        move_to_draw = analysis[0]['pv'][0]
        game.clicker.make_move(move_to_draw.uci())
        game.make_move(move_to_draw.uci())
        logging.info(f'FEN: {game.board.fen()}')
        logging.info(f'Sugessted move: {move_to_draw.uci()}')
        logging.info(f"Score evaluation: {analysis[0]['score']}")       
    driver.quit()


if __name__ == "__main__":
    main()



        