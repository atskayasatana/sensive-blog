from django.db.models import Count
from django.db.models import Prefetch
from django.shortcuts import render
from blog.models import Comment, Post, Tag


def get_likes_count(post):
    return post.num_likes


def get_related_posts_count(tag):
    return tag.posts.count()


def serialize_post_optimized(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': 0,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': len(Post.objects.filter(tags=tag)),
    }


def index(request):

    most_popular_posts = Post.objects.annotate(num_likes=Count('likes')).order_by('-num_likes')[:5]

    fresh_posts = Post.objects.order_by('published_at')
    most_fresh_posts = list(fresh_posts)[-5:]

    most_popular_tags = Tag.objects.popular()[:5]

    context = {
        'most_popular_posts': [
            serialize_post_optimized(post) for post in most_popular_posts
        ],
        'page_posts': [serialize_post_optimized(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):

    posts = Post.objects.annotate(num_likes=Count('likes', distinct=True)).prefetch_related(Prefetch('author', to_attr='author_name')).order_by('-num_likes')
    posts_with_comments = Post.objects.annotate(comments_count=Count('comments'))
    ids_and_comments = posts_with_comments.values_list('id', 'comments_count')
    count_for_id = dict(ids_and_comments)

    for post in posts:
        post.comments_count = count_for_id[post.id]

    comments = Comment.objects.prefetch_related(Prefetch('author', to_attr='author_name'))

    idx = 0
    for post in posts:
        if post.slug != slug:
            idx+=1

    post = posts[idx]

    comments = comments.filter(post=post)
    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author_name,
        })



    likes = post.num_likes

    related_tags = post.tags.all()


    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author_name,
        'comments': serialized_comments,
        'likes_amount': likes,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
        'comments_amount':post.comments_count
    }

    most_popular_tags = Tag.objects.popular()[:5]

    most_popular_posts =  posts[:5]

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post_optimized(post) for post in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = Tag.objects.get(title=tag_title)

    all_tags = Tag.objects.all()
    popular_tags = Tag.objects.popular()
    most_popular_tags = Tag.objects.popular()[:5]

    most_popular_posts = []  # TODO. Как это посчитать?

    related_posts = tag.posts.all()[:20]

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post_optimized(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post_optimized(post) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
