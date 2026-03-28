from django.contrib.auth.models import AbstractUser
# models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        # For CampusNest institutional accounts, default is False until OTP verification
        if 'is_superuser' not in extra_fields:
            extra_fields.setdefault('is_active', False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('roll_number', 'ADMIN')  # Optional default
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None  # Remove username field
    email = models.EmailField(unique=True)
    roll_number = models.CharField(max_length=20, blank=True, null=True,unique=True)  # Optional field

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name','roll_number']  # roll_number is optional

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    contact_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    bio = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"

class Hostel(models.Model):
    name = models.CharField(max_length=100)
    total_floors = models.PositiveIntegerField()
    main_image = models.ImageField(upload_to='hostels/')
    features = models.TextField(help_text="Comma-separated list of features")
    
    def feature_list(self):
        return [f.strip() for f in self.features.split(',')]

    def __str__(self):
        return self.name

class Room(models.Model):
    ROOM_TYPES = (
        ('four', '4-Sharing'),
        ('double', 'Double Sharing'),
        ('single', 'Single Seater')
    )
    AC_TYPES = (
        ('ac', 'AC'),
        ('non_ac', 'Non-AC'),
    )
    
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='rooms')
    floor = models.PositiveIntegerField()
    room_number = models.CharField(max_length=10)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    ac_type = models.CharField(max_length=10, choices=AC_TYPES)
    total_beds = models.PositiveIntegerField()
    occupied_beds = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amenities = models.TextField()

    @property
    def beds_left(self):
        return self.total_beds - self.occupied_beds

    def __str__(self):
        return f"{self.hostel.name} - Room {self.room_number}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['hostel', 'room_number'],
                name='unique_room_per_hostel'
            )
        ]

class Allocation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='allocations')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='allocations')
    allocation_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.room.room_number}"
    
    class Meta:
        constraints = [
            # Allow only one active (pending/confirmed) allocation per user
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(status__in=['pending', 'approved', 'confirmed']),
                name='unique_active_allocation_per_user'
            )
        ]
    
class RoomChangeRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='room_change_requests')
    current_allocation = models.ForeignKey(Allocation, on_delete=models.CASCADE, related_name='current_room_changes')
    requested_room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='requested_room_changes')
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - Change to {self.requested_room.room_number}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'status'],
                condition=models.Q(status='pending'),
                name='unique_pending_room_change_per_user'
            )
        ]
    
# models.py
class FeePayment(models.Model):
    transaction_id = models.CharField(
        max_length=100, 
        unique=True,
        db_index=True  # Add database index
    )
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments')
    allocation = models.ForeignKey(Allocation, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending')
    receipt = models.FileField(upload_to='payment_receipts/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.amount}"
    
    
    
    
# models.py
class ComplaintMaintenance(models.Model):
    
    REQUEST_TYPES = (
        ('complaint', 'Complaint'),
        ('maintenance', 'Maintenance'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    room_number = models.CharField(max_length=10)
    category = models.CharField(max_length=50)
    details = models.TextField()
    status = models.CharField(max_length=20, default='pending', choices=(('pending', 'Pending'), ('resolved', 'Resolved')))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.request_type}"

class Feedback(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    environment_rating = models.CharField(max_length=20)
    service_rating = models.IntegerField()
    comments = models.TextField()
    hostel = models.CharField(max_length=50)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.user.email if self.user else 'anonymous'}"

class EmailOTP(models.Model):
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.email} - {'Verified' if self.is_verified else 'Pending'}"

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not instance.is_staff and not instance.is_superuser:
        StudentProfile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if not instance.is_staff and not instance.is_superuser:
        if hasattr(instance, 'student_profile'):
            instance.student_profile.save()
