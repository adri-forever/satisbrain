.\.venv\Scripts\Activate.ps1

Set-Item env:FLASK_APP 'flasker.py'
Set-Item env:FLASK_ENV 'development'

flask run -h 0.0.0.0 -p 8080