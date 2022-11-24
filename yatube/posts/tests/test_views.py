
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Group, Post, Follow

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='UserAuthor')
        cls.user2 = User.objects.create_user(username='UserAuthor2')
        cls.user3 = User.objects.create_user(username='UserAuthor3')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='dogs',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',

        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        self.authorized_client3 = Client()
        self.authorized_client3.force_login(self.user3)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': 'dogs'})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': 'UserAuthor'})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': '1'})
            ),
            'posts/create_post.html': reverse('posts:post_create'),

        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_post_uses_correct_template(self):
        templates_pages_names = {
            'posts/create_post.html': (
                reverse('posts:post_edit', kwargs={'post_id': '1'})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_correct_page_context(self):
        '''Проверка контекста страниц'''
        pages: tuple = (
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': 'UserAuthor'}),
            reverse('posts:group_list', kwargs={'slug': 'dogs'})

        )
        for adress in pages:
            with self.subTest(adress=adress):
                response_post = self.guest_client.get(adress)
                obj = response_post.context['page_obj'][0]
                self.assertEqual(obj.text, self.post.text)
                self.assertEqual(obj.author, self.post.author)
                if adress == 'posts/group_list.html':
                    self.assertEqual(obj.group, self.group)

        cache.clear()
        post = Post.objects.create(
            text='Тестовый текст добавления',
            group=self.group,
            author=self.user)
        for adress in pages:
            with self.subTest(adress=adress):
                response_post_add = self.authorized_client.get(adress)
                object = response_post_add.context['page_obj']
                self.assertIn(post, object, f'Пост не появился {adress}')

    def test_post_detail_page_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:post_detail',
                                         kwargs={'post_id': '1'}))
        obj = response.context['post']
        self.assertEqual(obj.text, self.post.text)
        self.assertEqual(obj.group, self.post.group)
        self.assertEqual(obj.author, self.post.author)

    def test_post_added_correctly(self):
        group1 = Group.objects.create(
            title='Тестовая группа',
            slug='test_group1')
        posts_count = Post.objects.filter(group=self.group).count()
        Post.objects.create(
            text='Тестовый пост иной группы',
            author=self.user,
            group=group1,
        )
        group = Post.objects.filter(group=self.group).count()
        error_name = 'Пост отсутствует в иной группе'
        self.assertEqual(group, posts_count, error_name)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.user,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)

    def test_following_correctly(self):
        follow_count = Follow.objects.filter(user=self.user2).count()
        Follow.objects.get_or_create(author=self.user, user=self.user2)
        follow_count2 = Follow.objects.filter(user=self.user2).count()
        self.assertEqual(follow_count+1, follow_count2, "Нет подписки")
        Follow.objects.filter(author=self.user, user=self.user2).delete()
        follow_count3 = Follow.objects.filter(user=self.user2).count()
        self.assertEqual(follow_count3, follow_count2-1, "Отписка не удалась")

    def test_following_post_added_correctly(self):
        response = self.authorized_client2.get(reverse('posts:follow_index'))
        response2 = self.authorized_client3.get(reverse('posts:follow_index'))
        posts = response.content
        posts2 = response2.content
        Follow.objects.get_or_create(author=self.user, user=self.user2)
        Post.objects.create(
            text='Тестовый пост для подписчика',
            author=self.user,
        )
        response_follower = self.authorized_client2.get(reverse('posts:follow_index'))
        follower_posts = response_follower.content
        self.assertNotEqual(follower_posts, posts, 'Подписчик не видит посты')
        response_notfollower = self.authorized_client3.get(reverse('posts:follow_index'))
        notfollower_posts = response_notfollower.content
        self.assertEqual(notfollower_posts, posts2, 'Не подписчик видит посты')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Группа для тестов',
            slug='dogs',
        )
        cls.user = User.objects.create_user(username='UserAuthor')
        post_list = []
        for i in range(15):
            post_list.append(Post(
                text=f'Тестовый текст {i}',
                group=cls.group,
                author=cls.user)
            )
        Post.objects.bulk_create(post_list)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_index_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_index_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 5)

    def test_first_page_profile_contains_three_records(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': 'UserAuthor'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_profile_contains_three_records(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': 'UserAuthor'}) + '?page=5')
        self.assertEqual(len(response.context['page_obj']), 5)

    def test_first_page_groups_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'dogs'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_groups_contains_three_records(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'dogs'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 5)
