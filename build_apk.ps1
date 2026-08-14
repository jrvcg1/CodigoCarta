$ErrorActionPreference = "Stop"

$JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$ANDROID_HOME = "C:\Users\ruedaj\AppData\Local\Android\Sdk"
$BUILD_TOOLS = "$ANDROID_HOME\build-tools\34.0.0"
$ANDROID_JAR = "$ANDROID_HOME\platforms\android-34\android.jar"
$PROJ_DIR = "C:\Temp\CodigoCarta\android_apk_project"
$OUT_DIR = "$PROJ_DIR\out"
$UNALIGNED_APK = "$OUT_DIR\apk\app-unaligned.apk"
$FINAL_APK = "C:\Temp\CodigoCarta\CodigoCarta_Mentalismo.apk"

Write-Host "Iniciando compilacion de Codigo Carta Mentalismo APK..." -ForegroundColor Cyan

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

Write-Host "[2/5] Enlazando APK sin alinear..."
& "$BUILD_TOOLS\aapt2.exe" link -o $UNALIGNED_APK -I $ANDROID_JAR --manifest "$PROJ_DIR\app\src\main\AndroidManifest.xml" "$OUT_DIR\res\compiled.flat.zip" --java "$OUT_DIR\gen"

# 3. Compilar código Java
Write-Host "[3/5] Compilando fuentes Java (javac)..."
$javaFiles = Get-ChildItem -Recurse -Path "$PROJ_DIR\app\src\main\java" -Filter "*.java" | Select-Object -ExpandProperty FullName
$genJavaFiles = Get-ChildItem -Recurse -Path "$OUT_DIR\gen" -Filter "*.java" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
$allJavaFiles = @($javaFiles) + @($genJavaFiles)

& "$JAVA_HOME\bin\javac.exe" -d "$OUT_DIR\obj" -classpath $ANDROID_JAR -source 8 -target 8 $allJavaFiles

# 4. Convertir .class a DEX (d8)
Write-Host "[4/5] Generando Dalvik Executable (d8 classes.dex)..."
$classFiles = Get-ChildItem -Recurse -Path "$OUT_DIR\obj" -Filter "*.class" | Select-Object -ExpandProperty FullName
& "$BUILD_TOOLS\d8.bat" --min-api 24 --lib $ANDROID_JAR --output "$OUT_DIR\dex" $classFiles

# Añadir classes.dex dentro del APK usando Python
$pyCmd = "import zipfile; z = zipfile.ZipFile(r'$UNALIGNED_APK', 'a'); z.write(r'$OUT_DIR\dex\classes.dex', 'classes.dex'); z.close()"
python -c $pyCmd

# 5. Alinear y Firmar APK
Write-Host "[5/5] Alineando y Firmando la APK (zipalign + apksigner)..."
if (Test-Path $FINAL_APK) { Remove-Item -Force $FINAL_APK }
& "$BUILD_TOOLS\zipalign.exe" -f 4 $UNALIGNED_APK $FINAL_APK

$keyStore = "$OUT_DIR\debug.keystore"
& "$JAVA_HOME\bin\keytool.exe" -genkeypair -keystore $keyStore -storepass android -alias androiddebugkey -keypass android -dname "CN=CodigoCarta,O=Mentalismo,C=ES" -keyalg RSA -keysize 2048 -validity 10000

& "$BUILD_TOOLS\apksigner.bat" sign --ks $keyStore --ks-pass pass:android --key-pass pass:android --ks-key-alias androiddebugkey $FINAL_APK

Write-Host "APK COMPILADA Y FIRMADA CON EXITO EN: $FINAL_APK" -ForegroundColor Green
