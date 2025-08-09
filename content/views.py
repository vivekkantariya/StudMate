from collections import Counter
import re

from django.contrib import messages
from django.contrib.auth import login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .forms import CustomUserForm, ContentForm, ProfileForm, ReportForm
from .models import Content, Bookmark, Rating, ContentReport

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


# Profile views
@login_required
def profile_view(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    profile = user_obj.profile
    uploads = Content.objects.filter(author=user_obj)
    bookmarks = Bookmark.objects.filter(user=user_obj).select_related('content')
    bookmarked_contents = [b.content for b in bookmarks]
    for c in bookmarked_contents:
        c.is_bookmarked = True

    return render(request, 'profile/view.html', {
        'profile': profile,
        'uploads': uploads,
        'bookmarks': bookmarked_contents,
    })


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profileview')
    else:
        form = ProfileForm(instance=request.user.profile)

    return render(request, 'profile/edit.html', {'form': form})


# Edit content
def content_edit(request, pk):
    content = get_object_or_404(Content, pk=pk)
    if request.user != content.author:
        messages.error(request, "You are not authorized to edit this content.")
        return redirect('content_detail', pk=pk)

    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES, instance=content)
        if form.is_valid():
            form.save()
            messages.success(request, "Content updated successfully.")
            return redirect('content_detail', pk=content.pk)
    else:
        form = ContentForm(instance=content)

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
