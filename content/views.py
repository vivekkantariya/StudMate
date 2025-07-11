from .forms import CustomUserForm, ContentForm
from django.contrib.auth import login 
from .models import Content
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q

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

# View: List all content with filters and pagination
def content_list(request):
    search_query = request.GET.get('search', '')
    content_type = request.GET.get('content_type', '')
    sort_by = request.GET.get('sort_by', 'date')

    contents = Content.objects.all()

    if search_query:
        contents = contents.filter(
            Q(name__icontains=search_query) |
            Q(desc__icontains=search_query) |
            Q(tag_list__icontains=search_query)
        )

    if content_type:
        contents = contents.filter(content_type=content_type)

    contents = contents.order_by(sort_by)

    paginator = Paginator(contents, 9)  # 9 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'data': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
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