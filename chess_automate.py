from abc import ABC, abstractmethod

import sys
import psutil
import traceback
import os
import re
import yaml
from pathlib import Path
import pyautogui
import cv2
import numpy as np
from PIL import Image
import time
import logging
from operator import itemgetter
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.common import NoSuchElementException, ElementNotInteractableException
import chess
import chess.engine
import chess.polyglot
from random import random
from datetime import datetime,timedelta
import time

from logging import FileHandler, StreamHandler
from logging.handlers import RotatingFileHandler
import random
import copy

handlers = [
    FileHandler('logs/log.log', encoding = 'utf-8'),  # Default mode='a', encoding=None
    StreamHandler(),  # Default stream=sys.stderr
]
logging.basicConfig(handlers=handlers, format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)


class BrowserInterface(ABC):

    def __init__(self):
        self.user_data_path = None
        self.profile_path = None
        self.options = None
        self.driver = None

    @abstractmethod
    def configure_browser(self):
        pass

class ChromeBrowser(BrowserInterface):
    def __init__(self, user_data_dir: str, profile_directory: str):
        super().__init__()
        #chromepath = r"C:\Users\MJakimiuk\OneDrive\Documents\py\stockfish\chromedriver.exe"    
        self.user_data_path = Path(user_data_dir)
        self.profile_path = Path(profile_directory)
        
    def configure_browser(self):
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={self.user_data_path}") #e.g. C:\Users\You\AppData\Local\Google\Chrome\User Data
        options.add_argument(f'--profile-directory={self.profile_path}') #e.g. Profile 3
        options.add_argument("--start-maximized")
        options.add_argument("--custom-flag=webdriver-session")
        options.add_argument("--remote-debugging-port=2137")
        self.options = options
        self.driver = webdriver.Chrome(options=options)
        return self.driver

class FirefoxBrowser(BrowserInterface):
    def __init__(self):
        super().__init__()
        pass
    def configure_browser(self):
        pass

class ChessSiteInterface(ABC):

    def __init__(self,driver: webdriver):
        self.driver = driver
        self.site = None
        self.click_colours_keys = None
        self.arrow_colours_keys = None
        self.moves = None
        self.clock = None
        self.gameover = None
        self.color = None
        self.game_outcome = None
    
    @abstractmethod
    def wait_for_game(self):
        pass

    @abstractmethod
    def promote_pawn(self, promotion_piece):
        pass

    @abstractmethod
    def read_clock(self):
        pass

    @abstractmethod
    def read_moves(self):
        pass

    @abstractmethod
    def get_site_game_state(self):
        pass

    @abstractmethod
    def is_game_over(self):
        pass

    @abstractmethod
    def get_color(self):
        pass

    @abstractmethod
    def resign_game(self):
        pass

class LichessSite(ChessSiteInterface):
    def __init__(self, driver: webdriver):
        super().__init__(driver)
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
        
    def wait_for_game(self):
        #driver = webdriver.Chrome(executable_path=chromepath)
        waiter = WebDriverWait(self.driver, 600)
        waiter.until(EC.presence_of_element_located((By.XPATH,'//*[@id="main-wrap"]/main/div[1]/rm6/div[1]')))
        return self.driver
    
    def promote_pawn(self, promotion_piece):        
        promotion_order = ['q','n','r','b']
        promotion_no = promotion_order.index(promotion_piece)+1
        promotion_xpath = f'//*[@id="promotion-choice"]/square[{promotion_no}]'
        self.driver.find_element('xpath',promotion_xpath).click()
    
    def read_clock(self):
        try:
            time_str = self.driver.find_elements('xpath','//*[@id="main-wrap"]/main/div[1]/div[8]/div[2]')[0].text.replace('\n','')
        except:
            time_str = self.driver.find_elements('xpath','//*[@id="main-wrap"]/main/div[1]/div[8]/div')[0].text.replace('\n','')
        formats = ['%H:%M:%S', '%M:%S', '%M:%S.%f']
        t_datetime = None
        for fmt in formats:
            try:
                t_datetime = datetime.strptime(time_str, fmt)
                break
            except ValueError:
                continue
        if t_datetime is None:
            return timedelta(days=999999)        
        time = timedelta(hours=t_datetime.hour, minutes=t_datetime.minute, seconds=t_datetime.second, microseconds=t_datetime.microsecond)
        return time
    
    def read_moves(self):
        mon_moves_we = self.driver.find_elements('xpath','//*[@id="main-wrap"]/main/div[1]/rm6/l4x/kwdb')
        moves = [move.text for move in mon_moves_we]
        return moves
    
    def get_site_game_state(self):
        self.moves = self.read_moves()
        self.clock = self.read_clock()
        self.gameover = self.is_game_over()

    def is_game_over(self):
        try:
            element = self.driver.find_element('xpath','//*[@id="main-wrap"]/main/div[1]/rm6/l4x/div/p[1]')
            gameover = element.is_displayed()
            return gameover
        except:
            return False
        
    def get_color(self):
        if self.driver.find_element('xpath','//*[@id="main-wrap"]/main/div[1]/div[1]/div').get_attribute("class")=='cg-wrap orientation-black manipulable':
            self.color = 'black'
        else:
            self.color = 'white'     
        return self.color
    
    def resign_game(self):
        pass

    def start_first_game(self,**kwargs):
        pass

