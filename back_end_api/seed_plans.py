#!/usr/bin/env python3
"""
Script to seed the database with initial plan data.
Run this after running migrations to populate the plans table.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import SessionLocal, engine
from app.models.plan import Plan

def seed_plans():
    """Insert initial plans into the database."""

    # Create session
    session = SessionLocal()

    try:
        # Check if plans already exist
        existing_plans = session.query(Plan).count()
        if existing_plans > 0:
            print(f"Plans already exist ({existing_plans} found). Skipping seed.")
            return

        # Define initial plans
        plans_data = [
            {
                "name": "Free",
                "slug": "free",
                "price_cents": 0,
                "currency": "USD",
                "max_posts_per_day": 2,
                "description": "Perfect for trying out our AI writing assistant. Create up to 2 posts per day."
            },
            {
                "name": "Pro Monthly",
                "slug": "pro-monthly",
                "price_cents": 990,  # $9.90
                "currency": "USD",
                "max_posts_per_day": 50,
                "description": "Ideal for content creators and small businesses. Create up to 50 posts per day with advanced AI features."
            },
            {
                "name": "Pro Yearly",
                "slug": "pro-yearly",
                "price_cents": 9900,  # $99.00 (save ~17%)
                "currency": "USD",
                "max_posts_per_day": 50,
                "description": "Best value for serious content creators. Annual subscription with all Pro features and 50 posts per day."
            },
            {
                "name": "Enterprise",
                "slug": "enterprise",
                "price_cents": 29900,  # $299.00
                "currency": "USD",
                "max_posts_per_day": 500,
                "description": "For large teams and agencies. Unlimited posts, priority support, and custom integrations."
            }
        ]

        # Create plan objects
        plans = []
        for plan_data in plans_data:
            plan = Plan(**plan_data)
            plans.append(plan)
            session.add(plan)

        # Commit the transaction
        session.commit()

        print(f"Successfully seeded {len(plans)} plans:")
        for plan in plans:
            print(f"  - {plan.name} ({plan.slug}): {plan.price_cents // 100}.{plan.price_cents % 100:02d} {plan.currency} - {plan.max_posts_per_day} posts/day")

    except Exception as e:
        session.rollback()
        print(f"Error seeding plans: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_plans()