# Smart FitTrack

A simple full-stack workout and calorie tracker built with Flask and SQLite.

## Features
- Register / login (passwords hashed with Werkzeug)
- Add workouts: date, activity, duration (minutes), body weight (kg)
- Calories = MET × body weight (kg) × duration (hours)
- Dashboard: total workouts, total minutes, calories burned, average calories, chart
- Searchable history with delete
- Health check endpoint: `GET /api/health`

## Technologies
HTML5, CSS3, JavaScript, Python, Flask, SQLite, Werkzeug

## Run locally
```bash
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Project structure
```
Smart-FitTrack/
├── app.py
├── requirements.txt
├── README.md
├── static/style.css
└── templates/
    ├── login.html
    └── dashboard.html
```