class ChessDotComSite(ChessSiteInterface):
    def __init__(self, driver: webdriver):
        super().__init__(driver)
        self.site = 'https://www.chess.com/play/online/new'
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
        self.game_www = None
        
    def wait_for_game(self):
        #driver = webdriver.Chrome(executable_path=chromepath)
        board_element = (By.XPATH,'//*[@id="board-layout-sidebar"]/div/div[2]/div[1]/wc-eco-opening/div')
        new_game_element = (By.XPATH,'//*[@id="board-layout-sidebar"]/div/div[2]/div[7]/button[1]')
        try:
            waiter = WebDriverWait(self.driver, 60)
            waiter.until(EC.presence_of_element_located(board_element))
            waiter.until(EC.invisibility_of_element_located(new_game_element))
        except:
            logging.error("Game not detected")
            return False
        #driver = webdriver.Chrome(executable_path=chromepath)
        # waiter = WebDriverWait(self.driver, timeout=600, ignored_exceptions=errors)
        # errors = [NoSuchElementException, ElementNotInteractableException]
        
        # waiter.until(lambda d: board_element.is_displayed() and not new_game_element.is_displayed())
        logging.info("Game detected")
        self.game_www = self.driver.current_url
        return True
    
    def get_color(self):
        if 'black' in self.driver.find_element('xpath','//*[@id="board-layout-player-bottom"]/div/div[3]').get_attribute("class"):
            self.color = 'black'
        else:
            self.color = 'white'     
        return self.color
    
    def start_first_game(self, **kwargs):
        waiter = WebDriverWait(self.driver, 600)
        clicked = False
        try:
            self.driver.find_element('class name','coach-nudges-modal-close').click()
        except:
            pass
        waiter.until(EC.presence_of_element_located((By.CLASS_NAME,'selector-button-button')))
        list_button = self.driver.find_element('class name','selector-button-button')
        list_button.click()
        time.sleep(0.5)
        time_buttons = self.driver.find_elements('class name','time-selector-button-button')
        for b in time_buttons:
            if kwargs['time_control'] in b.text:
                b.click()
                clicked = True
                break
        if not clicked:
            logging.error("Time control not found")
            raise ValueError("Time control not found")
        time.sleep(1)
        buttons = self.driver.find_elements('class name','cc-button-primary')
        clicked = False
        for b in buttons:
            if 'Play' in b.text:
                b.click()
                clicked = True
        if not clicked:
            logging.error("Play button not found")
            raise ValueError("Play button not found")
    
    def start_new_game(self):
        start = time.time()
        new_game_clicked = False
        while not new_game_clicked:
            try:
                buttons = self.driver.find_element('class name','game-over-buttons-component').find_elements('xpath','.//*')
                for b in buttons:
                    if 'New' in b.text or 'Accept' in b.text:
                        try:
                            b.click()
                        except WebDriverException:
                            logging.debug("Button not clickable")
                            continue
                        self.new_game_button = b
                        break                
                logging.info("New game button found and clicked")
                new_game_clicked = True
                return True
            except:
                pass
            if time.time() - start > 1*60:
                logging.error("New game button not found")
                return False

    def promote_pawn(self, promotion_piece):
        #//*[@id="board-single"]/div[37]
        promotion_order = ['b','n','q','r']
        promotion_pieces = self.driver.find_elements('class name',"promotion-piece")
        promotion_index = promotion_order.index(promotion_piece)
        promotion_pieces[promotion_index].click()
    
    def read_clock(self):
        try:
            time_str = self.driver.find_elements('xpath','//*[@id="board-layout-player-bottom"]/div/div[3]/span')[0].text
        except:
            time_str = '%21:%37'
        formats = ['%H:%M:%S', '%M:%S', '%M:%S.%f']
        t_datetime = None
        for fmt in formats:
            try:
                t_datetime = datetime.strptime(time_str, fmt)
                break
            except ValueError:
                continue
        if t_datetime is None:
            return timedelta(seconds=30)        
        time = timedelta(hours=t_datetime.hour, minutes=t_datetime.minute, seconds=t_datetime.second, microseconds=t_datetime.microsecond)
        return time
    
    def read_moves(self):
        n = 1
        xpath_template = '//*[@id="live-game-tab-scroll-container"]/wc-move-list/wc-new-move-list/div/div[{n}]/div'
        san_pattern = re.compile(r'^(?:[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?|O-O(?:-O)?)[+#]?$')
        move_line = self.driver.find_elements('xpath',xpath_template.format(n=n))
        if not move_line:
            xpath_template = '//*[@id="live-game-tab-scroll-container"]/wc-move-list/wc-new-move-list/div/div[{n}]/div'
            return []
        moves = []
        while move_line:
            move_line = self.driver.find_elements('xpath',xpath_template.format(n=n))
            if not move_line:
                break
            if bool(san_pattern.match(move_line[0].text)):
                moves.append(move_line[0].text)
            try:
                if bool(san_pattern.match(move_line[1].text)):
                    moves.append(move_line[1].text)
            except:
                pass
            n+=1
        return moves
    
    def get_site_game_state(self):
        self.moves = self.read_moves()
        self.clock = self.read_clock()
        self.gameover, self.game_outcome = self.is_game_over()
        self.get_color()
        #logging.info(f"Game state: {self.moves}, {self.clock}, {self.gameover}")

    def is_game_over(self):
        try:
            game_over_element = self.driver.find_element('class name','game-over-modal-content')
        except e:
            is_game_over = False
            game_outcome = None
            return is_game_over, game_outcome
        is_game_over = game_over_element.is_displayed()
        result = self.driver.find_element('class name','game-over-modal-content').text
        game_outcome = ' '.join(result.split('\n')[:2])
        game_outcome = game_outcome
        return is_game_over, game_outcome
        
    def resign_game(self):
        self.driver.find_element('class name','resign-button-label').click()
        time.sleep(2)

