$ErrorActionPreference = "Stop"

$JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
if (-not (Test-Path "$JAVA_HOME\bin\javac.exe")) {
    $JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.19.7-hotspot"
}

$ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
$BUILD_TOOLS = "$ANDROID_HOME\build-tools\34.0.0"
$ANDROID_JAR = "$ANDROID_HOME\platforms\android-34\android.jar"
$PROJ_DIR = (Get-Item "android_consola_project").FullName
$OUT_DIR = "$PROJ_DIR\out"
$ASSETS_DIR = "$PROJ_DIR\app\src\main\assets"
$UNALIGNED_APK = "$OUT_DIR\apk\app-unaligned.apk"
$FINAL_APK = (Join-Path (Get-Location) "CodigoCarta_Consola.apk")

Write-Host "Iniciando compilacion de Codigo Carta Consola Oraculo APK..." -ForegroundColor Cyan

# 1. Preparar directorios de salida
if (Test-Path $OUT_DIR) { Remove-Item -Recurse -Force $OUT_DIR }
New-Item -ItemType Directory -Path "$OUT_DIR\res" | Out-Null
New-Item -ItemType Directory -Path "$OUT_DIR\gen" | Out-Null
New-Item -ItemType Directory -Path "$OUT_DIR\obj" | Out-Null
New-Item -ItemType Directory -Path "$OUT_DIR\dex" | Out-Null
New-Item -ItemType Directory -Path "$OUT_DIR\apk" | Out-Null

# 2. Compilar recursos con AAPT2
Write-Host "[1/5] Compilando recursos (aapt2)..."
& "$BUILD_TOOLS\aapt2.exe" compile --dir "$PROJ_DIR\app\src\main\res" -o "$OUT_DIR\res\compiled.flat.zip"

Write-Host "[2/5] Enlazando APK con assets (aapt2 link -A assets)..."
& "$BUILD_TOOLS\aapt2.exe" link -o $UNALIGNED_APK -I $ANDROID_JAR --manifest "$PROJ_DIR\app\src\main\AndroidManifest.xml" -A $ASSETS_DIR --min-sdk-version 21 --target-sdk-version 34 "$OUT_DIR\res\compiled.flat.zip" --java "$OUT_DIR\gen"

# 3. Compilar código Java
Write-Host "[3/5] Compilando fuentes Java (javac)..."
$javaFiles = Get-ChildItem -Recurse -Path "$PROJ_DIR\app\src\main\java" -Filter "*.java" | Select-Object -ExpandProperty FullName
$genJavaFiles = Get-ChildItem -Recurse -Path "$OUT_DIR\gen" -Filter "*.java" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
$allJavaFiles = @($javaFiles) + @($genJavaFiles)

& "$JAVA_HOME\bin\javac.exe" -d "$OUT_DIR\obj" -classpath $ANDROID_JAR -source 8 -target 8 $allJavaFiles
if ($LASTEXITCODE -ne 0) { throw 'Error en compilacion javac' }

# 4. Convertir .class a DEX (d8)
Write-Host "[4/5] Generando Dalvik Executable (d8 classes.dex)..."
$classFiles = Get-ChildItem -Recurse -Path "$OUT_DIR\obj" -Filter "*.class" | Select-Object -ExpandProperty FullName
& "$BUILD_TOOLS\d8.bat" --min-api 21 --lib $ANDROID_JAR --output "$OUT_DIR\dex" $classFiles
if ($LASTEXITCODE -ne 0) { throw 'Error en d8' }

# Añadir classes.dex dentro del APK usando Python
$pyCmd = "import zipfile; z = zipfile.ZipFile(r'$UNALIGNED_APK', 'a'); z.write(r'$OUT_DIR\dex\classes.dex', 'classes.dex'); z.close()"
python -c $pyCmd

# 5. Alinear y Firmar APK (V1 + V2 + V3 Signature Schemes)
Write-Host "[5/5] Alineando y Firmando la APK (zipalign + apksigner V1/V2/V3)..."
if (Test-Path $FINAL_APK) { Remove-Item -Force $FINAL_APK }
& "$BUILD_TOOLS\zipalign.exe" -f 4 $UNALIGNED_APK $FINAL_APK

$keyStore = "$OUT_DIR\debug.keystore"
& "$JAVA_HOME\bin\keytool.exe" -genkeypair -keystore $keyStore -storepass android -alias androiddebugkey -keypass android -dname "CN=CodigoCartaConsola,O=Mentalismo,C=ES" -keyalg RSA -keysize 2048 -validity 10000

& "$BUILD_TOOLS\apksigner.bat" sign --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true --ks $keyStore --ks-pass pass:android --key-pass pass:android --ks-key-alias androiddebugkey $FINAL_APK

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "APK CONSOLA COMPILADA Y FIRMADA CON EXITO EN: $FINAL_APK" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
