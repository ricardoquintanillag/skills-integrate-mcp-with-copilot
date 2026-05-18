# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Unregister students from activities
- Persist data in SQLite database
- Prevent duplicate signups and over-capacity signups
- Block signups on inactive activities

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student from an activity                               |

## Data Model

The application uses a relational SQLite model with three entities:

1. **Activities**:

   - Name
   - Description
   - Schedule
   - Status (`active` / `inactive`)
   - Maximum number of participants allowed
   - Enrollments

2. **Students**:

   - Email (unique)
   - Name (optional)

3. **Enrollments**:

   - Relationship between students and activities
   - Unique per `(activity, student)`

The app initializes the schema on startup and seeds sample data on first run.