class Factory:
    
    @staticmethod
    def create_browser(browser_choice: str,  user_data_dir: str, profile_directory: str):
        if browser_choice.lower() == 'chrome':
            return ChromeBrowser(user_data_dir, profile_directory)
        elif browser_choice.lower() == 'firefox':
            return FirefoxBrowser(user_data_dir, profile_directory)
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

class ChessGame:
    def __init__(self, engine_path: str, site_interface: ChessSiteInterface, engine_options: dict = None, start_position: str = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', opening_book: str = None, time_control: str = '3 min'):
        self.color = site_interface.color
        self.followed_variant = []
        self.variant_start_ply = 0
        self.variant_followed_for_ply = 0
        if self.color == 'white':
            self.white_perspective = True
        else:
            self.white_perspective = False
        self.piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9
        }
        self.white_material_score = 0
        self.black_material_score = 0
        self.material_diff = 0
        self.moves = []
        self.gameover = False
        self.board = chess.Board(fen=start_position)
        self.analysis = None
        self.analysies = []
        self.start_position = start_position
        self.engine_path = engine_path
        self.engine_options = engine_options
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.opening_book = opening_book
        if engine_options:
            for option, value in engine_options.items():
                self.engine.configure({option: value})
        self.site = site_interface
        total_time, increment = self.parse_time_control(time_control)
        expected_moves = 90
        self.expected_moves = expected_moves
        risk_factor = 0.2
        self.risk_factor = risk_factor
        # Oblicz średni czas na ruch
        self.avg_time_per_move = ((total_time + expected_moves * increment) / expected_moves)        
        # Odchylenie standardowe
        self.sigma = risk_factor * self.avg_time_per_move        
        # Zapisz całkowity dostępny czas
        self.total_time = total_time

    def get_san_moves(self):
        san_moves = []
        temp_board = chess.Board(fen=self.start_position) # Tworzenie kopii planszy
        for move in self.board.move_stack:
            san_moves.append(temp_board.san(move))
            temp_board.push(move)  # Aktualizacja kopii planszy
        return san_moves
    
    def make_move(self, move):
        self.board.push_uci(move)
        self.moves.append(move)
        return self.board
    
    def is_game_synced(self):
        board_moves = self.get_san_moves()
        site_moves = self.site.moves
        if len(site_moves) != len(board_moves):
            return False
        for i,move in enumerate(site_moves):
            if move != board_moves[i]:
                return False
        return True

    def sync_board(self):  
        self.board = chess.Board(fen=self.start_position)               
        for move in self.site.moves:
            self.board.push_san(move)
        self.moves = self.site.moves
        self.white_material_score = self.get_material_score(True)
        self.black_material_score = self.get_material_score(False)
        return self.board
    
    def get_material_score(self, color: bool):
        value = 0
        for piece_type in self.piece_values:
            value += len(self.board.pieces(piece_type, color)) * self.piece_values[piece_type]
        return value
    
    def should_we_resign(self):
        if self.analysis is None:
            return False, None, None
        if self.color == 'white':
            material_diff = self.white_material_score - self.black_material_score
        else:
            material_diff = self.black_material_score - self.white_material_score
        score = self.analysis[0]['score']
        self.material_diff = material_diff
        if material_diff <= -5 and self.analysis[0]['score'].relative.cp < -150:
            return True, self.analysis[0]['score'], material_diff
        else:
            return False, self.analysis[0]['score'], material_diff
    
    def find_best_move(self, time_limit: int = 5, depth_limit: int = 1, multipv: int = 5, wait_for_time_limit: bool = True):
        start_time = time.time()
        # if self.opening_book is not None:
        #     with chess.polyglot.open_reader(self.opening_book) as reader:
        #         try:
        #             entry = reader.find(self.board)
        #             book_move = entry.move()
        #             logging.info(f"Found book move: {book_move}")
        #             analysis = self.engine.analyse(self.board, chess.engine.Limit(time=1, depth=depth_limit),multipv=1)
        #             return book_move, analysis
        #         except IndexError:
        #             logging.info("No book move found, proceeding with engine analysis.")
        # Sprawdź liczbę legalnych ruchów
        num_legal_moves = len(list(self.board.legal_moves))
        analysis = self.engine.analyse(self.board, chess.engine.Limit(time=time_limit, depth=depth_limit),multipv=multipv)
        self.analysis = analysis
        if multipv == 1:
            elapsed = time.time() - start_time
            if elapsed < time_limit and num_legal_moves > 2 and wait_for_time_limit and self.board.ply() > 4:
                logging.info(f"Analysis took too short, sleeping for {(time_limit-elapsed)} seconds")
                time.sleep((time_limit-elapsed))
            self.variant_start_ply = self.board.ply() + 1
            self.variant_followed_for_ply = 1
            self.followed_variant = analysis[0]['pv']
            best_move = analysis[0]['pv'][0]
            return best_move, analysis
        best_cp = -1e10
        for i in range(multipv):
            if self.color == 'white':
                cp = analysis[i]['score'].white().cp
            else:
                cp = analysis[i]['score'].black().cp
            if cp > best_cp:
                best_cp = cp
                best_variant = analysis[i]
                self.analysis = best_variant
        elapsed = time.time() - start_time
        logging.info(f"Analysis time: {elapsed}")
        if elapsed < time_limit and num_legal_moves > 2 and wait_for_time_limit and self.board.ply() > 4:
            logging.info(f"Analysis took too short, sleeping for {(time_limit-elapsed)} seconds")
            time.sleep((time_limit-elapsed))
        self.variant_start_ply = self.board.ply() + 1
        self.variant_followed_for_ply = 1
        self.followed_variant = best_variant[0]['pv']
        best_move = best_variant[0]['pv'][0]
        return best_move, best_variant

    def find_non_losing_move(self, time_limit: int = 5, depth_limit: int = 1, multipv: int = 10):
        start_time = time.time()
        analysis = self.engine.analyse(self.board, chess.engine.Limit(time=time_limit, depth=depth_limit),multipv=multipv)
        best_cp = 1e10
        for i in range(multipv):
            if self.color == 'white':
                cp = analysis[i]['score'].white().cp
            else:
                cp = analysis[i]['score'].black().cp
            if abs(cp) < abs(best_cp):
                best_cp = cp
                best_variant = analysis[i]
                self.analysis = best_variant
                self.analysies.append(best_variant) #tutaj trzeba zmienić żeby dodawało najlepszy wariant a nie ten remisujący
        elapsed = time.time() - start_time
        best_move = best_variant['pv'][0]
        logging.info(f"Analysis time: {elapsed}")
        return best_move, best_variant

    def blunder_detector(self, threshold: float = 200):
        new_analysis = self.analysies[-1]
        prv_analysis = self.analysies[-2]
        if prv_analysis is None or new_analysis is None:
            return False
        if self.color == 'white':
            cp = new_analysis['score'].white().cp
            prv_cp = prv_analysis['score'].white().cp
        else:
            cp = new_analysis['score'].black().cp
            prv_cp = prv_analysis['score'].black().cp
        if prv_cp + threshold <= cp:
            return True
        return False

    def is_variant_followed(self):
        try:
            if self.board.move_stack[-1] == self.followed_variant[self.variant_followed_for_ply]:
                return True
            return False
        except:
            return False
        
    def is_safe_premove(self, move: chess.Move):
        # Pobierz pole docelowe ruchu
        target_square = move.to_square
        
        # Sprawdź, czy na polu docelowym znajduje się bierka Twojego koloru
        piece_on_target = self.board.piece_at(target_square)
        if piece_on_target and piece_on_target.color == (not self.board.turn):
            # Sprawdź, ilu przeciwników atakuje to pole
            attackers = self.board.attackers(self.board.turn, target_square)
            if len(attackers) == 1:
                return True
        return False
    
    def parse_time_control(self, time_control: str):
        # Sprawdzenie formatu z inkrementem: np. '3 | 1'
        if '|' in time_control:
            parts = time_control.split('|')
            minutes = int(parts[0].strip())
            self.increment = int(parts[1].strip())
            self.total_time = minutes * 60
            logging.info(f"Time control: Total time: {self.total_time}, increment: {self.increment}")
            return self.total_time, self.increment
        # Sprawdzenie formatu bez inkrementu: np. '3 min' lub '10 min'
        elif 'min' in time_control:
            minutes = int(re.findall(r'\d+', time_control)[0])
            self.total_time = minutes * 60
            self.increment = 0
            logging.info(f"Time control: Total time: {self.total_time}, increment: {self.increment}")
            return self.total_time, self.increment
        # Jeśli format jest nieznany, zwracamy None
        else:
            raise ValueError(f"Nieznany format kontroli czasowej: {time_control}")
        
    def generate_move_time(self):
        # Losowanie czasu ruchu z zapisanego rozkładu normalnego
        move_time = random.gauss(self.avg_time_per_move, self.sigma)
        
        # Ograniczenie czasów ruchu do pewnych granic
        move_time = max(0, move_time)  # Minimalny czas na ruch to 1 sekunda
        max_time = self.site.clock.total_seconds() / 2  # Maksymalny czas na ruch to połowa dostępnego czasu
        move_time = min(move_time, max_time)  # Maksymalny czas to połowa dostępnego czasu
        return move_time

