# Ścieżka do venv
$venvPath = "C:\Users\micha\OneDrive\Documents\py\chess_automate\.venv\Scripts\Activate.ps1"

# Ścieżka do pliku Pythona
$pythonScriptPath = "C:\Users\micha\OneDrive\Documents\py\chess_automate\chess_automate.py"

# Nazwa procesu Pythona
$pythonProcessName = "python"

# Interwał czasu (w sekundach)
$interval = 60

& $venvPath

while ($true) {
    # Sprawdzanie, czy skrypt Pythona działa
    $processRunning = Get-Process | Where-Object { $_.Path -eq $pythonScriptPath }

    if (-not $processRunning) {
        # Jeśli skrypt nie działa, uruchom go w aktywowanym środowisku venv
        Start-Process "python" -ArgumentList $pythonScriptPath
        Write-Output "Skrypt Python został uruchomiony w venv."
    } else {
        Write-Output "Skrypt Python już działa."
    }

    # Czekanie przez określony czas
    Start-Sleep -Seconds $interval
}
