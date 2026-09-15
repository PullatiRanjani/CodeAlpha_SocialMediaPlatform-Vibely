from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import RegisterForm, LoginForm, PostForm, StoryForm, CommentForm, ProfileForm
from .models import (
    Profile, Follow, Post, Like, Comment, Story, StoryLike, StoryReply,
    StoryView, Notification,
)


def ensure_profile(user):
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={'display_name': user.first_name},
    )
    return profile


def public_users(qs):
    return qs.filter(is_active=True, is_staff=False, is_superuser=False)


def social_user_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return wrapped


def active_stories():
    return (
        Story.objects
        .filter(
            expires_at__gt=timezone.now(),
            author__is_active=True,
            author__is_staff=False,
            author__is_superuser=False,
        )
        .select_related('author', 'author__profile')
        .order_by('-created_at')
    )


@social_user_required
def home(request):
    profile = ensure_profile(request.user)

    # Stories are visible only for the current user, people they follow,
    # and people who follow them. Own story is always shown separately.
    connection_ids = set(
        Follow.objects.filter(
            Q(follower=request.user) | Q(following=request.user)
        ).values_list('follower_id', 'following_id')
    )

    connected_user_ids = {
        uid
        for pair in connection_ids
        for uid in pair
        if uid != request.user.id
    }

    visible_story_users = connected_user_ids | {request.user.id}

    visible_stories = list(
        active_stories()
        .filter(author_id__in=visible_story_users)
        .order_by('-created_at')
    )

    # One story tile per user, while the viewer can navigate through all active stories.
    story_tiles = []
    seen = set()

    for story in visible_stories:
        if story.author_id not in seen:
            story_tiles.append(story)
            seen.add(story.author_id)

    posts = (
        Post.objects
        .filter(
            author=request.user,
            author__is_active=True,
            author__is_staff=False,
            author__is_superuser=False,
        )
        .select_related('author', 'author__profile')
        .prefetch_related('likes', 'comments__user')
    )

    people = (
        public_users(User.objects.exclude(pk=request.user.pk))
        .select_related('profile')
        .annotate(followers_count=Count('follower_links', distinct=True))
        .order_by('-followers_count', 'username')
    )

    following_ids = set(
        Follow.objects
        .filter(follower=request.user)
        .values_list('following_id', flat=True)
    )

    unread = request.user.notifications.filter(is_read=False).count()

    own_story = next(
        (s for s in story_tiles if s.author_id == request.user.id),
        None
    )

    other_story_tiles = [
        s for s in story_tiles
        if s.author_id != request.user.id
    ]

    return render(request, 'home.html', {
        'profile': profile,
        'own_story': own_story,
        'story_tiles': other_story_tiles,
        'posts': posts,
        'unread': unread,
        'people': people,
        'following_ids': following_ids,
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.email = form.cleaned_data['email']
        user.first_name = form.cleaned_data.get('first_name', '')
        user.save()

        ensure_profile(user)
        login(request, user)

        messages.success(request, 'Welcome to Vibely!')
        return redirect('home')

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        value = form.cleaned_data['username']
        password = form.cleaned_data['password']

        user = User.objects.filter(
            Q(username__iexact=value) |
            Q(email__iexact=value)
        ).first()

        if user:
            user = authenticate(
                request,
                username=user.username,
                password=password
            )

        if user is not None:
            login(request, user)
            ensure_profile(user)
            return redirect(request.GET.get('next') or 'home')

        form.add_error(
            None,
            'Invalid username/email or password.'
        )

    return render(request, 'auth/login.html', {'form': form})


@social_user_required
def logout_view(request):
    logout(request)
    return redirect('login')


@social_user_required
def create_post(request):
    if request.method == 'GET':
        return render(
            request,
            'create_post.html',
            {'form': PostForm()}
        )

    form = PostForm(request.POST, request.FILES)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        messages.success(request, 'Your post is live.')
        return redirect('home')

    return render(
        request,
        'create_post.html',
        {'form': form}
    )


@social_user_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(
        Post.objects.filter(
            author__is_staff=False,
            author__is_superuser=False
        ),
        pk=post_id,
    )

    like, created = Like.objects.get_or_create(
        user=request.user,
        post=post
    )

    if not created:
        like.delete()

    elif post.author_id != request.user.id:
        Notification.objects.create(
            recipient=post.author,
            actor=request.user,
            kind='like',
            post=post
        )

    return JsonResponse({
        'liked': created,
        'count': post.likes.count()
    })


@social_user_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(
        Post.objects.filter(
            author__is_staff=False,
            author__is_superuser=False
        ),
        pk=post_id,
    )

    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = request.user
        comment.save()

        if post.author_id != request.user.id:
            Notification.objects.create(
                recipient=post.author,
                actor=request.user,
                kind='comment',
                post=post,
                text=comment.text,
            )

    return redirect(
        request.META.get('HTTP_REFERER', 'home')
    )


@social_user_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(
        Post,
        pk=post_id,
        author=request.user
    )

    post.delete()

    messages.success(request, 'Post deleted.')
    return redirect('home')


@social_user_required
def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects
        .filter(
            author__is_staff=False,
            author__is_superuser=False
        )
        .select_related('author', 'author__profile')
        .prefetch_related(
            'comments__user',
            'comments__user__profile'
        ),
        pk=post_id,
    )

    return render(
        request,
        'post_detail.html',
        {
            'post': post,
            'comment_form': CommentForm()
        }
    )


@social_user_required
def profile(request, username):
    profile_user = get_object_or_404(
        public_users(User.objects.all()),
        username=username
    )

    ensure_profile(profile_user)

    is_following = (
        request.user != profile_user
        and Follow.objects.filter(
            follower=request.user,
            following=profile_user
        ).exists()
    )

    followers = public_users(
        User.objects.filter(
            following_links__following=profile_user
        )
    ).select_related('profile').distinct()

    following = public_users(
        User.objects.filter(
            follower_links__follower=profile_user
        )
    ).select_related('profile').distinct()

    posts = (
        Post.objects
        .filter(author=profile_user)
        .prefetch_related('likes', 'comments')
    )

    stories = Story.objects.filter(
        author=profile_user,
        expires_at__gt=timezone.now()
    )

    return render(request, 'profile.html', {
        'profile_user': profile_user,
        'profile': profile_user.profile,
        'posts': posts,
        'followers': followers,
        'following': following,
        'follower_count': followers.count(),
        'following_count': following.count(),
        'following_ids': set(
            Follow.objects
            .filter(follower=request.user)
            .values_list('following_id', flat=True)
        ),
        'is_following': is_following,
        'stories': stories,
    })


@social_user_required
@require_POST
def toggle_follow(request, username):
    target = get_object_or_404(
        public_users(User.objects.all()),
        username=username
    )

    if target == request.user:
        return redirect(
            'profile',
            username=username
        )

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=target,
    )

    if not created:
        follow.delete()

    else:
        Notification.objects.create(
            recipient=target,
            actor=request.user,
            kind='follow'
        )

    return redirect(
        'profile',
        username=username
    )