class ChessBoardClicker:
    def __init__(self, site_interface: ChessSiteInterface, chess_game: ChessGame, debug_mode: bool = True):
        white_perspective = True if site_interface.color == 'white' else False
        self.white_perspective = white_perspective
        self.debug_mode = debug_mode
        self.squares = {}
        self.game = chess_game
        self.chessboard_contour = None
        self.click_colours_keys = site_interface.click_colours_keys
        self.arrow_colours_keys = site_interface.arrow_colours_keys
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

    def get_random_coordinates(self,square):
        left, top = square['top_left']
        right, bottom = square['bottom_right']
        margin = 15
        x = random.randint(left + margin, right - margin)
        y = random.randint(top + margin, bottom - margin)
        return x, y

    def highlight_square(self, square_name, speed: float = 0.1, colour: str = 'red'):
        square = self.squares[square_name]
        center_x, center_y = square['center']        
        keys = self.site_interface.click_colours_keys[colour]
        if keys is not None:
            for key in keys:
                pyautogui.keyDown(key)
        pyautogui.moveTo(center_x, center_y, duration=speed)
        pyautogui.mouseDown(button='right')
        time.sleep(0.08)
        pyautogui.mouseUp(button='right')
        if keys is not None:
            for key in keys:
                pyautogui.keyUp(key)

    def draw_arrow(self, move_uci: str, speed: float = 0.2, colour: str = 'red'):
        start_square = move_uci[:2]
        end_square = move_uci[2:4]
        if len(move_uci) > 4:
            promotion_piece = move_uci[4]
            logging.info(f"Promote to {promotion_piece}")
        start_square = self.squares[start_square]
        end_square = self.squares[end_square]
        start_x, start_y = start_square['center']
        end_x, end_y = end_square['center']        
        keys = self.site_interface.arrow_colours_keys[colour]
        if keys is not None:
            for key in keys:
                pyautogui.keyDown(key)
        pyautogui.moveTo(start_x, start_y, duration=speed)
        time.sleep(0.1)
        pyautogui.dragTo(end_x, end_y, duration=speed, button='right')
        if keys is not None:
            for key in keys:
                pyautogui.keyUp(key)
        

    def draw_arrow_between_random_squares(self, speed: float = 0.1, colour: str = 'red'):
        # Temp copy of actual game board
        tmp_board = copy.deepcopy(self.game.board)
        # Change perspective (we only executing this method when it is not our move)
        tmp_board.turn = not tmp_board.turn
        # list of all legal moves in tmp_board
        legal_moves = list(tmp_board.legal_moves)
        # Choose random move
        random_move = random.choice(legal_moves)
        # Draw arrow with randomly chosen move
        self.draw_arrow(str(random_move.uci()), speed, colour)        
    
    def make_move(self, move_uci: str, move_speed: float = 0.1, drag_speed: float = 0.2):
        start_square = move_uci[:2]
        end_square = move_uci[2:4]
        promotion_piece = None
        if len(move_uci) > 4:
            promotion_piece = move_uci[4]
        start_square = self.squares[start_square]
        end_square = self.squares[end_square]
        start_x, start_y = self.get_random_coordinates(start_square)
        end_x, end_y = self.get_random_coordinates(end_square)
        pyautogui.moveTo(start_x, start_y, move_speed, pyautogui.easeInElastic)
        pyautogui.dragTo(end_x, end_y, drag_speed, pyautogui.easeInElastic, button='left')
        if promotion_piece is not None:
            try:
                self.site_interface.promote_pawn(promotion_piece)
            except Exception as e:
                logging.error(e)

