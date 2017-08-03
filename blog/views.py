import time
import datetime
import socket
import json
from markdown.extensions.toc import TocExtension
import markdown
from django.utils.text import slugify
from django.views import generic
from django.http import HttpResponse
from django.shortcuts import (render, render_to_response, redirect, get_object_or_404)
from django.core.mail import (send_mail, BadHeaderError)
from django.core.exceptions import ObjectDoesNotExist
from django.template import RequestContext
from django.conf import settings
from django.db.models import (Q, Count)
from .models import Category

from blog.models import *
from blog.forms import ContactForm
from blog.utils.paginator import GenericPaginator
from blog.serializers import AuthorSerializer, PostSerializer, CategorySerializer, TagSerializer
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response


def handler400(request):
    response = render_to_response('error_page.html', {'title': '400 Bad Request', 'message': '400'},
                                  context_instance=RequestContext(request))
    response.status_code = 400
    return response


def handler403(request):
    response = render_to_response('error_page.html', {'title': '403 Permission Denied', 'message': '403'},
                                  context_instance=RequestContext(request))
    response.status_code = 403
    return response


def handler404(request):
    response = render_to_response('error_page.html', {'title': '404 Not Found', 'message': '404'},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response


def handler500(request):
    response = render_to_response('error_page.html', {'title': '500 Server Error', 'message': '500'},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (IsAuthenticated,)
    # filter_backends = (filters.DjangoFilterBackend,)

    # /api/posts/{pk}/detail/
    @detail_route(methods=['get'])
    def detail(self, request, pk=None):
        post = get_object_or_404(Post, pk=pk)
        result = {
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'description': post.description,
            'meta_description': post.meta_description
        }

        return Response(result, status=status.HTTP_200_OK)    

    # /api/posts/all_posts/
    @list_route(methods=['get'])
    def all_posts(self, request):
        post = Post.objects.values_list('title', flat=True).distinct()
        return Response(post, status=status.HTTP_200_OK)


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = (IsAuthenticated,)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAuthenticated,)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticated,)



class HomepageView(generic.ListView):
    queryset = Post.objects.published()
    template_name = 'blog/blog_home.html'
    paginate_by = 5
    context_object_name = 'object_list'

    # 过滤数据，获取所有已发布文章，并且将内容转成markdown形式
    def get_queryset(self):
        object_list = Post.objects.published()
        for objects  in object_list:
            # 将markdown标记的文本转为html文本
            objects.description = markdown.markdown(objects.description,
                                      extensions=[
                                          'markdown.extensions.extra',
                                          'markdown.extensions.codehilite',
                                          'markdown.extensions.toc',
                                      ])        
        return object_list

    def get_context_data(self, **kwargs):
        context_data = super(HomepageView, self).get_context_data(**kwargs)
        context_data['page_range'] = GenericPaginator(
            self.queryset,
            self.paginate_by,
            self.request.GET.get('page')
        ).get_page_range()
        return context_data



