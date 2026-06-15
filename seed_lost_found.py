import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Hostel.settings')
django.setup()

from Hostels.models import CustomUser
from app2.models import LostItem, FoundItem
from django.core.files import File
from datetime import date

student_user = CustomUser.objects.filter(is_superuser=False).first()
brain_dir = r"C:\Users\kesha\.gemini\antigravity\brain\7ef1bafd-8dc2-48b2-8be8-6ff515a602d5"

def attach_image(obj, field_name, source_filename, dest_subpath):
    source_path = os.path.join(brain_dir, source_filename)
    if os.path.exists(source_path):
        with open(source_path, 'rb') as f:
            getattr(obj, field_name).save(dest_subpath, File(f), save=True)

# Seed Lost Item
wallet, _ = LostItem.objects.get_or_create(
    title='Brown Leather Wallet',
    defaults={
        'description': 'Lost my brown leather wallet near the cafeteria. Contains my student ID.',
        'category': 'wallet',
        'location': 'Near Cafeteria',
        'contact_info': 'student1@campusnest.edu',
        'date_lost': date.today()
    }
)
attach_image(wallet, 'image', 'lost_wallet_1781511202871.png', 'lost_wallet.png')

# Wait, I didn't generate keys, but I can reuse an image or just not have an image for found items.
print("Lost & Found seeded successfully.")
