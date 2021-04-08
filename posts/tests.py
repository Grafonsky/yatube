from django.test import TestCase, Client, override_settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import HttpResponse
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import User, Post, Group, Comment


User = get_user_model()


TEST_CASHE = {
            "default": {
                "BACKEND": "django.core.cache.backends.dummy.DummyCache",
                }
            }


class CreatePostsTestCase(TestCase):
    def setUp(self):
        self.unauthorized_client = Client()
        self.authorized_client = Client()
        self.user = User.objects.create_user(
            username = "TestUser",
            email = "testovy@email.com",
            password = "1fx6|unz#i",
        )
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title="Тестовая группа",
            slug="testgroup",
            description="Тестовое описание"
        )

    def test_authorized_create_post(self):
        """Авторизованный пользователь может опубликовать пост (new)"""
        self.authorized_client.post(
            reverse("new_post"), {
                "text": "Тестовому пользователю тестовый пост!",
                "group": self.group.id,
                "author": self.user,
                }
        )
        cache.clear()
        self.assertEqual(Post.objects.filter(
            text="Тестовому пользователю тестовый пост!",
            group=self.group.id,
            author=self.user,
        ).count(), 1)
        
    def test_unauthorized_create_post(self):
        """Неавторизованный посетитель не может опубликовать пост
        (его редиректит на страницу входа)
        """
        response = self.unauthorized_client.post(
            reverse("new_post"), {
                "text": "Тестовому пользователю тестовый пост!",
                "group": self.group.id,
                "author": self.user,
            }
        )
        cache.clear()
        self.assertRedirects(
            response,
            "/auth/login/?next=/new/",
            status_code=302
        )


class NewPostsTestCase(TestCase):
    def setUp(self):
        self.authorized_client = Client()
        self.user = User.objects.create_user(
            username = "TestUser",
            email = "testovy@email.com",
            password = "1fx6|unz#i",
        )
        self.group = Group.objects.create(
            title="Тестовая группа",
            slug="testgroup",
            description="Тестовое описание"
        )
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            text="Тестовому пользователю тестовый пост!",
            group = self.group,
            author=self.user,
        )

    def test_new_post(self):
        """После публикации поста, новая запись появляется на главной странице
        сайта (index), на персональной странице пользователя (profile) и
        на отдельной странице поста (post)
        """
        urls = (
            reverse("index"),
            reverse("profile", args=[self.user]),
            reverse("post", args=[self.user, self.post.id])
        )
        cache.clear()
        for url in urls:
            response = self.authorized_client.get(url)
            self.assertContains(response, self.post)


class PostsEditTestCase(TestCase):
    def setUp(self):
        self.authorized_client = Client()
        self.user = User.objects.create_user(
            username = "TestUser",
            email = "testovy@email.com",
            password = "1fx6|unz#i",
        )
        self.group_one = Group.objects.create(
            title="Тестовая группа",
            slug="testgroup_one",
            description="Тестовое описание"
        )
        self.group_two = Group.objects.create(
            title="Еще одна тестовая группа!",
            slug="testgroup_two",
            description="Никто здесь группу не оставлял?"
        )
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            text="Тестовому пользователю тестовый пост!",
            group = self.group_one,
            author=self.user,
        )
        self.new_text = "Тестовому посту тестовое редактирование!"
        self.client.post(
            reverse("post_edit", args=[self.user.username, self.post.id]),
            {"text": self.new_text, "group": self.group_two}
        )

    def test_post_edit(self):
        """Авторизованный пользователь может отредактировать свой пост,
        после этого содержимое поста изменится на главной странице
        сайта (index), на персональной странице пользователя (profile),
        на отдельной странице поста (post)
        """
        urls = (
            reverse("index"),
            reverse("profile", args=[self.user]),
            reverse("post", args=[self.user, self.post.id])
        )
        cache.clear()
        for url in urls:
            response = self.authorized_client.get(url)
            self.assertContains(response, self.post)


class ServerResponseTestCase(TestCase):
    def test_404(self):
        self.authorized_client = Client()
        response = self.client.get("/test/test404page/test")
        self.assertEqual(response.status_code, 404)


class ImgUploadCaseTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username = "TestUser",
            email = "testovy@email.com",
            password = "1fx6|unz#i",
        )
        self.client.force_login(self.user)
        self.group = Group.objects.create(
            title="Тестовая группа",
            slug="testgroup",
            description="Тестовое описание"
        )
        dir_path = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04"
            b"\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02"
            b"\x44\x01\x00\x3b"
        )
        image = SimpleUploadedFile(
            "small_pic.jpg",
            dir_path,
            content_type="image"
        )
        self.client.post(
            reverse("new_post"), {
                "text": "Тестовый пост с картинкой",
                "author": self.user,
                "group": self.group.id,
                "image": image,
            }
        )
    
    def test_img(self):
        """Проверка наличия картинки на странице отдельной записи, группы,
        профиля и на главной странице
        """
        urls = (
            reverse("index"),
            reverse("profile", args=[self.user.username]),
            reverse("post", args=[self.user.username, 1]),
            reverse("group", args=[self.group.slug]),
        )
        cache.clear()
        for url in urls:
            response = self.client.get(url)
            self.assertContains(response, "<img")

    def test_not_img(self):
        """Проверка защиты от загрузки файлов неграфических форматов
        """
        dir_path = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04"
            b"\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02"
            b"\x44\x01\x00\x3b"
        )
        image = SimpleUploadedFile(
            "small_doc.doc",
            dir_path,
            content_type="doc"
        )
        self.client.post(
            reverse("new_post"), {
                "text": "Тестовый пост с картинкой",
                "author": self.user,
                "group": self.group.id,
                "image": image,
            }
        )
        cache.clear()
        self.assertEqual(Post.objects.count(), 1)


class CashTestCase(TestCase):
    def setUp(self):
        self.authorized_client = Client()
        self.user = User.objects.create_user(
            username = "TestUser",
            email = "testovy@email.com",
            password = "1fx6|unz#i",
        )
        self.group = Group.objects.create(
            title="Тестовая группа",
            slug="testgroup",
            description="Тестовое описание"
        )
        self.authorized_client.force_login(self.user)

    @override_settings(CASHES=TEST_CASHE)
    def test_cache(self):
        response = self.authorized_client.get("")
        self.post = Post.objects.create(
            text="Тестовому пользователю тестовый пост!",
            group = self.group,
            author=self.user,
        )
        self.assertNotContains(response, self.post)
        cache.clear()
        response = self.authorized_client.get("")
        self.assertContains(response, self.post)


class FollowCaseTest(TestCase):
    def setUp(self):
        self.authorized_client = Client()
        self.user_one = User.objects.create_user(
            username = "TestUser1",
            email = "testovy@email.com",
            password = "1fx6|unz#i",
        )
        self.user_two = User.objects.create_user(
            username = "TestUser2",
            email = "testovy@email.com",
            password = "1fx6|unz#i",
        )
        self.group = Group.objects.create(
            title="Тестовая группа",
            slug="testgroup",
            description="Тестовое описание"
        )
        self.authorized_client.force_login(self.user_two)
        self.post = Post.objects.create(
            text="Тестовому пользователю тестовый пост!",
            group = self.group,
            author=self.user_one,
        )

    def test_follow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей
        """
        self.authorized_client.get(
            reverse(
                "profile_follow",
                args=[self.user_one]
            )
        )
        self.assertEqual(self.user_two.follower.count(), 1)

    def test_unfollow(self):
        """Авторизованный пользователь может отписываться от других
        пользователей
        """
        self.authorized_client.get(
            reverse(
                "profile_unfollow",
                args=[self.user_one]
            )
        )
        self.assertEqual(self.user_two.follower.count(), 0)

    def test_not_follow_index(self):
        """Авторизованный пользователь не видит посты людей, на которых он
        не подписан
        """
        url = reverse("follow_index")
        response = self.authorized_client.get(url)
        self.assertNotContains(response, self.post)

    def test_follow_index(self):
        self.authorized_client.get(
            reverse(
                "profile_follow",
                args=[self.user_one]
            )
        )
        url = reverse("follow_index")
        response = self.authorized_client.get(url)
        self.assertContains(response, self.post)


class CommentCaseTest(TestCase):
    def setUp(self):
        self.authorized_client = Client()
        self.user = User.objects.create_user(
            username = "TestUser",
            email = "testovy@email.com",
            password = "1fx6|unz#i",
        )
        self.group = Group.objects.create(
            title="Тестовая группа",
            slug="testgroup",
            description="Тестовое описание"
        )
        self.post = Post.objects.create(
            text="Тестовому пользователю тестовый пост!",
            group = self.group,
            author=self.user,
        )

    def test_not_authorized_comment(self):
        """Проверка возможности комментирования у неавторизованного
        пользователя
        """
        response = self.client.post(
            reverse("add_comment", args=[self.user.username, self.post.id]),
            follow = True
        )
        self.assertRedirects(
            response,
            f"/auth/login/?next=/{self.user.username}/{self.post.id}/comment",
            status_code=302
        )

    def test_authorized_comment(self):
        """Проверка возможности комментирования у авторизованного
        пользователя
        """
        self.authorized_client.force_login(self.user)
        self.authorized_client.post(
            reverse("add_comment", args=[self.user.username, self.post.id]), {
                "text": "дизлайк отписка",
                "author": self.user,
                "post": self.post,
            }
        )
        self.assertEqual(Comment.objects.filter(
            text="дизлайк отписка",
            author=self.user,
            post=self.post,
        ).count(), 1)
    