@social_user_required
def search(request):
    q = request.GET.get('q', '').strip()

    users = (
        public_users(User.objects.all())
        .filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(profile__display_name__icontains=q)
        )
        .select_related('profile')[:50]
        if q else []
    )

    posts = (
        Post.objects
        .filter(
            author__is_staff=False,
            author__is_superuser=False,
            caption__icontains=q,
        )
        .select_related(
            'author',
            'author__profile'
        )[:30]
        if q else []
    )

    return render(
        request,
        'search.html',
        {
            'q': q,
            'users': users,
            'posts': posts
        }
    )


@social_user_required
def notifications(request):
    notes = request.user.notifications.select_related(
        'actor',
        'actor__profile',
        'post',
        'story'
    )

    request.user.notifications.filter(
        is_read=False
    ).update(is_read=True)

    return render(
        request,
        'notifications.html',
        {'notifications': notes}
    )


@social_user_required
def settings_view(request):
    profile_obj = ensure_profile(request.user)

    form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=profile_obj,
    )

    if request.method == 'POST' and form.is_valid():
        remove_avatar = form.cleaned_data.get(
            'remove_avatar',
            False
        )

        if remove_avatar and profile_obj.avatar:
            profile_obj.avatar.delete(save=False)
            profile_obj.avatar = None

        p = form.save(commit=False)

        request.user.first_name = p.display_name
        request.user.save(
            update_fields=['first_name']
        )

        form.save()

        messages.success(
            request,
            'Profile updated.'
        )

        return redirect(
            'profile',
            username=request.user.username
        )

    return render(
        request,
        'settings.html',
        {'form': form}
    )


