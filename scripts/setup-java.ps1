# 在本仓库安装便携版 JDK 17 + Maven（无需系统级安装）
# 用法（PowerShell 管理员或普通用户均可）:
#   powershell -ExecutionPolicy Bypass -File scripts/setup-java.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Tools = Join-Path $Root "tools"
$JdkDir = Join-Path $Tools "jdk-17"
$MavenDir = Join-Path $Tools "maven"

New-Item -ItemType Directory -Force -Path $Tools | Out-Null

function Expand-ArchiveZip($ZipPath, $DestParent) {
    $before = @(Get-ChildItem $DestParent -Directory | ForEach-Object { $_.FullName })
    Expand-Archive -Path $ZipPath -DestinationPath $DestParent -Force
    $after = Get-ChildItem $DestParent -Directory | Where-Object { $before -notcontains $_.FullName }
    if (-not $after) {
        $after = Get-ChildItem $DestParent -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    } else {
        $after = $after | Select-Object -First 1
    }
    if (-not $after) { throw "解压后未找到目录: $ZipPath" }
    return $after.FullName
}

# ---------- JDK 17 (Eclipse Temurin) ----------
if (-not (Test-Path (Join-Path $JdkDir "bin\java.exe"))) {
    Write-Host "[setup] 下载 JDK 17 ..."
    $jdkZip = Join-Path $Tools "jdk-17.zip"
    $jdkUrl = "https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse?project=jdk"
    Invoke-WebRequest -Uri $jdkUrl -OutFile $jdkZip -UseBasicParsing
    if (-not (Test-Path $jdkZip)) { throw "JDK 下载失败: $jdkZip" }
    $extracted = Expand-ArchiveZip $jdkZip $Tools
    Remove-Item $jdkZip
    if ($extracted -ne $JdkDir) {
        if (Test-Path $JdkDir) { Remove-Item -Recurse -Force $JdkDir }
        Rename-Item $extracted $JdkDir
    }
    Write-Host "[setup] JDK 安装完成: $JdkDir"
} else {
    Write-Host "[setup] JDK 已存在: $JdkDir"
}

# ---------- Maven ----------
$mvnExe = Join-Path $MavenDir "bin\mvn.cmd"
if (-not (Test-Path $mvnExe)) {
    Write-Host "[setup] 下载 Maven 3.9.9 ..."
    $mvnZip = Join-Path $Tools "maven.zip"
    $mvnUrl = "https://archive.apache.org/dist/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.zip"
    Invoke-WebRequest -Uri $mvnUrl -OutFile $mvnZip -UseBasicParsing
    if (-not (Test-Path $mvnZip)) { throw "Maven 下载失败: $mvnZip" }
    $extracted = Expand-ArchiveZip $mvnZip $Tools
    Remove-Item $mvnZip
    if ($extracted -ne $MavenDir) {
        if (Test-Path $MavenDir) { Remove-Item -Recurse -Force $MavenDir }
        Rename-Item $extracted $MavenDir
    }
    Write-Host "[setup] Maven 安装完成: $MavenDir"
} else {
    Write-Host "[setup] Maven 已存在: $MavenDir"
}

# ---------- env script ----------
$envScript = Join-Path $Root "scripts\env-java.ps1"
$envContent = @'
# Enable portable JDK/Maven in current PowerShell session
$Root = Split-Path -Parent $PSScriptRoot
$env:JAVA_HOME = Join-Path $Root "tools\jdk-17"
$env:Path = "$env:JAVA_HOME\bin;" + (Join-Path $Root "tools\maven\bin") + ";" + $env:Path
Write-Host "JAVA_HOME=$env:JAVA_HOME"
java -version
mvn -version
'@
Set-Content -Encoding UTF8 -Path $envScript -Value $envContent

Write-Host ""
Write-Host "完成。在新终端执行:"
Write-Host "  . .\scripts\env-java.ps1"
Write-Host "  mvn -f backend\java\pom.xml spring-boot:run"
