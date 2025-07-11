from django.db import models
from django.contrib.auth.models import User
from django.db import models

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