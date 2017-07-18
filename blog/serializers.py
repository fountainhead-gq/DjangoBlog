from django.contrib.auth.models import User
from django.conf import settings
from django.utils.timezone import now
from rest_framework import serializers
from blog.models import Post, Author, Category, Tag


class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.CharField()
    class Meta:
        model = Author
        # fields = '__all__'
        fields = ('user', 'about', 'website')
        

class CategorySerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='api:category-detail')
    class Meta:
        model = Category
        fields = ('id', 'name','url')
        

class TagSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='api:tag-detail')
    class Meta:
        model = Tag
        fields = ('id', 'title', 'slug', 'url')


class PostSerializer(serializers.HyperlinkedModelSerializer):
    # author = AuthorSerializer()
    # category = CategorySerializer()
    # tags = TagSerializer()
    
    class Meta:
        model = Post
        # fields = '__all__'
        fields = ('id', 'title', 'slug', 'keywords', 'views', 'created', 'description', 'meta_description', 'category', 'tags')
                