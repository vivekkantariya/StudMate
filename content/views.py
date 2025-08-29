from collections import Counter
import re
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q, Sum, Count, Avg
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.utils import timezone

from .forms import CustomUserForm, ContentForm, ProfileForm, ReportForm, ContentEditForm
from .models import Content, Bookmark, Rating, ContentReport, Download, Follow

from django.db.models import Avg
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# Home view
def home(request):
    search_query = request.GET.get('search', '')
    content_type = request.GET.get('content_type', '')
    sort_by = request.GET.get('sort_by', '-date')

    contents = Content.objects.filter(is_public=True)

    if search_query:
        contents = contents.filter(
            Q(name__icontains=search_query) |
            Q(desc__icontains=search_query) |
            Q(tags__icontains=search_query)
        )

    if content_type:
        contents = contents.filter(content_type=content_type)

    valid_sort_options = ['-date', 'date', '-rate', '-download_count', 'name']
    if sort_by not in valid_sort_options:
        sort_by = '-date'

    contents = contents.order_by(sort_by)

    user_bookmarked_ids = set()
    if request.user.is_authenticated:
        user_bookmarked_ids = set(
            Bookmark.objects.filter(user=request.user, content__in=contents)
            .values_list('content_id', flat=True)
        )

    for content in contents:
        content.is_bookmarked = content.id in user_bookmarked_ids

    paginator = Paginator(contents, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_resources = Content.objects.filter(is_public=True).count()
    active_users = User.objects.count()

    content_counts = {
        'total_resources': total_resources,
        'active_users': active_users,
        'note_count': Content.objects.filter(content_type='note', is_public=True).count(),
        'assignment_count': Content.objects.filter(content_type='ass', is_public=True).count(),
        'practical_count': Content.objects.filter(content_type='prac', is_public=True).count(),
        'project_count': Content.objects.filter(content_type='project', is_public=True).count(),
    }

    context = {
        'data': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        **content_counts,
    }

    return render(request, 'content/home.html', context)


# Registration
def register(request):
    if request.method == "POST":
        form = CustomUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserForm()

    return render(request, "registration/register.html", {"form": form})


def logout_view(request):
    django_logout(request)
    return redirect('home')


# Bookmark system
@login_required
def bookmark(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, content=content)

    if not created:
        bookmark.delete()

    return redirect(request.META.get('HTTP_REFERER', 'content_list'))


@login_required
def bookmarked_contents(request):
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('content')
    contents = [b.content for b in bookmarks]
    for c in contents:
        c.is_bookmarked = True
    return render(request, 'content/my_bookmarks.html', {'contents': contents})


# Content list view
def content_list(request):
    search_query = request.GET.get('search', '')
    content_type = request.GET.get('content_type', '')
    sort_by = request.GET.get('sort_by', '-date')

    contents = Content.objects.filter(is_public=True)

    if search_query:
        contents = contents.filter(
            Q(name__icontains=search_query) |
            Q(desc__icontains=search_query) |
            Q(tags__icontains=search_query)
        )

    if content_type:
        contents = contents.filter(content_type=content_type)

    valid_sort_options = ['-date', 'date', '-rate', '-download_count', 'name']
    if sort_by not in valid_sort_options:
        sort_by = '-date'

    contents = contents.order_by(sort_by)

    user_bookmarked_ids = set()
    if request.user.is_authenticated:
        user_bookmarked_ids = set(
            Bookmark.objects.filter(user=request.user, content__in=contents).values_list('content_id', flat=True)
        )

    for content in contents:
        content.is_bookmarked = content.id in user_bookmarked_ids

    paginator = Paginator(contents, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_resources = Content.objects.filter(is_public=True).count()
    active_users = User.objects.count()
    download_sum = Content.objects.filter(is_public=True).aggregate(total=Sum('download_count'))['total']
    total_downloads = download_sum if download_sum else 0

    content_counts = {
        'total_resources': total_resources,
        'note_count': Content.objects.filter(content_type='note', is_public=True).count(),
        'assignment_count': Content.objects.filter(content_type='ass', is_public=True).count(),
        'practical_count': Content.objects.filter(content_type='prac', is_public=True).count(),
        'project_count': Content.objects.filter(content_type='project', is_public=True).count(),
    }

    context = {
        'data': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'active_users': active_users,
        'total_downloads': total_downloads,
        **content_counts,
    }

    return render(request, 'content/home.html', context)


# Content detail
def content_detail(request, pk):
    item = get_object_or_404(Content, pk=pk)
    related_resources = Content.objects.filter(
        Q(content_type=item.content_type) |
        Q(tags__icontains=item.tags.split(',')[0] if item.tags else '')
    ).exclude(pk=item.pk).distinct()[:5]

    return render(request, 'content/content_detail.html', {
        'item': item,
        'related_resources': related_resources
    })


# Create content
def content_create(request):
    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES)
        if form.is_valid():
            content = form.save(commit=False)
            content.author = request.user
            content.save()
            return redirect('content_list')
    else:
        form = ContentForm()
    return render(request, 'content/content_create.html', {'form': form})


@login_required
def my_upload(request):
    data = Content.objects.filter(author=request.user)
    return render(request, 'content/myupload.html', {'data': data})


# Profile views with dynamic analytics
@login_required
def profile_view(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    profile = user_obj.profile
    uploads = Content.objects.filter(author=user_obj, is_public=True)
    bookmarks = Bookmark.objects.filter(user=user_obj).select_related('content')
    bookmarked_contents = [b.content for b in bookmarks if b.content.is_public]
    for c in bookmarked_contents:
        c.is_bookmarked = True

    # Check if current user is following this user
    is_following = False
    if request.user.is_authenticated and request.user != user_obj:
        is_following = Follow.objects.filter(
            follower=request.user, 
            following=user_obj
        ).exists()

    # Calculate dynamic analytics
    analytics = calculate_user_analytics(user_obj)

    context = {
        'profile': profile,
        'uploads': uploads,
        'bookmarks': bookmarked_contents,
        'is_following': is_following,
        'is_own_profile': request.user == user_obj,
        'followers_count': user_obj.followers.count(),
        'following_count': user_obj.following.count(),
        'analytics': analytics,
    }

    return render(request, 'profile/view.html', context)


def calculate_user_analytics(user_obj):
    """
    Calculate dynamic analytics for a user based on actual database data
    """
    # Get current date and 30 days ago for comparison
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    
    # Get user's content
    user_contents = Content.objects.filter(author=user_obj, is_public=True)
    
    # Total downloads for user's content
    total_downloads = user_contents.aggregate(
        total=Sum('download_count')
    )['total'] or 0
    
    # Downloads in last 30 days (if you want to track this, you'd need to modify Download model to track creation time)
    recent_downloads = Download.objects.filter(
        content__author=user_obj,
        timestamp__gte=thirty_days_ago
    ).count()
    
    # Calculate download growth percentage
    if total_downloads > 0:
        old_downloads = total_downloads - recent_downloads
        download_growth = ((recent_downloads / max(old_downloads, 1)) * 100) if old_downloads > 0 else 100
    else:
        download_growth = 0
    
    # Content upload count
    total_uploads = user_contents.count()
    recent_uploads = user_contents.filter(date__gte=thirty_days_ago).count()
    
    # Upload growth percentage
    if total_uploads > 0:
        old_uploads = total_uploads - recent_uploads
        upload_growth = ((recent_uploads / max(old_uploads, 1)) * 100) if old_uploads > 0 else 100
    else:
        upload_growth = 0
    
    # Followers data
    total_followers = user_obj.followers.count()
    recent_followers = Follow.objects.filter(
        following=user_obj,
        created_at__gte=thirty_days_ago
    ).count()
    
    # Follower growth percentage
    if total_followers > 0:
        old_followers = total_followers - recent_followers
        follower_growth = ((recent_followers / max(old_followers, 1)) * 100) if old_followers > 0 else 100
    else:
        follower_growth = 0
    
    # Average rating for user's content
    avg_rating = user_contents.aggregate(
        avg_rate=Avg('rate')
    )['avg_rate'] or 0
    
    # Engagement calculation (ratings + bookmarks for user's content)
    total_ratings = Rating.objects.filter(content__author=user_obj).count()
    total_bookmarks = Bookmark.objects.filter(content__author=user_obj).count()
    engagement_score = total_ratings + total_bookmarks
    
    # Calculate engagement percentage (this is a simplified calculation)
    if total_uploads > 0:
        engagement_rate = (engagement_score / (total_uploads * 2)) * 100  # Max 2 engagements per upload
        engagement_rate = min(engagement_rate, 100)  # Cap at 100%
    else:
        engagement_rate = 0
    
    # Recent engagement
    recent_ratings = Rating.objects.filter(
        content__author=user_obj,
        created_at__gte=thirty_days_ago
    ).count()
    recent_bookmarks = Bookmark.objects.filter(
        content__author=user_obj,
        created_at__gte=thirty_days_ago
    ).count()
    recent_engagement = recent_ratings + recent_bookmarks
    
    # Engagement growth
    if engagement_score > 0:
        old_engagement = engagement_score - recent_engagement
        engagement_growth = ((recent_engagement / max(old_engagement, 1)) * 100) if old_engagement > 0 else 100
    else:
        engagement_growth = 0
    
    return {
        'total_uploads': total_uploads,
        'upload_growth': round(upload_growth, 1),
        'total_downloads': total_downloads,
        'download_growth': round(download_growth, 1),
        'total_followers': total_followers,
        'follower_growth': round(follower_growth, 1),
        'engagement_rate': round(engagement_rate, 1),
        'engagement_growth': round(engagement_growth, 1),
        'avg_rating': round(avg_rating, 1),
        'total_ratings': total_ratings,
        'total_bookmarks': total_bookmarks,
    }


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profileview',user_id = request.user.id)
    else:
        form = ProfileForm(instance=request.user.profile)

    return render(request, 'profile/edit.html', {'form': form})


# Follow/Unfollow functionality
@login_required
@require_POST
def toggle_follow(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    
    # Prevent self-following
    if request.user == target_user:
        messages.error(request, "You cannot follow yourself.")
        return redirect('profile_view', user_id=user_id)
    
    follow_obj, created = Follow.objects.get_or_create(
        follower=request.user,
        following=target_user
    )
    
    if not created:
        # Already following, so unfollow
        follow_obj.delete()
        action = 'unfollowed'
        is_following = False
    else:
        # Wasn't following, now following
        action = 'followed'
        is_following = True
    
    # If it's an AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'action': action,
            'is_following': is_following,
            'followers_count': target_user.followers.count()
        })
    
    # Regular request, redirect back
    messages.success(request, f"You have {action} {target_user.username}.")
    return redirect('profileview',user_id=request.user.id)


@login_required
def following_list(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    following = Follow.objects.filter(follower=user_obj).select_related('following__profile')
    
    context = {
        'user_obj': user_obj,
        'following': following,
        'is_own_profile': request.user == user_obj,
    }
    
    return render(request, 'profile/following_list.html', context)


@login_required
def followers_list(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    followers = Follow.objects.filter(following=user_obj).select_related('follower__profile')
    
    context = {
        'user_obj': user_obj,
        'followers': followers,
        'is_own_profile': request.user == user_obj,
    }
    
    return render(request, 'profile/followers_list.html', context)

# views.py
# Use this debug version temporarily to see what's happening:

@login_required
def content_edit(request, pk):
    content = get_object_or_404(Content, pk=pk)
    if request.user != content.author:
        messages.error(request, "You are not authorized to edit this content.")
        return redirect('content_detail', pk=pk)

    if request.method == 'POST':
        print(f"POST data: {request.POST}")
        print(f"FILES data: {request.FILES}")
        print(f"Current file: {content.file}")
        
        form = ContentEditForm(request.POST, request.FILES, instance=content)
        
        if form.is_valid():
            print("Form is valid")
            # Get the remove_file flag from POST data
            remove_file = request.POST.get('remove_file') == 'true'
            print(f"Remove file flag: {remove_file}")
            
            # Get the new file from cleaned data
            new_file = form.cleaned_data.get('file')
            print(f"New file from form: {new_file}")
            
            # Save form but don't commit yet
            updated_content = form.save(commit=False)
            
            # Handle file operations
            if remove_file and not new_file:
                print("Removing file without replacement")
                if updated_content.file:
                    old_file = updated_content.file
                    updated_content.file = None
                    print(f"Deleting old file: {old_file}")
                    if old_file:
                        try:
                            old_file.delete(save=False)
                            print("Old file deleted successfully")
                        except Exception as e:
                            print(f"Error deleting old file: {e}")
            
            elif new_file:
                print(f"New file being uploaded: {new_file}")
                # Handle old file cleanup
                if content.file and content.file != new_file:
                    old_file = content.file
                    print(f"Cleaning up old file: {old_file}")
                    try:
                        old_file.delete(save=False)
                        print("Old file cleaned up successfully")
                    except Exception as e:
                        print(f"Error cleaning up old file: {e}")
            
            # Now save the content
            try:
                updated_content.save()
                print(f"Content saved successfully. New file: {updated_content.file}")
                messages.success(request, "Content updated successfully.")
                return redirect('content_detail', pk=updated_content.pk)
            except Exception as e:
                print(f"Error saving content: {e}")
                messages.error(request, f"Error saving content: {str(e)}")
        else:
            print("Form is not valid")
            print(f"Form errors: {form.errors}")
            # Debug form errors
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Form error - {field}: {error}")
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = ContentEditForm(instance=content)

    return render(request, 'content/content_edit.html', {'form': form, 'content': content})

# Delete content
@login_required
@require_POST
def content_delete(request, pk):
    content = get_object_or_404(Content, pk=pk)
    if request.user != content.author:
        messages.error(request, "You are not authorized to delete this content.")
        return redirect('content_detail', pk=pk)
    

    content.delete()
    messages.success(request, "Content deleted successfully.")
    return redirect('home')


# ===== Search APIs =====
def search_api(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'contents': [], 'users': [], 'tags': []})

    contents = Content.objects.filter(
        Q(name__icontains=query) |
        Q(desc__icontains=query) |
        Q(tags__icontains=query),
        is_public=True
    ).select_related('author').order_by('-date')[:5]

    contents_data = [{
        'id': c.id,
        'name': c.name,
        'desc': c.desc[:100] + ('...' if len(c.desc) > 100 else ''),
        'content_type': c.content_type,
        'date': c.date.isoformat(),
        'author__username': c.author.username,
        'download_count': c.download_count,
        'rate': float(c.rate),
        'tags': c.tags
    } for c in contents]

    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(profile__bio__icontains=query) |
        Q(profile__institution__icontains=query)
    ).select_related('profile').annotate(
        content_count=Count('contents', filter=Q(contents__is_public=True))
    )[:3]

    users_data = [{
        'id': u.id,
        'username': u.username,
        'first_name': u.first_name,
        'last_name': u.last_name,
        'profile__bio': u.profile.bio if hasattr(u, 'profile') else '',
        'profile__institution': u.profile.institution if hasattr(u, 'profile') else '',
        'content_count': u.content_count
    } for u in users]

    tags_data = []
    if len(query) >= 2:
        all_tags = Content.objects.filter(is_public=True, tags__icontains=query).values_list('tags', flat=True)
        tag_counter = Counter()
        for tags_string in all_tags:
            if tags_string:
                tags = [t.strip().lower() for t in tags_string.split(',') if t.strip()]
                for t in tags:
                    if query.lower() in t:
                        tag_counter[t] += 1
        for tag, count in tag_counter.most_common(4):
            tags_data.append({'name': tag.title(), 'count': count})

    return JsonResponse({'contents': contents_data, 'users': users_data, 'tags': tags_data})

@receiver([post_save, post_delete], sender=Rating)
def update_content_rating(sender, instance, **kwargs):
    content = instance.content
    avg_rating = content.ratings.aggregate(avg=Avg('score'))['avg'] or 0
    content.rate = round(avg_rating, 1)  # 1 decimal place
    content.save(update_fields=['rate'])


@login_required
@require_POST
def rate_content(request, content_id):
    content = get_object_or_404(Content, pk=content_id)
    try:
        score = int(request.POST.get('score'))
        if score < 1 or score > 5:
            raise ValueError
    except (ValueError, TypeError):
        messages.error(request, "Invalid rating.")
        return redirect('content_detail', pk=content_id)

    Rating.objects.update_or_create(
        user=request.user,
        content=content,
        defaults={'score': score}
    )
    messages.success(request, "Your rating has been submitted.")
    return redirect('content_detail', pk=content_id)

# views.py
@login_required
def report_content(request, pk):
    content = get_object_or_404(Content, pk=pk)

    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report, created = ContentReport.objects.get_or_create(
                reporter=request.user,
                content=content,
                defaults=form.cleaned_data
            )
            if not created:
                messages.warning(request, "You have already reported this content.")
            else:
                messages.success(request, "Report submitted. Our moderators will review it.")
            return redirect('content_detail', pk=pk)
    else:
        form = ReportForm()

    return render(request, 'content/report_content.html', {
        'form': form,
        'content': content
    })

@login_required
@require_POST
def api_record_download(request, content_id):
    content = get_object_or_404(Content, id=content_id, is_public=True)
    Download.objects.create(user=request.user, content=content)
    Content.objects.filter(id=content.id).update(download_count=models.F('download_count') + 1)
    return JsonResponse({'success': True, 'download_count': Content.objects.get(pk=content.id).download_count})

@require_POST
def increment_download(request, content_id):
    """
    Increment download count and create download record
    """
    content = get_object_or_404(Content, id=content_id)
    
    # Increment the download count
    content.download_count += 1
    content.save()
    
    # Create download record if user is authenticated
    if request.user.is_authenticated:
        Download.objects.create(
            user=request.user,
            content=content
        )
    else:
        # Create anonymous download record
        Download.objects.create(
            content=content
        )
    
    return JsonResponse({'status': 'success', 'download_count': content.download_count})