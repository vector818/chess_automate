import os
import chess.pgn

def extract_games_by_opening(input_folder, output_file, opening_name):
    # Lista do przechowywania gier na podstawie otwarcia
    matched_games = []

    # Iteracja po wszystkich plikach w folderze
    for i,filename in enumerate(os.listdir(input_folder)):
        print(f'Przetwarzanie pliku {filename}. Plik numer {i+1} z {len(os.listdir(input_folder))}.')
        if filename.endswith('.pgn'):
            with open(os.path.join(input_folder, filename), 'r') as pgn_file:
                while True:
                    game = chess.pgn.read_game(pgn_file)
                    if game is None:
                        break
                    
                    # Sprawdzenie, czy w sekcji otwarcia jest podane otwarcie
                    if opening_name.lower() in game.headers.get("Opening", "").lower():
                        matched_games.append(game)

    # Zapisanie gier do jednego pliku PGN
    with open(output_file, 'w') as output:
        for game in matched_games:
            output.write(str(game) + '\n\n')  # Dwa nowe wiersze między grami

    return len(matched_games)  # Zwraca liczbę znalezionych gier

# Użycie funkcji
input_folder = 'C:/Users/mjakimiuk/Downloads/Lichess Elite Database'  # Ścieżka do folderu z plikami PGN
output_file = 'C:/Users/mjakimiuk/Downloads/Lichess Elite Database/london_system_games.pgn'  # Nazwa pliku wyjściowego
opening_name = 'London System'  # Nazwa otwarcia do wyszukania

# Wywołanie funkcji
num_games = extract_games_by_opening(input_folder, output_file, opening_name)

print(f'Znaleziono {num_games} gier dla otwarcia "{opening_name}" i zapisano do {output_file}.')
