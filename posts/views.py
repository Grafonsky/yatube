from django.http import request
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.views.decorators.cache import cache_page

from .models import Post, Group, Comment, Follow
from .forms import PostForm, CommentForm


User = get_user_model()


@cache_page(1 * 20, key_prefix="index_page")
def index(request):
    post_list = Post.objects.all().select_related("author")
    follow = False
    if request.user.is_authenticated:
        follow = Follow.objects.filter(user=request.user).exists()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "index.html", {
            "page": page,
            "paginator": paginator,
            "follow": follow,
        }
    )


def group(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group).all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html", {
            "group": group,
            "page": page,
            "paginator": paginator
        }
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("index")
    form = PostForm()
    return render(
        request,
        "new_post.html", {
            "form": form,
        }
    )   


def profile(request, username):
    profile  = get_object_or_404(User, username=username)
    post_list = profile.posts.all()
    paginator = Paginator(post_list, 10)
    posts_count = post_list.count()
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    followers = Follow.objects.filter(author=profile.id).count()
    follows = Follow.objects.filter(user=profile.id).count()
    following = Follow.objects.filter(
        author=profile.id,
        user=request.user.id
    ).exists()
    return render(
        request,
        "profile.html", {
            "profile": profile,
            "posts_count": posts_count,
            "page": page,
            "paginator": paginator,
            "followers": followers,
            "follows": follows,
            "following": following,
        }
    )
 
 
def post_view(request, username, post_id):
    profile  = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id)
    post_list = profile.posts.all()
    posts_count = post_list.count()
    form = CommentForm()
    comments = post.comments.all()
    followers = Follow.objects.filter(author=profile.id).count()
    follows = Follow.objects.filter(user=profile.id).count()
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            author=profile.id, 
            user=request.user.id
        ).exists()
    return render(
        request,
        "post.html", {
            "form": form, 
            "profile": profile,
            "post": post,
            "posts_count": posts_count,
            "comments": comments,
            "followers": followers,
            "follows": follows,
        }
    )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = post.author
    if request.user != user:
        return redirect("post", username=user.username, post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.method == "POST":
        form.save()
        return redirect(
            "post",
            username=request.user.username,
            post_id=post_id
        )
    return render(
        request,
        "new_post.html", {
            "form": form,
            "post": post,
        }
    )


def page_not_found(request, exception):
    return render(
        request, 
        "misc/404.html", 
        {"path": request.path}, 
        status=404
    )


def server_error(request):
    return render(
        request,
        "misc/500.html",
        status=500
    ) 


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = CommentForm(request.POST)
    comments = post.comments.all()
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect(
            "post",
            username=request.user.username,
            post_id=post_id
        )
    return redirect(
            "post",
            username=request.user.username,
            post_id=post_id
        )
    

@login_required
def follow_index(request):
    follower = get_object_or_404(User, username=request.user.username)
    post_list = Post.objects.filter(author__following__user=follower).all()
    paginator = Paginator(post_list, 10) 
    page_number = request.GET.get("page") 
    page = paginator.get_page(page_number)
    return render(
        request,
        "follow.html", {
            "page": page,
            "paginator": paginator,
        }
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follower = request.user
    if author.id != follower.id:
        Follow.objects.get_or_create(user=follower, author=author, defaults={
            "user": follower, "author": author
            }
        )
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    follower = request.user
    author = get_object_or_404(User, username=username)
    follow_check = Follow.objects.filter( 
        user=follower.id, 
        author=author.id, 
    )
    if follow_check.exists(): 
        follow_check.delete() 
    return redirect("profile", username=username)
