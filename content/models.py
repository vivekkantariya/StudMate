from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.db.models import F

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

    def followers_count(self):
        return self.user.followers.count()
    
    def following_count(self):
        return self.user.following.count()

# Signal to automatically create Profile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    Profile.objects.get_or_create(user=instance)
    instance.profile.save()

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
        indexes = [
            models.Index(fields=['follower', 'created_at']),
            models.Index(fields=['following', 'created_at']),
        ]
    
    def clean(self):
        if self.follower == self.following:
            raise ValidationError("Users cannot follow themselves.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmark')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user','content')
        
    def __str__(self):
        return f"{self.user.username} bookmarked {self.content.name}"

# models.py
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='ratings')
    score = models.PositiveSmallIntegerField()  # 1 to 5

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'content')  # One rating per user per content

    def __str__(self):
        return f"{self.user.username} rated {self.content.name} as {self.score}"

# models.py
class ReportReason(models.TextChoices):
    INAPPROPRIATE = "inappropriate", "Inappropriate Content"
    SPAM = "spam", "Spam or Misleading"
    COPYRIGHT = "copyright", "Copyright Violation"
    OTHER = "other", "Other"

class ContentReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name="reports")
    reason = models.CharField(max_length=50, choices=ReportReason.choices)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        unique_together = ('reporter', 'content')  # One report per user per content

    def __str__(self):
        return f"Report by {self.reporter.username} on {self.content.name} - {self.reason}"

class Download(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
