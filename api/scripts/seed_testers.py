"""Seed tester accounts across Free, Basic, Premium, and Tester plans.

Usage:
    python scripts/seed_testers.py [--test-db] [--db-url URL]
"""

import argparse
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.db.models import Plan, Subscription, User

TESTER_PLAN = {
    "id": "tester",
    "name": "Tester (Internal)",
    "price_birr": 0.0,
    "period_days": 365,
    "questions_per_day": 999,
    "monthly_voice_chars": 100000,
    "max_upload_chars": 900000,
    "cloud_stt": True,
}

TESTERS = [
    {
        "id": "tester-free-1",
        "phone": "+251911000001",
        "name": "Abebe Bikila",
        "grade": 9,
        "preferred_lang": "am",
        "plan_id": "free",
        "free_questions_left": 5,
    },
    {
        "id": "tester-free-2",
        "phone": "+251911000002",
        "name": "Sara Haile",
        "grade": 10,
        "preferred_lang": "en",
        "plan_id": "free",
        "free_questions_left": 2,
    },
    {
        "id": "tester-free-3",
        "phone": "+251911000003",
        "name": "Dawit Kebede",
        "grade": 11,
        "preferred_lang": "am",
        "plan_id": "free",
        "free_questions_left": 0,
    },
    {
        "id": "tester-basic-1",
        "phone": "+251911000004",
        "name": "Tigist Assefa",
        "grade": 9,
        "preferred_lang": "am",
        "plan_id": "basic",
        "free_questions_left": 0,
    },
    {
        "id": "tester-basic-2",
        "phone": "+251911000005",
        "name": "Yohannes Girma",
        "grade": 11,
        "preferred_lang": "en",
        "plan_id": "basic",
        "free_questions_left": 0,
    },
    {
        "id": "tester-basic-3",
        "phone": "+251911000006",
        "name": "Bethlehem Tadesse",
        "grade": 12,
        "preferred_lang": "am",
        "plan_id": "basic",
        "free_questions_left": 0,
    },
    {
        "id": "tester-premium-1",
        "phone": "+251911000007",
        "name": "Kenenisa Bekele",
        "grade": 10,
        "preferred_lang": "am",
        "plan_id": "premium",
        "free_questions_left": 0,
    },
    {
        "id": "tester-premium-2",
        "phone": "+251911000008",
        "name": "Derartu Tulu",
        "grade": 12,
        "preferred_lang": "en",
        "plan_id": "premium",
        "free_questions_left": 0,
    },
    {
        "id": "tester-tester-1",
        "phone": "+251911000009",
        "name": "Haile Gebrselassie",
        "grade": 12,
        "preferred_lang": "am",
        "plan_id": "tester",
        "free_questions_left": 5,
    },
    {
        "id": "tester-tester-2",
        "phone": "+251911000010",
        "name": "Meseret Defar",
        "grade": 11,
        "preferred_lang": "en",
        "plan_id": "tester",
        "free_questions_left": 5,
    },
]


def seed_testers(database_url: str) -> None:
    """Idempotently seed the tester plan and 10 tester accounts into the given database."""
    engine = create_engine(database_url)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        # 1. Ensure 'tester' plan exists
        tester_plan = session.get(Plan, TESTER_PLAN["id"])
        if not tester_plan:
            tester_plan = Plan(**TESTER_PLAN)
            session.add(tester_plan)
            session.commit()
            print("  Created 'tester' plan tier.")

        now = datetime.now(UTC)
        seeded_count = 0

        # 2. Seed testers
        for data in TESTERS:
            user = session.get(User, data["id"])
            if not user:
                user = User(
                    id=data["id"],
                    phone=data["phone"],
                    name=data["name"],
                    grade=data["grade"],
                    preferred_lang=data["preferred_lang"],
                    plan_id=data["plan_id"],
                    free_questions_left=data["free_questions_left"],
                    created_at=now,
                )
                session.add(user)
                session.flush()
                seeded_count += 1
            else:
                user.phone = data["phone"]
                user.name = data["name"]
                user.grade = data["grade"]
                user.preferred_lang = data["preferred_lang"]
                user.plan_id = data["plan_id"]
                user.free_questions_left = data["free_questions_left"]

            # Add active subscription if on paid or tester tier
            if data["plan_id"] in {"basic", "premium", "tester"}:
                sub = (
                    session.query(Subscription)
                    .filter(Subscription.user_id == user.id)
                    .first()
                )
                if not sub:
                    sub = Subscription(
                        user_id=user.id,
                        plan_id=data["plan_id"],
                        starts_at=now,
                        ends_at=now + timedelta(days=365),
                        payment_id="seed_test_sub",
                    )
                    session.add(sub)

        session.commit()
        print(f"  Successfully seeded/updated {len(TESTERS)} testers ({seeded_count} new).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed test accounts for Tibeb AI.")
    parser.add_argument("--test-db", action="store_true", help="Seed into TEST_DATABASE_URL")
    parser.add_argument("--db-url", type=str, default=None, help="Explicit database URL")
    args = parser.parse_args()

    settings = get_settings()
    if args.db_url:
        db_url = args.db_url
    elif args.test_db:
        db_url = settings.TEST_DATABASE_URL
    else:
        db_url = settings.DATABASE_URL

    print(f"Seeding testers into database: {db_url.split('@')[-1] if '@' in db_url else db_url}...")
    seed_testers(db_url)


if __name__ == "__main__":
    main()
