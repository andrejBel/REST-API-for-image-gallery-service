from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Item, Image, Comment, MyUser, Vote, Favourite


class VotesInline(admin.TabularInline):
    model = Image.votes.through
    verbose_name = "Vote"
    verbose_name_plural = "Votes"
    extra = 1


class CommentsInline(admin.TabularInline):
    model = Image.comments.through
    verbose_name = "Comment"
    verbose_name_plural = "Comments"
    extra = 1


class FavouritesInline(admin.TabularInline):
    model = Image.favourites.through
    verbose_name = "Favourite"
    verbose_name_plural = "Favourite"
    extra = 1


class ReportsInline(admin.TabularInline):
    model = Image.reports.through
    verbose_name = "Report"
    verbose_name_plural = "Report"
    extra = 1


class ImageInline(admin.ModelAdmin):
    model = Image
    exclude = ("votes", "comments")
    inlines = (
        VotesInline, CommentsInline, FavouritesInline, ReportsInline
    )


class UserAdmin(BaseUserAdmin):
    exclude = ("votes", "comments")
    inlines = (
        VotesInline, CommentsInline, FavouritesInline, ReportsInline
    )


admin.site.register(MyUser, UserAdmin)

admin.site.register(Item)
admin.site.register(Image, ImageInline)
admin.site.register(Favourite)
admin.site.register(Comment)
admin.site.register(Vote)
