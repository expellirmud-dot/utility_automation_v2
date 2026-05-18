Start-Process powershell -ArgumentList '-NoExit','-Command','cd D:\utility_automation_v2_light; $env:PYTHONPATH="."; python -m uvicorn src.ui.ops_overview_api:app --host 127.0.0.1 --port 8000 --reload'

Start-Process powershell -ArgumentList '-NoExit','-Command','cd D:\utility_automation_v2_light\frontend\operator-observatory; npm run dev'