class DetailPostView(generic.DetailView):
    model = Post
    template_name = 'blog/blog_detail.html'
    context_object_name = 'post'

    def get_client_ip(self):
        ip = self.request.META.get("HTTP_X_FORWARDED_FOR", None)
        if ip:
            ip = ip.split(", ")[0]
        else:
            ip = self.request.META.get("REMOTE_ADDR", "")
        return ip

    def visitorCounter(self):
        obj = self.get_object()
        count = obj.increase_views()
        return count


    # def visitorCounter(self):
    #     try:
    #         Visitor.objects.get(
    #             post=self.object,
    #             ip=self.request.META['REMOTE_ADDR']
    #         )
    #     except ObjectDoesNotExist:
    #         dns = str(socket.getfqdn(
    #             self.request.META['REMOTE_ADDR']
    #         )).split('.')[-1]
    #         try:
    #             # trying for localhost: str(dns) == 'localhost',
    #             # trying for production: int(dns)
    #             if str(dns) == 'localhost':
    #                 visitor = Visitor(
    #                     post=self.object,
    #                     ip=self.request.META['REMOTE_ADDR']
    #                 )
    #                 visitor.save()
    #             else:
    #                 pass
    #         except ValueError:
    #             pass
    #     return Visitor.objects.filter(post=self.object).count()

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.publish == False:
            if request.user.is_anonymous() or \
                    request.user != obj.author.user:
                return redirect('homepage')
            else:
                return super(DetailPostView, self).dispatch(
                    request, *args, **kwargs
                )
        elif request.GET.get('format') == 'json':
            get_cover = lambda obj: None if obj.cover == None \
                or obj.cover == '' \
                else 'https://{0}{1}{2}'.format(
                    request.get_host(),
                    settings.MEDIA_URL,
                    obj.cover
                )
            data = dict(
                title=obj.title,
                url='https://{0}/blog/{1}'.format(
                    request.get_host(),
                    obj.slug
                ),
                cover=get_cover(obj),
                author=obj.author.user.username,
                created=str(obj.created)[:19],
                modified=str(obj.modified)[:19],
                tags=[
                    {'title': t.title, 'slug': t.slug}
                    for t in obj.tags.all()
                ],
                description=obj.description,
                visitors=obj.total_visitors
            )
            return HttpResponse(
                json.dumps(data),
                content_type='application/json'
            )
        else:
            return super(DetailPostView, self).dispatch(
                request, *args, **kwargs
            )

    def get_object(self, queryset=None):
        # 渲染markdown样式，覆写 get_object 方法的目的是因为需要对 post 的 description 值进行渲染
        post = super(DetailPostView, self).get_object(queryset=None)
        post.description = markdown.markdown(post.description,
                                      extensions=[
                                          'markdown.extensions.extra',
                                          'markdown.extensions.codehilite',
                                          'markdown.extensions.toc',
                                      ])
        return post

    def get_context_data(self, **kwargs):
        context_data = super(DetailPostView, self).get_context_data(**kwargs)
        related_posts = Post.objects.filter(
            tags__in=list(self.object.tags.all())
        ).exclude(id=self.object.id).distinct()
        context_data['related_posts'] = related_posts[:5]  # limit for post
        context_data['get_client_ip'] = self.get_client_ip()
        context_data['visitor_counter'] = self.object.increase_views()
        return context_data



class SearchPostsView(generic.ListView):
    template_name = 'blog/blog_search.html'
    paginate_by = 10

    def get_queryset(self):
        self.query = self.request.GET.get('q')
        try:
            search_posts = Post.objects.published().filter(
                Q(title__icontains=self.query) |
                Q(description__icontains=self.query) |
                Q(keywords__icontains=self.query) |
                Q(meta_description__icontains=self.query)
            ).order_by('-created').order_by('-id')
            return search_posts
        except:
            return Post.objects.published()

    def get_context_data(self, **kwargs):
        context_data = super(SearchPostsView, self).get_context_data(**kwargs)
        context_data['query'] = self.query
        context_data['page_range'] = GenericPaginator(
            self.get_queryset(),
            self.paginate_by,
            self.request.GET.get('page')
        ).get_page_range()
        return context_data


class AuthorPostsView(generic.ListView):
    template_name = 'blog/blog_posts_author.html'
    paginate_by = 10

    def get_queryset(self):
        username = self.kwargs['username']
        self.author = get_object_or_404(Author, user__username=username)
        posts_author = Post.objects.published().filter(
            author=self.author
        ).order_by('-created').order_by('-id')
        return posts_author

    def get_context_data(self, **kwargs):
        context_data = super(AuthorPostsView, self).get_context_data(**kwargs)
        context_data['author'] = self.author
        context_data['page_range'] = GenericPaginator(
            self.get_queryset(),
            self.paginate_by,
            self.request.GET.get('page')
        ).get_page_range()
        return context_data


class TagPostsView(generic.ListView):
    template_name = 'blog/blog_posts_tag.html'
    paginate_by = 10

    def get_queryset(self):
        slug = self.kwargs['slug']
        self.tag = get_object_or_404(Tag, slug=slug)
        results_filter = Post.objects.published().filter(
            tags=self.tag
        ).order_by('-created').order_by('-id')
        return results_filter

    def get_context_data(self, **kwargs):
        context_data = super(TagPostsView, self).get_context_data(**kwargs)
        context_data['tag'] = self.tag
        context_data['page_range'] = GenericPaginator(
            self.get_queryset(),
            self.paginate_by,
            self.request.GET.get('page')
        ).get_page_range()
        return context_data


