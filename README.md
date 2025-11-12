# Environmental Monitoring MVP

Minimal Flask web application for environmental monitoring workflows in a food manufacturing plant.

## Features

- Flask + SQLite single instance deployment
- Master data management for sites, zones, and sampling points
- Plan creation with automatic weekly/monthly schedule generation
- Sample registration linked to schedules
- Test order management and result entry with automated pass/fail judgement
- Dashboard with monthly summary, trend chart endpoint, and CSV export

## Getting Started

1. Create a virtual environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Initialize the application database:
   ```bash
   flask --app app run  # first start will create instance path
   curl http://localhost:5000/init  # seeds default admin and sample data
   ```
3. Login with `admin@example.com` / `admin` and begin managing data.

For development convenience run `python seed.py` to seed base data.

## Testing

Run unit tests (requires dependencies):
```bash
pytest
```
