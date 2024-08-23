# Zdefiniuj ścieżkę do środowiska wirtualnego (venv)
$venvPath = "C:\Users\mjakimiuk\OneDrive - PEX PharmaSequence Sp z o.o\Dokumenty\python\chess_automate\.venv\Scripts\Activate.ps1"

# Zdefiniuj wzorzec do wyszukiwania w ścieżce wykonywalnej
$pattern = "*chess_automate*"

# Zdefiniuj ścieżkę do skryptu Pythona, który ma być uruchamiany, jeśli proces nie działa
$pythonScriptDir = "C:\Users\mjakimiuk\OneDrive - PEX PharmaSequence Sp z o.o\Dokumenty\python\chess_automate"
$pythonScriptPath = "C:\Users\mjakimiuk\OneDrive - PEX PharmaSequence Sp z o.o\Dokumenty\python\chess_automate\chess_automate.py"

# Aktywuj środowisko wirtualne
& $venvPath

# Czas w sekundach pomiędzy sprawdzeniami
$checkInterval = 10

cd $pythonScriptDir

Start-Sleep -Seconds $checkInterval

# Pętla while true
while ($true) {
    # Wyszukaj procesy Python, które pasują do wzorca w ścieżce
    $processes = Get-WmiObject Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.ExecutablePath -like $pattern }

    # Jeśli proces istnieje, wyświetl informacje o nim
    if ($processes) {
        $processes | Select-Object ProcessId, Name, ExecutablePath, CommandLine | Format-Table -AutoSize
    } else {
        Write-Output "Nie znaleziono procesu Python z pasującą ścieżką: $pattern"
        Write-Output "Uruchamiam skrypt Pythona: $pythonScriptPath"

        # Uruchom skrypt Pythona
        python $pythonScriptPath
    }

    # Odczekaj przed kolejną iteracją
    Start-Sleep -Seconds $checkInterval
}
