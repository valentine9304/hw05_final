from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseRedirect

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow

POST_COUNT = 10
POST_THIRTY = 30


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, POST_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, POST_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    if request.user.is_authenticated:
        follow = Follow.objects.filter(
            author=author, user=request.user).exists()
    else:
        follow = False
    post_list = author.posts.all()
    post_count = author.posts.count()
    paginator = Paginator(post_list, POST_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        "author": author,
        "page_obj": page_obj,
        "post_count": post_count,
        'following': follow,
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_title = post.text[:POST_THIRTY]
    pub_date = post.pub_date
    author = post.author
    author_post_count = author.posts.all().count()
    comments = post.comments.all()
    form_comment = CommentForm()
    context = {
        'post': post,
        'author_post_count': author_post_count,
        'post_title': post_title,
        'pub_date': pub_date,
        'author': author,
        'comments': comments,
        'form_comment': form_comment,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect("posts:post_detail", post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {
        'post': post,
        'post_id': post_id,
        'form': form,
        'is_edit': True,
    }
    if not form.is_valid():
        return render(
            request, 'posts/create_post.html',
            context)
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_delete(request, post_id=None):
    post_to_delete = Post.objects.get(id=post_id)
    post_to_delete.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def follow_index(request):
    sub_authors_posts = Post.objects.filter(
        author__following__user=request.user)
    paginator = Paginator(sub_authors_posts, POST_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(author=author, user=request.user)
        return redirect('posts:profile', username=username)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.filter(author=author, user=request.user).delete()
        return redirect('posts:profile', username=username)
    return redirect('posts:profile', username=username)


def page_not_found(request, exception):
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def server_error(request):
    return render(request, 'core/500.html', status=500)


def permission_denied(request, exception):
    return render(request, 'core/403.html', status=403)


def csrf_failure(request, reason=''):
    return render(request, 'core/403csrf.html')
