import os
import django
from datetime import date, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Hostel.settings')
django.setup()

from Hostels.models import CustomUser
from app2.models import DiscussionMessage, MessMenu, TodayMenu, MessRules, Form, ClaimRequest, MarketplaceItem

# Create some users if none exist, or get the first superuser
admin_user = CustomUser.objects.filter(is_superuser=True).first()
if not admin_user:
    admin_user = CustomUser.objects.create_superuser('admin@campusnest.edu', 'adminpassword123', first_name='Admin', last_name='User')

student_user = CustomUser.objects.filter(is_superuser=False).first()
if not student_user:
    student_user = CustomUser.objects.create_user('student1@campusnest.edu', 'studentpassword123', first_name='John', last_name='Doe')

# Seed Marketplace Items
if not MarketplaceItem.objects.exists():
    MarketplaceItem.objects.create(
        seller=student_user,
        title='Used Engineering Mathematics Vol 1',
        description='Barely used, in great condition. No highlighting.',
        price=350.00,
        category='Books',
        condition='Like New'
    )
    MarketplaceItem.objects.create(
        seller=student_user,
        title='Mini Fridge 50L',
        description='Perfect for dorm rooms. Selling because I am graduating.',
        price=2500.00,
        category='Electronics',
        condition='Used'
    )
    MarketplaceItem.objects.create(
        seller=student_user,
        title='Scientific Calculator FX-991EX',
        description='Fully functional, battery replaced last month.',
        price=800.00,
        category='Electronics',
        condition='Used'
    )
    print("Marketplace seeded.")

# Seed Events (Form)
if not Form.objects.exists():
    Form.objects.create(
        name='Annual Tech Symposium',
        description='Join us for a 2-day tech extravaganza featuring guest lectures from industry leaders.',
        date=date.today() + timedelta(days=5),
        time='09:00:00',
        venue='Main Auditorium',
        organizer='Tech Club'
    )
    Form.objects.create(
        name='Inter-Hostel Sports Meet',
        description='Cheer for your hostel! Football, Basketball, and Athletics.',
        date=date.today() + timedelta(days=10),
        time='16:00:00',
        venue='Campus Sports Ground',
        organizer='Sports Council'
    )
    Form.objects.create(
        name='Hackathon 2026',
        description='48 hours of non-stop coding. Prizes up to 50k!',
        date=date.today() + timedelta(days=15),
        time='18:00:00',
        venue='Computer Center Library',
        organizer='Google Developer Student Club'
    )
    print("Events seeded.")

# Seed Discussions
if not DiscussionMessage.objects.exists():
    DiscussionMessage.objects.create(
        user=student_user,
        message='Does anyone know if the library is open 24/7 during the mid-sem exams next week?'
    )
    DiscussionMessage.objects.create(
        user=admin_user,
        message='Yes, the main library reading rooms will remain open 24/7 starting this Monday.'
    )
    DiscussionMessage.objects.create(
        user=student_user,
        message='Awesome, thanks!'
    )
    print("Discussions seeded.")

# Seed Mess Menu
if not MessMenu.objects.exists():
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    meals = ['Breakfast', 'Lunch', 'Snacks', 'Dinner']
    for day in days:
        MessMenu.objects.create(day=day, meal_type='Breakfast', menu='Aloo Paratha, Curd, Tea/Coffee, Banana')
        MessMenu.objects.create(day=day, meal_type='Lunch', menu='Rajma Chawal, Roti, Seasonal Veg, Salad, Papad')
        MessMenu.objects.create(day=day, meal_type='Snacks', menu='Samosa, Green Chutney, Tea')
        MessMenu.objects.create(day=day, meal_type='Dinner', menu='Paneer Butter Masala, Dal Tadka, Jeera Rice, Roti, Gulab Jamun')
    print("Mess Menu seeded.")

print("All seeds applied successfully.")
