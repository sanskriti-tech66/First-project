import asyncio
from sqlalchemy import select, func
from database.db import engine, Base, AsyncSessionLocal
from database.models import FAQ

FAQS = [
    {"question": "How do I return a product?", "answer": "You can return any product within 30 days of receipt. Please visit our Returns portal to generate a shipping label."},
    {"question": "What is your shipping policy?", "answer": "We offer free standard shipping on orders over $50. Expedited shipping is available at checkout."},
    {"question": "How long does shipping take?", "answer": "Standard shipping typically takes 3-5 business days. Expedited shipping takes 1-2 business days."},
    {"question": "Can I change my shipping address?", "answer": "Address changes can only be made within 1 hour of placing the order. Please contact support immediately."},
    {"question": "Do you ship internationally?", "answer": "Currently, we only ship within the United States and Canada."},
    {"question": "How do I track my order?", "answer": "Once your order ships, you will receive an email with a tracking number and a link to track your package."},
    {"question": "What payment methods do you accept?", "answer": "We accept Visa, MasterCard, American Express, PayPal, and Apple Pay."},
    {"question": "Why was my credit card declined?", "answer": "Declines are usually due to an incorrect billing address or insufficient funds. Please check with your bank or try another card."},
    {"question": "How do I reset my password?", "answer": "Click 'Forgot Password' on the login page. We will email you a link to securely reset your password."},
    {"question": "How do I delete my account?", "answer": "To permanently delete your account and data, please go to Account Settings > Privacy > Delete Account."},
    {"question": "My item arrived damaged.", "answer": "We apologize for the inconvenience! Please email us a photo of the damaged item within 48 hours, and we will ship a replacement."},
    {"question": "Are your products cruelty-free?", "answer": "Yes, all of our products are 100% cruelty-free and never tested on animals."},
    {"question": "Do you offer a warranty?", "answer": "Yes, all electronics come with a 1-year manufacturer's warranty covering defects."},
    {"question": "How do I contact technical support?", "answer": "You can reach technical support by emailing tech@example.com or calling 1-800-555-TECH."},
    {"question": "Do you offer gift cards?", "answer": "Yes! Digital gift cards are available in amounts ranging from $10 to $200 on our website."}
]

async def seed_database():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Seeding FAQs...")
    async with AsyncSessionLocal() as session:
        try:
            # Check if FAQs already exist
            existing_count = await session.execute(select(func.count(FAQ.id)))
            count = existing_count.scalar()
            
            if count > 0:
                print(f"Database already has {count} FAQs. Skipping seed.")
                return
            
            for faq_data in FAQS:
                faq = FAQ(question=faq_data["question"], answer=faq_data["answer"])
                session.add(faq)
            await session.commit()
            print("Database seeding complete!")
        except Exception as e:
            await session.rollback()
            print(f"Error seeding database: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(seed_database())