class CategoryView(generic.ListView):
    model = Post
    template_name = 'blog/blog_home.html'
    # context_object_name = 'post_list'

    def get_queryset(self):
        cate = get_object_or_404(Category, pk=self.kwargs.get('pk'))
        return super(CategoryView, self).get_queryset().filter(category=cate)


class ArchivesView(generic.ListView):
    model = Post
    template_name = 'blog/blog_home.html'
    # context_object_name = 'post_list'

    def get_queryset(self):
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        return super(ArchivesView, self).get_queryset().filter(created__year=year,created__month=month)


class SitemapView(generic.ListView):
    queryset = Post.objects.published()
    template_name = 'blog/blog_sitemap.html'
    paginate_by = 30

    def get_context_data(self, **kwargs):
        context_data = super(SitemapView, self).get_context_data(**kwargs)
        context_data['page_range'] = GenericPaginator(
            self.queryset,
            self.paginate_by,
            self.request.GET.get('page')
        ).get_page_range()
        return context_data


# class DetailPageView(generic.DetailView):
#     model = Page
#     template_name = 'blog/blog_page.html'


# class AboutView(generic.TemplateView):
#     model = Page
#     template_name = 'blog/blog_about.html'


class ContactView(generic.TemplateView):
    template_name = 'blog/blog_contact.html'

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        if context['form'].is_valid():
            cd = context['form'].cleaned_data
            subject = cd['subject']
            from_email = cd['email']
            message = cd['message']

            try:
                send_mail(
                    subject + " from {}".format(from_email),
                    message,
                    from_email,
                    [settings.EMAIL_HOST_USER]
                )
            except BadHeaderError:
                return HttpResponse('Invalid header found.')

            ctx = {
                'success': """Thankyou, We appreciate that you've
                taken the time to write us.
                We'll get back to you very soon.
                Please come back and see us often."""
            }
            return render(request, self.template_name, ctx)
        return super(generic.TemplateView, self).render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(ContactView, self).get_context_data(**kwargs)
        form = ContactForm(self.request.POST or None)
        context['form'] = form
        return context


class TrendingPostsView(generic.ListView):
    template_name = 'blog/blog_trending_posts.html'

    def get_queryset(self):
        posts = Post.objects.published()
        top_posts = Visitor.objects.filter(post__in=posts)\
            .values('post').annotate(visit=Count('post__id'))\
            .order_by('-visit')

        list_pk_top_posts = [pk['post'] for pk in top_posts]
        filter_posts = list(Post.objects.published().filter(pk__in=list_pk_top_posts))
        sorted_posts = sorted(filter_posts, key=lambda i: list_pk_top_posts.index(i.pk))

        self.get_filter = self.request.GET.get('filter')
        now_year = time.strftime("%Y")
        now_month = time.strftime("%m")
        now_date = datetime.date.today()
        start_week = now_date - datetime.timedelta(7)
        end_week = start_week + datetime.timedelta(7)

        if self.get_filter == 'week':
            filter_posts = list(Post.objects.published()
                                .filter(pk__in=list_pk_top_posts)
                                .filter(created__date__range=[start_week, end_week])
                                )
            sorted_posts = sorted(filter_posts, key=lambda i: list_pk_top_posts.index(i.pk))

        elif self.get_filter == 'month':
            filter_posts = list(Post.objects.published()
                                .filter(pk__in=list_pk_top_posts)
                                .filter(created__month=now_month)
                                .filter(created__year=now_year)
                                )
            sorted_posts = sorted(filter_posts, key=lambda i: list_pk_top_posts.index(i.pk))

        elif self.get_filter == 'year':
            filter_posts = list(Post.objects.published()
                                .filter(pk__in=list_pk_top_posts)
                                .filter(created__year=now_year)
                                )
            sorted_posts = sorted(filter_posts, key=lambda i: list_pk_top_posts.index(i.pk))

        else:
            self.get_filter == 'global'
            sorted_posts = sorted_posts
        return sorted_posts[:20]  # Return 20 posts only

    def get_context_data(self, **kwargs):
        context_data = super(TrendingPostsView, self).get_context_data(**kwargs)
        context_data['filter'] = self.get_filter
        return context_data
