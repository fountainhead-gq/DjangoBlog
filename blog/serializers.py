from django.contrib.auth.models import User
from django.conf import settings
from django.utils.timezone import now
from rest_framework import serializers
from blog.models import Post, Author, Category, Tag


# class AuthorSerializer(serializers.HyperlinkedModelSerializer):
#     user = serializers.CharField()
#     class Meta:
#         model = Author
#         # fields = '__all__'
#         fields = ('user', 'about', 'website')
        

# class CategorySerializer(serializers.HyperlinkedModelSerializer):
#     url = serializers.HyperlinkedIdentityField(view_name='api:category-detail')
#     class Meta:
#         model = Category
#         fields = ('id', 'name','url')
        

# class TagSerializer(serializers.HyperlinkedModelSerializer):
#     url = serializers.HyperlinkedIdentityField(view_name='api:tag-detail')
#     class Meta:
#         model = Tag
#         fields = ('id', 'title', 'slug', 'url')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Author
        # fields = '__all__'
        fields = ('id', 'user', 'about', 'website')

    def create(self, validated_data):
        profile_data = validated_data.pop('user')
        user = User.objects.create(**validated_data)
        Author.objects.create(user=user, **profile_data)
        return user        


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name','classify')
        

class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'title', 'slug')


class PostSerializer(serializers.HyperlinkedModelSerializer):
    # author = AuthorSerializer(read_only=True)
    # tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    category = CategorySerializer()
    tags = TagSerializer(many=True)
    
    class Meta:
        model = Post
        fields = ('id', 'title', 'slug',  'views', 'created', 'description',  'category', 'tags')
                