$ErrorActionPreference = "Stop"

$app_name = "Wallet"
$temp_data_building = "temp_data"
mkdir $temp_data_building -ErrorAction SilentlyContinue
if (-not $args[0]) {
	$app_path = Get-Location
	$app_path = "$app_path\$app_name"
} else {
    if (Test-Path $args) {
        $app_path = "$args\$app_name"
    } else {
        Write-Output "Invalid path provided: $args"
        exit
    }
}

$build_folder = [System.IO.Path]::GetDirectoryName($app_path)

Write-Output "Building app in $build_folder"
Write-Output "Proceed with building executable"

& "D:\Python 3.11\python.exe" -m PyInstaller "$app_name.spec" --noconfirm --distpath "$build_folder" --workpath "$temp_data_building"

mkdir "$app_path\_internal\logs"
mkdir "$app_path\_internal\backup"

[System.Environment]::SetEnvironmentVariable("WalletAppPath", $app_path, "User")
Remove-Item -Recurse -Force $temp_data_building