def auto_play_best_moves():
    config_dict = yaml.safe_load(open('config.yaml'))['auto_play_best_moves']
    browser_choice = config_dict['browser_choice']
    site_choice = config_dict['site_choice']
    user_data_dir = config_dict['user_data_dir']
    profile_directory = config_dict['profile_directory']
    engine_path = config_dict['engine_path']
    engine_wieghts_path = config_dict['engine_wieghts_path']
    backend = config_dict['backend']
    engine_options = {
        "WeightsFile": engine_wieghts_path,
        "Backend": backend,
        "MinibatchSize": "1",
        "MaxPrefetch": "4"
    }
    opening_book = config_dict['opening_book']
    browser = Factory.create_browser(browser_choice, user_data_dir, profile_directory)
    driver = browser.configure_browser()
    site = Factory.create_chess_site(site_choice, driver)
    driver.get(site.site)
    time.sleep(2)
    time_control = config_dict['time_control']
    site.start_first_game(time_control=time_control)
    succes = site.wait_for_game()
    if not succes:
        driver.quit()
        return    
    startposition = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1' # '7K/8/8/8/8/8/pk6/8 w - - 0 1'
    while True:
        moves = []
        color = site.get_color()
        game = ChessGame(engine_path=engine_path, site_interface=site, engine_options=engine_options, start_position=startposition, opening_book=opening_book, time_control=time_control)
        clicker = ChessBoardClicker(site_interface=site, chess_game=game, debug_mode=True)   
        clicker.get_squares()
        while not game.gameover:
            site.get_site_game_state()
            game_synced = game.is_game_synced()
            if not game_synced:
                game.sync_board()
            if site.gameover:
                logging.info(f"Game over. We were playing as: {game.color}. Game outcome: {site.game_outcome}")
                break                
            on_move = 'white' if game.board.turn else 'black'
            if on_move != site.color:
                resign, cp_score, material_diff = game.should_we_resign()
                #resign=False
                if resign:
                    logging.info(f"Resigning game. Material difference: {material_diff}. Score: {cp_score}")
                    try:
                        game.site.resign_game()
                    except:
                        pass
                if not resign:
                    if random.random() < 0.1 and game.board.ply() > 2:
                        logging.info(f"Drawing random arrow because it's not out move, we play as {game.color}. Game ply: {game.board.ply()}. Time on clock: {site.clock}")
                        clicker.draw_arrow_between_random_squares()
                continue 
            logging.info(f"It's our move. We play as {site.color}. Game ply: {game.board.ply()}. Time on clock: {site.clock}")
            if game.is_variant_followed() and game.variant_followed_for_ply+1<len(game.followed_variant):
                logging.info(f"Opponent is following our variant. Making move.")
                logging.info(f"We are following variant {game.followed_variant}")
                logging.info(f"Variant followed for {game.variant_followed_for_ply} plys")
                random_delay = 0#int(round(random.normalvariate(1, 1),0))
                random_delay = 0 if random_delay < 0 else random_delay
                time.sleep(random_delay)
                game.variant_followed_for_ply += 1
                move_to_draw = game.followed_variant[game.variant_followed_for_ply]
                game.variant_followed_for_ply += 1
            else:
                random_think = game.generate_move_time()
                random_think = 0 if site.clock < timedelta(seconds=45) else random_think
                logging.info(f"Thinking time: {random_think}. Going to analyze the position and pick best move. Board position: {game.board.fen()}")
                depth_limit = 1 #if game.board.ply() > 12 else 5
                if game.board.is_checkmate() == False:
                    move_to_draw, analysis = game.find_best_move(time_limit=random_think, depth_limit=depth_limit, multipv=1)
                else:
                    continue
            clicker.make_move(move_to_draw.uci())
            game.make_move(move_to_draw.uci())
            try:
                if game.is_safe_premove(game.followed_variant[game.variant_followed_for_ply+1]):
                    logging.info(f"We are following variant with safe premove {game.followed_variant[game.variant_followed_for_ply+1]}, making premove.")
                    clicker.make_move(game.followed_variant[game.variant_followed_for_ply+1].uci())
            except:
                pass            
            logging.info(f'Sugessted move: {move_to_draw.uci()}')
            logging.info(f"Score evaluation: {analysis[0]['score']} | Material diff: {game.material_diff}")       
        time.sleep(random.randint(5,10))
        succes = site.start_new_game()
        game.engine.quit()
        if not succes:
            driver.quit()
            return        
        succes = site.wait_for_game()
        if not succes:
            driver.quit()
            return
        
