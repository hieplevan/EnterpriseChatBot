from backend.app.db.session import engine, Base, SessionLocal
from backend.app.db.models import User, DocumentRecord


def init_database():
    """Khoi tao cac bang du lieu va tao san cac User Doanh nghiep mau."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Kiem tra va seed users mau
        existing_users = db.query(User).count()
        if existing_users == 0:
            seed_users = [
                User(
                    username="admin",
                    full_name="System Administrator",
                    role="ADMIN",
                    department="ALL",
                ),
                User(
                    username="legal_counsel",
                    full_name="Truong Phong Phap Che (Legal)",
                    role="LEGAL",
                    department="LEGAL",
                ),
                User(
                    username="hr_manager",
                    full_name="Truong Phong Nhan Su (HR)",
                    role="HR",
                    department="HR",
                ),
                User(
                    username="finance_lead",
                    full_name="Ke Toan Truong (Finance)",
                    role="FINANCE",
                    department="FINANCE",
                ),
                User(
                    username="general_staff",
                    full_name="Nhan Vien Noi Bo (Staff)",
                    role="EMPLOYEE",
                    department="GENERAL",
                ),
            ]
            db.add_all(seed_users)
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
    print("Database initialized successfully.")
