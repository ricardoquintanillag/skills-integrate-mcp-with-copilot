"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, selectinload, sessionmaker

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

DATABASE_URL = f"sqlite:///{current_dir / 'activities.db'}"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text())
    schedule: Mapped[str] = mapped_column(String(255))
    max_participants: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="active")

    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="activity",
        cascade="all, delete-orphan",
    )


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("activity_id", "student_id", name="uq_enrollment_activity_student"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))

    activity: Mapped[Activity] = relationship(back_populates="enrollments")
    student: Mapped[Student] = relationship(back_populates="enrollments")

SEED_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


def get_or_create_student(db: Session, email: str) -> Student:
    student = db.scalar(select(Student).where(Student.email == email))
    if student:
        return student

    student = Student(email=email)
    db.add(student)
    db.flush()
    return student


def seed_database(db: Session) -> None:
    existing = db.scalar(select(func.count(Activity.id)))
    if existing and existing > 0:
        return

    for name, details in SEED_ACTIVITIES.items():
        activity = Activity(
            name=name,
            description=details["description"],
            schedule=details["schedule"],
            max_participants=details["max_participants"],
            status="active",
        )
        db.add(activity)
        db.flush()

        for email in details["participants"]:
            student = get_or_create_student(db, email)
            db.add(Enrollment(activity_id=activity.id, student_id=student.id))

    db.commit()


def serialize_activity(activity: Activity) -> dict:
    participants = sorted(enrollment.student.email for enrollment in activity.enrollments)
    return {
        "description": activity.description,
        "schedule": activity.schedule,
        "max_participants": activity.max_participants,
        "status": activity.status,
        "participants": participants,
    }


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_database(db)


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    with SessionLocal() as db:
        query = (
            select(Activity)
            .options(selectinload(Activity.enrollments).selectinload(Enrollment.student))
            .order_by(Activity.name)
        )
        all_activities = db.scalars(query).all()
        return {activity.name: serialize_activity(activity) for activity in all_activities}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    with SessionLocal() as db:
        activity = db.scalar(
            select(Activity)
            .options(selectinload(Activity.enrollments).selectinload(Enrollment.student))
            .where(Activity.name == activity_name)
        )

        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        if activity.status != "active":
            raise HTTPException(status_code=400, detail="Activity is inactive")

        existing_signup = db.scalar(
            select(Enrollment)
            .join(Student)
            .where(Enrollment.activity_id == activity.id, Student.email == email)
        )
        if existing_signup:
            raise HTTPException(status_code=400, detail="Student is already signed up")

        if len(activity.enrollments) >= activity.max_participants:
            raise HTTPException(status_code=400, detail="Activity is full")

        student = get_or_create_student(db, email)
        db.add(Enrollment(activity_id=activity.id, student_id=student.id))
        db.commit()
        return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    with SessionLocal() as db:
        activity = db.scalar(select(Activity).where(Activity.name == activity_name))
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        enrollment = db.scalar(
            select(Enrollment)
            .join(Student)
            .where(Enrollment.activity_id == activity.id, Student.email == email)
        )
        if not enrollment:
            raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

        db.delete(enrollment)
        db.commit()
        return {"message": f"Unregistered {email} from {activity_name}"}