def highlight_best_piece():
    config_dict = yaml.safe_load(open('config.yaml'))['highlight_best_piece']
    browser_choice = config_dict['browser_choice']
    site_choice = config_dict['site_choice']
    user_data_dir = config_dict['user_data_dir']
    profile_directory = config_dict['profile_directory']
    engine_path = config_dict['engine_path']
    engine_wieghts_path = config_dict['engine_wieghts_path']
    backend = config_dict['backend']
    engine_options = {
        "WeightsFile": engine_wieghts_path,
        "Backend": backend,
        "MinibatchSize": "1",
        "MaxPrefetch": "4"
    }
    browser = Factory.create_browser(browser_choice, user_data_dir, profile_directory)
    driver = browser.configure_browser()
    site = Factory.create_chess_site(site_choice, driver)
    driver.get(site.site)
    time.sleep(2)
    succes = site.wait_for_game()
    if not succes:
        driver.quit()
        return    
    startposition = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1' # '7K/8/8/8/8/8/pk6/8 w - - 0 1'
    analyzed = False
    while True:
        moves = []
        color = site.get_color()
        game = ChessGame(engine_path=engine_path, site_interface=site, engine_options=engine_options, start_position=startposition)
        clicker = ChessBoardClicker(site_interface=site, chess_game=game, debug_mode=True)    
        clicker.get_squares()        
        while not game.gameover:
            site.get_site_game_state()
            game_synced = game.is_game_synced()
            if not game_synced:
                game.sync_board()
                analyzed = False
            if site.gameover:
                break
            on_move = 'white' if game.board.turn else 'black'
            if on_move != site.color or analyzed:
                continue 
            logging.info(f"It's our move.")            
            random_think = 5
            logging.info(f"Thinking time: {random_think}. Going to analyze the position and highlight piece with best move.")
            depth_limit = 20
            move_to_draw, analysis = game.find_best_move(time_limit=random_think, depth_limit=depth_limit, multipv=1, wait_for_time_limit=False)
            square = chess.square_name(move_to_draw.from_square)
            clicker.highlight_square(square)
            analyzed = True          
            logging.info(f'FEN: {game.board.fen()}')
            logging.info(f'Sugessted quare: {square}')
            logging.info(f"Score evaluation: {analysis[0]['score']}")       
        game.engine.quit()
        n=0
        while driver.current_url == site.game_www and n<120:
            time.sleep(0.5)
            n+=1      
        succes = site.wait_for_game()
        if not succes:
            driver.quit()
            return
        
