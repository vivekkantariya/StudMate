from .forms import CustomUserForm, ContentForm
from django.contrib.auth import login , logout as django_logout
from django.contrib.auth.models import User 
from django.contrib.auth.decorators import login_required 
from .models import Content
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import ProfileForm
from django.contrib import messages


# Create your views here.
def home(request):
    data = Content.objects.all()
    return render(request,"content/home.html",{'data':data})

# when we dealing with inbuilt django auth we want to use outer templates directory html for rendering 
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
    
    return render(request, "registration/register.html",{"form" : form})


def logout_view(request):
    django_logout(request)
    return redirect('home')

from django.db.models import Sum, Count
from django.core.paginator import Paginator
from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Content  # Make sure this import is correct

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Content, Bookmark

@login_required
def bookmark(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, content=content)

    if not created:
        # Bookmark already exists, so remove it
        bookmark.delete()

    return redirect(request.META.get('HTTP_REFERER', 'content_list'))  # Redirect back to previous page

@login_required
def bookmarked_contents(request):
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('content')
    contents = [b.content for b in bookmarks]
    for c in contents:
        c.is_bookmarked = True
    return render(request, 'content/my_bookmarks.html', {'contents': contents})


def content_list(request):
    print("=== DEBUG: Starting content_list view ===")
    
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
    
    # DEBUG: Check if we have any content
    print(f"DEBUG: Total Content objects in DB: {Content.objects.count()}")
    print(f"DEBUG: Public Content objects: {Content.objects.filter(is_public=True).count()}")
    print(f"DEBUG: Total User objects: {User.objects.count()}")
    
    # Calculate stats with detailed debugging
    try:
        total_resources = Content.objects.filter(is_public=True).count()
        print(f"DEBUG: total_resources = {total_resources}")
        
        active_users = User.objects.count()
        print(f"DEBUG: active_users = {active_users}")
        
        # Check if download_count field has any values
        download_sum = Content.objects.filter(is_public=True).aggregate(
            total=Sum('download_count')
        )['total']
        total_downloads = download_sum if download_sum is not None else 0
        print(f"DEBUG: total_downloads = {total_downloads}")
        
        # Debug individual download counts
        content_downloads = Content.objects.filter(is_public=True).values_list('name', 'download_count')
        print(f"DEBUG: Individual download counts: {list(content_downloads)}")
        
    except Exception as e:
        print(f"DEBUG: Error calculating stats: {e}")
        total_resources = 0
        active_users = 0
        total_downloads = 0
    
    # Content type counts
    content_counts = {
        'total_resources': total_resources,
        'note_count': Content.objects.filter(content_type='note', is_public=True).count(),
        'assignment_count': Content.objects.filter(content_type='ass', is_public=True).count(),
        'practical_count': Content.objects.filter(content_type='prac', is_public=True).count(),
        'project_count': Content.objects.filter(content_type='project', is_public=True).count(),
    }
    
    print(f"DEBUG: content_counts = {content_counts}")
    
    context = {
        'data': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'active_users': active_users,
        'total_downloads': total_downloads,
        **content_counts,
    }
    
    print(f"DEBUG: Final context keys: {list(context.keys())}")
    print(f"DEBUG: Context values - total_resources: {context['total_resources']}, active_users: {context['active_users']}, total_downloads: {context['total_downloads']}")
    
    return render(request, 'content/home.html', context)
# View: Content detail
def content_detail(request, pk):
    item = get_object_or_404(Content, pk=pk)
    context = {
        'item': item
    }
    return render(request, 'content/content_detail.html', context)

# View: Create new content
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
    
def edit_content(request):
    if request.method == 'POST':
        pass
    
@login_required
def my_upload(request):
    data = Content.objects.filter(author=request.user)
    print("Data found:", data)  # check your server console
    return render(request, 'content/myupload.html', {'data': data})

@login_required
def profile_view(request):
    profile = request.user.profile
    return render(request, 'profile/view.html', {'profile': profile})

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