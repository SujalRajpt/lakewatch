@echo off
setlocal

title LakeWatch Simulator Test

set "BASE=http://localhost:9000"
set "BACKEND=http://localhost:8000"

echo.
echo ==========================================
echo       LAKEWATCH SIMULATOR TEST
echo ==========================================
echo.

REM ==================================================
REM 1. HEALTH
REM ==================================================

echo [1/10] Testing simulator health...
curl.exe -s "%BASE%/health"
echo.
echo.

REM ==================================================
REM 2. LAKES
REM ==================================================

echo [2/10] Testing lake list...
curl.exe -s "%BASE%/simulation/lakes"
echo.
echo.

REM ==================================================
REM 3. LAKE CONTROL
REM ==================================================

echo [3/10] Testing lake stress control...
curl.exe -s -X POST "%BASE%/simulation/lakes/LAKE-001/control" ^
  -H "Content-Type: application/json" ^
  -d "{\"stress_level\":100}"
echo.
echo.

echo Checking LAKE-001 control...
curl.exe -s "%BASE%/simulation/lakes/LAKE-001"
echo.
echo.

REM ==================================================
REM 4. CURRENT READING
REM ==================================================

echo [4/10] Testing current reading preview...
curl.exe -s "%BASE%/simulation/lakes/LAKE-001/current-reading"
echo.
echo.

REM ==================================================
REM 5. BEHAVIOR CONFIG
REM ==================================================

echo [5/10] Checking initial behavior configuration...
curl.exe -s "%BASE%/simulation/behaviors"
echo.
echo.

REM ==================================================
REM 6. MISSING READINGS
REM ==================================================

echo [6/10] Testing missing readings...
echo Enabling missing readings at 100 percent...

curl.exe -s -X POST "%BASE%/simulation/behaviors/control" ^
  -H "Content-Type: application/json" ^
  -d "{\"missing_readings_enabled\":true,\"missing_reading_rate\":1.0}"

echo.
echo Waiting 3 seconds for simulator...
timeout /t 3 /nobreak >nul

echo.
echo Checking simulator logs for dropped readings...
docker compose logs --tail=30 simulator | findstr /C:"[DROPPED]"

echo.
echo.

REM ==================================================
REM 7. DUPLICATES
REM ==================================================

echo [7/10] Testing duplicate readings...
echo.

curl.exe -s -X POST "%BASE%/simulation/behaviors/control" ^
  -H "Content-Type: application/json" ^
  -d "{\"missing_readings_enabled\":false,\"duplicate_readings_enabled\":true,\"duplicate_reading_rate\":1.0}"

echo.
echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo.
echo Checking simulator logs for duplicates...
docker compose logs --tail=50 simulator | findstr /C:"[DUPLICATE]"

echo.
echo.

REM ==================================================
REM 8. MALFORMED PAYLOADS
REM ==================================================

echo [8/10] Testing malformed payloads...
echo.

curl.exe -s -X POST "%BASE%/simulation/behaviors/control" ^
  -H "Content-Type: application/json" ^
  -d "{\"duplicate_readings_enabled\":false,\"malformed_payloads_enabled\":true,\"malformed_payload_rate\":1.0}"

echo.
echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo.
echo Checking simulator logs...
docker compose logs --tail=50 simulator | findstr /C:"[MALFORMED]"

echo.
echo Checking backend for 422 responses...
docker compose logs --tail=50 backend | findstr /C:"422"

echo.
echo.

REM ==================================================
REM 9. OUT OF ORDER + DELAYED + ANOMALIES
REM ==================================================

echo [9/10] Testing out-of-order events...
echo.

curl.exe -s -X POST "%BASE%/simulation/behaviors/control" ^
  -H "Content-Type: application/json" ^
  -d "{\"malformed_payloads_enabled\":false,\"out_of_order_enabled\":true,\"out_of_order_rate\":1.0}"

echo.
echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo.
echo Checking logs...
docker compose logs --tail=50 simulator | findstr /C:"[OUT-OF-ORDER]"

echo.
echo.
echo Testing delayed events...

curl.exe -s -X POST "%BASE%/simulation/behaviors/control" ^
  -H "Content-Type: application/json" ^
  -d "{\"out_of_order_enabled\":false,\"delayed_events_enabled\":true,\"delayed_event_rate\":1.0}"

echo.
echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo.
echo Checking logs...
docker compose logs --tail=50 simulator | findstr /C:"[DELAYED]"

echo.
echo.
echo Testing anomalies...

curl.exe -s -X POST "%BASE%/simulation/behaviors/control" ^
  -H "Content-Type: application/json" ^
  -d "{\"delayed_events_enabled\":false,\"anomalies_enabled\":true,\"anomaly_rate\":1.0}"

echo.
echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo.
echo Checking logs...
docker compose logs --tail=50 simulator | findstr /C:"[ANOMALY]"

echo.
echo.

REM ==================================================
REM 10. BACKEND CONNECTIVITY
REM ==================================================

echo [10/10] Testing backend connectivity...
echo.

echo Sensor data:
curl.exe -s "%BACKEND%/sensors/SENSOR-001/data"
echo.
echo.

echo Sensor status:
curl.exe -s "%BACKEND%/sensors/SENSOR-001/status"
echo.
echo.

REM ==================================================
REM RESTORE EVERYTHING
REM ==================================================

echo.
echo ==========================================
echo       RESTORING NORMAL CONFIGURATION
echo ==========================================
echo.

echo Disabling all data-quality behaviors...

curl.exe -s -X POST "%BASE%/simulation/behaviors/control" ^
  -H "Content-Type: application/json" ^
  -d "{\"missing_readings_enabled\":false,\"duplicate_readings_enabled\":false,\"malformed_payloads_enabled\":false,\"out_of_order_enabled\":false,\"delayed_events_enabled\":false,\"anomalies_enabled\":false,\"missing_reading_rate\":0.05,\"duplicate_reading_rate\":0.02,\"malformed_payload_rate\":0.02,\"out_of_order_rate\":0.02,\"delayed_event_rate\":0.02,\"anomaly_rate\":0.02}"

echo.
echo.

echo Resetting LAKE-001 stress level to 0...

curl.exe -s -X POST "%BASE%/simulation/lakes/LAKE-001/control" ^
  -H "Content-Type: application/json" ^
  -d "{\"stress_level\":0}"

echo.
echo.

REM ==================================================
REM FINAL CHECK
REM ==================================================

echo ==========================================
echo       FINAL CONFIGURATION CHECK
echo ==========================================
echo.

echo Data-quality configuration:
curl.exe -s "%BASE%/simulation/behaviors"

echo.
echo.

echo LAKE-001 configuration:
curl.exe -s "%BASE%/simulation/lakes/LAKE-001"

echo.
echo.

echo ==========================================
echo          TEST COMPLETE
echo ==========================================
echo.

pause