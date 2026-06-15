from django.db import models
from django.utils import timezone

class Club(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    logo = models.ImageField(upload_to='clubs/logos/', blank=True, null=True)
    leads = models.ManyToManyField('Hostels.CustomUser', related_name='managed_clubs', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Form(models.Model):
    name = models.CharField(max_length=255)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='events', blank=True, null=True)
    date = models.DateField()
    time = models.TimeField()
    venue = models.CharField(max_length=255)
    description = models.TextField(help_text="Event description", blank=True, null=True)
    organizer = models.CharField(max_length=255, help_text="Legacy organizer name")
    poster = models.ImageField(upload_to='events/posters/', blank=True, null=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class EventGalleryImage(models.Model):
    event = models.ForeignKey(Form, related_name='gallery_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='events/gallery/')
    caption = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Gallery image for {self.event.name}"

class MessMenu(models.Model):
    DAY_CHOICES = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
        ("Sunday", "Sunday"),
    ]
    MEAL_TYPE_CHOICES = [
        ("Breakfast", "Breakfast"),
        ("Lunch", "Lunch"),
        ("Snacks", "Snacks"),
        ("Dinner", "Dinner"),
        ("Additional Meal", "Additional Meal"),
    ]
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    menu = models.TextField()

    class Meta:
        unique_together = ['day', 'meal_type']
        ordering = ['day', 'meal_type']

    def __str__(self):
        return f"{self.day} - {self.meal_type}"

class TodayMenu(models.Model):
    day = models.CharField(max_length=20)
    meal_type = models.CharField(max_length=20)
    menu = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.day} - {self.meal_type}"

class MessRules(models.Model):
    rule = models.TextField()
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.rule[:50]

    class Meta:
        ordering = ['order']

class DiscussionMessage(models.Model):
    user = models.ForeignKey('Hostels.CustomUser', on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_notification = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.email}: {self.message[:30]}"

class Item(models.Model):
    CATEGORY_CHOICES = [
        ('keys', 'Keys'),
        ('phone', 'Phone'),
        ('bottle', 'Bottle'),
        ('wallet', 'Wallet'),
        ('bag', 'Bag'),
        ('documents', 'Documents'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    location = models.CharField(max_length=200)
    contact_info = models.CharField(max_length=200)
    image = models.ImageField(upload_to='lost_found/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_claimed = models.BooleanField(default=False)

    class Meta:
        abstract = True
        ordering = ['-created_at']

class LostItem(Item):
    date_lost = models.DateField()

    def __str__(self):
        return f"Lost: {self.title}"

    class Meta:
        ordering = ['-created_at']

class FoundItem(Item):
    date_found = models.DateField()

    def __str__(self):
        return f"Found: {self.title}"

    class Meta:
        ordering = ['-created_at']

class ClaimRequest(models.Model):
    item = models.ForeignKey(FoundItem, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Claim request for {self.item.title}"

    class Meta:
        ordering = ['-created_at']

class MarketplaceItem(models.Model):
    CONDITION_CHOICES = [
        ('New', 'Brand New'),
        ('Like New', 'Excellent / Like New'),
        ('Used', 'Good / Used'),
        ('Rough', 'Fair / Functional'),
    ]
    
    CATEGORY_CHOICES = [
        ('Books', 'Books & Study Material'),
        ('Electronics', 'Electronics & Gadgets'),
        ('Furniture', 'Hostel Furniture'),
        ('Clothing', 'Clothing & Accessories'),
        ('Other', 'Miscellaneous'),
    ]

    seller = models.ForeignKey('Hostels.CustomUser', on_delete=models.CASCADE, related_name='listed_items')
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    image = models.ImageField(upload_to='marketplace/', blank=True, null=True)
    is_sold = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - ₹{self.price}"

    class Meta:
        ordering = ['-created_at']

# WebSocket Broadcast Signal
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=DiscussionMessage)
def broadcast_discussion_message(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'discussion_global',
            {
                'type': 'chat_message',
                'message': instance.message,
                'user': instance.user.get_full_name() or instance.user.email,
                'user_id': instance.user.id,
                'is_notification': instance.is_notification,
            }
        )