import os
import shutil
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Hostel.settings')
django.setup()

from app2.models import MarketplaceItem, LostItem, Form, EventGalleryImage
from django.core.files import File

brain_dir = r"C:\Users\kesha\.gemini\antigravity\brain\7ef1bafd-8dc2-48b2-8be8-6ff515a602d5"
media_dir = r"e:\HMS SOLO\Solo-HMS_Updated-Django\media"

if not os.path.exists(media_dir):
    os.makedirs(media_dir)

def attach_image(obj, field_name, source_filename, dest_subpath):
    source_path = os.path.join(brain_dir, source_filename)
    if os.path.exists(source_path):
        with open(source_path, 'rb') as f:
            getattr(obj, field_name).save(dest_subpath, File(f), save=True)

# Attach to Marketplace
maths = MarketplaceItem.objects.filter(title__icontains='Mathematics').first()
if maths: attach_image(maths, 'image', 'maths_book_1781511145530.png', 'maths_book.png')

fridge = MarketplaceItem.objects.filter(title__icontains='Fridge').first()
if fridge: attach_image(fridge, 'image', 'mini_fridge_1781511158991.png', 'mini_fridge.png')

calc = MarketplaceItem.objects.filter(title__icontains='Calculator').first()
if calc: attach_image(calc, 'image', 'calculator_1781511171605.png', 'calculator.png')

# Attach to Events (Forms)
tech = Form.objects.filter(name__icontains='Symposium').first()
if tech: attach_image(tech, 'poster', 'tech_poster_1781511183048.png', 'tech_poster.png')

sports = Form.objects.filter(name__icontains='Sports').first()
if sports: attach_image(sports, 'poster', 'sports_poster_1781511216060.png', 'sports_poster.png')

hack = Form.objects.filter(name__icontains='Hackathon').first()
if hack: 
    attach_image(hack, 'poster', 'hackathon_poster_1781511229854.png', 'hackathon_poster.png')
    # Create Gallery Images for Hackathon
    hack.is_archived = True
    hack.save()
    if not EventGalleryImage.objects.filter(event=hack).exists():
        g1 = EventGalleryImage(event=hack, caption='Students collaborating')
        attach_image(g1, 'image', 'gallery_1_1781511241833.png', 'gallery_1.png')
        g2 = EventGalleryImage(event=hack, caption='Tech Talk')
        attach_image(g2, 'image', 'gallery_2_1781511268256.png', 'gallery_2.png')

print("Images seeded successfully.")
