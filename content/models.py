from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class ContentType(models.TextChoices):
    PRACTICAL = "prac", "Practical"
    NOTE = "note", "Notes"
    ASSIGNMENT = "ass", "Assignment"
    PROJECT = "project", "Project"

class Content(models.Model):
    # the user which uploded the content 
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contents')           
    name = models.CharField(max_length=200)
    desc = models.TextField(verbose_name="Description")
    content_type = models.CharField(max_length=10, choices=ContentType.choices)
    date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Track updates
    tags = models.CharField(max_length=200, help_text="Comma-separated (3-5 tags)")
    file = models.FileField(upload_to='notes/', blank=True, null=True)
    is_public = models.BooleanField(default=True)
    download_count = models.PositiveIntegerField(default=0)

    # This will be updated based on actual ratings (e.g. from another model)
    rate = models.DecimalField(max_digits=2, decimal_places=1, default=0.0, editable=False)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['content_type', 'date']),
            models.Index(fields=['author', 'is_public']),
        ]
        
    def __str__(self):
        return self.name 

    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    institution = models.CharField(max_length=100, blank=True)
    course = models.CharField(max_length=100, blank=True)
    semester = models.PositiveSmallIntegerField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    reputation = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signal to automatically create Profile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    Profile.objects.get_or_create(user=instance)
    instance.profile.save()
    
class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmark')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user','content')
        
    def __str__(self):
        return f"{self.user.username} bookmarked {self.content.name}"


# ✅ 8. Rate Limits & Upload Quotas
# To reduce spam:

# Limit uploads per user per day
# ✅ 9. Watermarking / Fingerprinting (optional)
# To discourage reuploads and plagiarism:

# Add a unique watermark to documents on upload

# Embed user IDs invisibly (steganography / metadata)