def give_non_losing_move():
    config_dict = yaml.safe_load(open('config.yaml'))['give_non_losing_move']
    browser_choice = config_dict['browser_choice']
    site_choice = config_dict['site_choice']
    user_data_dir = config_dict['user_data_dir']
    profile_directory = config_dict['profile_directory']
    engine_path = config_dict['engine_path']
    engine_wieghts_path = config_dict['engine_wieghts_path']
    backend = config_dict['backend']
    engine_options = {
        "WeightsFile": engine_wieghts_path,
        "Backend": backend,
        "MinibatchSize": "1",
        "MaxPrefetch": "4"
    }
    browser = Factory.create_browser(browser_choice, user_data_dir, profile_directory)
    driver = browser.configure_browser()
    site = Factory.create_chess_site(site_choice, driver)
    driver.get(site.site)
    time.sleep(2)
    succes = site.wait_for_game()
    if not succes:
        driver.quit()
        return    
    startposition = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1' # '7K/8/8/8/8/8/pk6/8 w - - 0 1'
    analyzed = False
    while True:
        moves = []
        color = site.get_color()
        game = ChessGame(engine_path=engine_path, site_interface=site, engine_options=engine_options, start_position=startposition)
        clicker = ChessBoardClicker(site_interface=site, chess_game=game, debug_mode=True)    
        clicker.get_squares()        
        while not game.gameover:
            site.get_site_game_state()
            game_synced = game.is_game_synced()
            if not game_synced:
                game.sync_board()
                analyzed = False
            if site.gameover:
                break
            on_move = 'white' if game.board.turn else 'black'
            if on_move != site.color or analyzed:
                continue 
            logging.info(f"It's our move.")            
            random_think = 5
            logging.info(f"Thinking time: {random_think}. Going to analyze the position and give non losing move.")
            depth_limit = 20
            move_to_draw, analysis = game.find_non_losing_move(time_limit=random_think, depth_limit=depth_limit, multipv=10)
            clicker.draw_arrow(move_to_draw.uci(), colour='green')
            analyzed = True
            is_blunder = game.blunder_detector()
            if is_blunder:
                logging.info(f"Blunder detected. Try to find best move. Highlighting best piece.")
                best_move, _ = game.find_best_move(time_limit=random_think, depth_limit=depth_limit, multipv=1, wait_for_time_limit=False)
                square = chess.square_name(best_move.from_square)
                clicker.highlight_square(square, colour='red')           
            logging.info(f'FEN: {game.board.fen()}')
            logging.info(f"Score evaluation: {analysis['score']}")       
        game.engine.quit()
        n=0
        while driver.current_url == site.game_www and n<120:
            time.sleep(0.5)
            n+=1      
        succes = site.wait_for_game()
        if not succes:
            driver.quit()
            return

def close_webdrivers():
    for process in psutil.process_iter(['pid', 'name']):
        if 'chromedriver' in process.info['name'] or 'geckodriver' in process.info['name']:
            logging.info(f"Zamykanie procesu {process.info['name']} o PID {process.info['pid']}")
            process.terminate()

def close_webdriver_browsers():
    browsers = ['chrome', 'firefox', 'msedge']
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        if any(browser in process.info['name'].lower() for browser in browsers):
            cmdline = " ".join(process.info['cmdline']).lower()
            if '--remote-debugging-port=2137' in cmdline or '--enable-automation' in cmdline or 'webdriver' in cmdline:
                logging.info(f"Zamykanie procesu przeglądarki {process.info['name']} o PID {process.info['pid']}")
                process.terminate()

if __name__ == "__main__":
    while True:
        #auto_play_best_moves()
        try:
            auto_play_best_moves()
            #highlight_best_piece()
            #give_non_losing_move()
        except Exception as e:
            logging.error('Unhandled exception caught')
            logging.error(e)
            logging.error(traceback.format_exc())
            close_webdrivers()
            close_webdriver_browsers()
            os._exit(1)

        