@social_user_required
def create_story(request):
    form = StoryForm(
        request.POST or None,
        request.FILES or None
    )

    if request.method == 'POST' and form.is_valid():
        story = form.save(commit=False)
        story.author = request.user
        story.save()

        messages.success(
            request,
            'Your story is live for 24 hours.'
        )

        return redirect('home')

    return render(
        request,
        'story_create.html',
        {'form': form}
    )


@social_user_required
def story_viewer(request, username):
    owner = get_object_or_404(
        public_users(User.objects.all()),
        username=username
    )

    allowed = (
        owner == request.user
        or Follow.objects.filter(
            Q(
                follower=request.user,
                following=owner
            )
            | Q(
                follower=owner,
                following=request.user
            )
        ).exists()
    )

    if not allowed:
        raise Http404(
            'This story is not available to you.'
        )

    stories = list(
        Story.objects
        .filter(
            author=owner,
            expires_at__gt=timezone.now(),
        )
        .order_by('created_at')
    )

    if not stories:
        raise Http404(
            'No active stories.'
        )

    if request.user != owner:
        for story in stories:
            StoryView.objects.get_or_create(
                story=story,
                user=request.user
            )

    return render(
        request,
        'story_viewer.html',
        {
            'owner': owner,
            'stories': stories
        }
    )


@social_user_required
@require_POST
def story_like(request, story_id):
    story = get_object_or_404(
        Story.objects.filter(
            expires_at__gt=timezone.now(),
            author__is_staff=False,
            author__is_superuser=False,
        ),
        pk=story_id,
    )

    allowed = (
        story.author_id == request.user.id
        or Follow.objects.filter(
            Q(
                follower=request.user,
                following=story.author
            )
            | Q(
                follower=story.author,
                following=request.user
            )
        ).exists()
    )

    if not allowed:
        return JsonResponse(
            {'error': 'not allowed'},
            status=403
        )

    if story.author_id == request.user.id:
        return JsonResponse(
            {'error': 'own story'},
            status=400
        )

    like, created = StoryLike.objects.get_or_create(
        user=request.user,
        story=story
    )

    if not created:
        like.delete()

    else:
        Notification.objects.create(
            recipient=story.author,
            actor=request.user,
            kind='story_like',
            story=story
        )

    return JsonResponse({
        'liked': created,
        'count': story.likes.count()
    })


@social_user_required
@require_POST
def story_reply(request, story_id):
    story = get_object_or_404(
        Story.objects.filter(
            expires_at__gt=timezone.now(),
            author__is_staff=False,
            author__is_superuser=False,
        ),
        pk=story_id,
    )

    allowed = (
        story.author_id == request.user.id
        or Follow.objects.filter(
            Q(
                follower=request.user,
                following=story.author
            )
            | Q(
                follower=story.author,
                following=request.user
            )
        ).exists()
    )

    if allowed and story.author_id != request.user.id:
        text = request.POST.get(
            'text',
            ''
        ).strip()

        if text:
            StoryReply.objects.create(
                user=request.user,
                story=story,
                text=text
            )

            Notification.objects.create(
                recipient=story.author,
                actor=request.user,
                kind='story_reply',
                story=story,
                text=text,
            )

    return redirect(
        'story_viewer',
        username=story.author.username
    )


@social_user_required
@require_POST
def delete_story(request, story_id):
    story = get_object_or_404(
        Story,
        pk=story_id,
        author=request.user
    )

    story.delete()

    messages.success(
        request,
        'Story deleted.'
    )

    return redirect('home')


@social_user_required
def story_insights(request, story_id):
    story = get_object_or_404(
        Story,
        pk=story_id,
        author=request.user
    )

    viewers = (
        StoryView.objects
        .filter(story=story)
        .select_related(
            'user',
            'user__profile'
        )
    )

    likes = (
        StoryLike.objects
        .filter(story=story)
        .select_related(
            'user',
            'user__profile'
        )
    )

    replies = (
        StoryReply.objects
        .filter(story=story)
        .select_related(
            'user',
            'user__profile'
        )
    )

    return render(
        request,
        'story_insights.html',
        {
            'story': story,
            'viewers': viewers,
            'likes': likes,
            'replies': replies,
        }
    )