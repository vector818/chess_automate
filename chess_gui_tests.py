import tkinter as tk
from tkinter import filedialog, messagebox
import chess.engine
import time
import threading
import logging

# Konfiguracja logowania
handlers = [
    logging.FileHandler('logs/log.log', encoding='utf-8'),
    logging.StreamHandler()
]
logging.basicConfig(handlers=handlers, format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

class ChessApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chess Engine Simulator")
        self.geometry("400x300")
        
        # Ścieżka do silnika
        self.engine_path = None
        
        # Tworzenie GUI
        self.create_widgets()

    def create_widgets(self):
        # Przycisk do wyboru ścieżki do silnika
        self.engine_label = tk.Label(self, text="Engine Path:")
        self.engine_label.pack(pady=10)
        
        self.engine_path_entry = tk.Entry(self, width=40)
        self.engine_path_entry.pack(pady=5)
        
        self.browse_button = tk.Button(self, text="Browse", command=self.browse_engine)
        self.browse_button.pack(pady=5)
        
        # Przycisk do uruchomienia gry silników
        self.start_button = tk.Button(self, text="Start Game", command=self.start_game)
        self.start_button.pack(pady=10)

        # Przycisk wyjścia
        self.quit_button = tk.Button(self, text="Quit", command=self.quit)
        self.quit_button.pack(pady=5)

        # Logi w GUI
        self.log_text = tk.Text(self, height=10, width=50)
        self.log_text.pack(pady=10)

    def browse_engine(self):
        # Otwieranie okna dialogowego do wyboru ścieżki do silnika
        self.engine_path = filedialog.askopenfilename(title="Select Chess Engine")
        self.engine_path_entry.delete(0, tk.END)
        self.engine_path_entry.insert(0, self.engine_path)
        logging.info(f"Selected engine path: {self.engine_path}")

    def start_game(self):
        # Sprawdzenie czy silnik został wybrany
        if not self.engine_path:
            messagebox.showerror("Error", "Please select an engine path!")
            return
        
        logging.info("Starting game between two engines...")
        
        # Uruchamianie symulacji w osobnym wątku, żeby GUI nie zamarzało
        game_thread = threading.Thread(target=self.run_engine_game)
        game_thread.start()

    def run_engine_game(self):
        try:
            with chess.engine.SimpleEngine.popen_uci(self.engine_path) as engine1, chess.engine.SimpleEngine.popen_uci(self.engine_path) as engine2:
                board = chess.Board()
                
                # Dopóki gra trwa
                while not board.is_game_over():
                    # Silnik1 robi ruch
                    result1 = engine1.play(board, chess.engine.Limit(time=1, depth=20))
                    board.push(result1.move)
                    self.update_log(f"Engine 1 plays: {result1.move}")
                    
                    if board.is_game_over():
                        break
                    
                    # Minimalny czas między ruchami
                    time.sleep(1)
                    
                    # Silnik2 robi ruch
                    result2 = engine2.play(board, chess.engine.Limit(time=1, depth=20))
                    board.push(result2.move)
                    self.update_log(f"Engine 2 plays: {result2.move}")
                    
                    # Minimalny czas między ruchami
                    time.sleep(1)

                self.update_log(f"Game over: {board.result()}")

        except Exception as e:
            logging.error(f"Error during engine game: {str(e)}")
            self.update_log(f"Error: {str(e)}")

    def update_log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

if __name__ == "__main__":
    app = ChessApp()
    app.mainloop()
