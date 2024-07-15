import pyautogui
import cv2
import numpy as np
from PIL import Image
import time
import matplotlib.pyplot as plt


class ChessBoardClicker:
    def __init__(self, debug_mode: bool = True, white_perspective: bool = True):
        self.white_perspective = white_perspective
        self.debug_mode = debug_mode
        self.squares = {}
        self.chessboard_contour = None
        self.click_colours_keys = {'red' : None,
                        'yellow': 'ctrl',
                        'green': 'shift',
                        'blue': 'alt'
                        }
        self.arrow_colours_keys = {'yellow' : None,
                        'red': 'ctrl',
                        'green': 'shift',
                        'blue': 'alt'
                        }

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
        # Rysowanie konturu szachownicy na obrazie (opcjonalne)
        if chessboard_contour is not None and self.debug_mode:
            cv2.drawContours(screenshot_cv, [chessboard_contour], -1, (0, 255, 0), 3)
            cv2.imwrite("chessboard_detected.png", screenshot_cv)
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

    def highlight_square(self, square_name, speed: float = 0.1, colour: str = 'red'):
        square = self.squares[square_name]
        center_x, center_y = square['center']
        pyautogui.moveTo(center_x, center_y, duration=speed)
        key = self.click_colours_keys[colour]
        if key is not None:
            pyautogui.keyDown(key)
        pyautogui.rightClick()
        if key is not None:
            pyautogui.keyUp(key)

    def draw_arrow(self, start_square, end_square, speed: float = 0.1, colour: str = 'red'):
        start_square = self.squares[start_square]
        end_square = self.squares[end_square]
        start_x, start_y = start_square['center']
        end_x, end_y = end_square['center']
        pyautogui.moveTo(start_x, start_y, duration=speed)
        key = self.arrow_colours_keys[colour]
        if key is not None:
            pyautogui.keyDown(key)
        pyautogui.dragTo(end_x, end_y, duration=speed, button='right')
        if key is not None:
            pyautogui.keyUp(key)
    
    def make_move(self, start_square, end_square, speed: float = 0.1):
        start_square = self.squares[start_square]
        end_square = self.squares[end_square]
        start_x, start_y = start_square['center']
        end_x, end_y = end_square['center']
        pyautogui.moveTo(start_x, start_y, duration=speed)
        pyautogui.dragTo(end_x, end_y, duration=speed, button='left')


if __name__ == "__main__":
    white_perspective = True
    clicker = ChessBoardClicker(debug_mode=True, white_perspective=white_perspective)
    clicker.get_squares()
    clicker.highlight_square("a1", colour='red')
    clicker.highlight_square("b3", colour='blue')
    clicker.highlight_square("e2", colour='green')
    clicker.highlight_square("h8", colour='yellow')
    clicker.highlight_square("h1")
    clicker.highlight_square("f1")
    clicker.draw_arrow("d2", "e4", colour='green')
    clicker.draw_arrow("g6", "h8")
    clicker.make_move("c4", "b5")