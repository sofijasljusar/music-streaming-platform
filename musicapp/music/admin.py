from django.contrib import admin
from .utils import get_image_preview
from .templatetags.custom_filters import format_duration

from .models import Artist, ArtistAlbum, Song, PlatformMix, UserPlaylist, UserPlaylistSong, Genre


class SongCollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'image_preview_list', 'get_total_duration', 'get_amount_of_songs']
    readonly_fields = ('image_preview_detail',)

    @admin.display(description="Image")
    def image_preview_list(self, obj):
        return get_image_preview(obj, 50)

    @admin.display(description="Image Preview")
    def image_preview_detail(self, obj):
        return get_image_preview(obj, 500)

    @admin.display(description="Total Duration")
    def get_total_duration(self, obj):
        return format_duration(obj.get_total_duration())

    @admin.display(description="Number of Songs")
    def get_amount_of_songs(self, obj):
        return obj.get_amount_of_songs()


class SongAdmin(admin.ModelAdmin):
    list_display = ['name', 'image_preview_list', 'release_date', 'album', 'duration']
    readonly_fields = ('image_preview_detail',)

    @admin.display(description="Image")
    def image_preview_list(self, obj):
        return get_image_preview(obj, 50)

    @admin.display(description="Image Preview")
    def image_preview_detail(self, obj):
        return get_image_preview(obj, 500)


class ArtistAlbumInline(admin.TabularInline):
    model = ArtistAlbum
    extra = 0


class ArtistAdmin(admin.ModelAdmin):
    inlines = [ArtistAlbumInline]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        artist = self.get_object(request, object_id)
        songs = Song.objects.filter(artists=artist)

        if extra_context is None:
            extra_context = {}
        extra_context['songs'] = songs

        return super().change_view(request, object_id, form_url, extra_context=extra_context)


class ArtistAlbumAdmin(SongCollectionAdmin):
    list_display = SongCollectionAdmin.list_display + ['owner', 'release_date', "songs_preview"]

    @admin.display(description="Songs")
    def songs_preview(self, obj):
        return ", ".join(obj.songs.values_list("name", flat=True)[:5])


class UserPlaylistSongInline(admin.TabularInline):
    model = UserPlaylistSong
    extra = 0
    fields = ['song']


class UserPlaylistAdmin(SongCollectionAdmin):
    inlines = [UserPlaylistSongInline]
    list_display = SongCollectionAdmin.list_display + ['owner']


class PlatformMixAdmin(SongCollectionAdmin):
    list_display = SongCollectionAdmin.list_display + ['owner']


admin.site.register(Artist, ArtistAdmin)
admin.site.register(ArtistAlbum, ArtistAlbumAdmin)
admin.site.register(Song, SongAdmin)
admin.site.register(PlatformMix, PlatformMixAdmin)
admin.site.register(UserPlaylist, UserPlaylistAdmin)
admin.site.register(Genre)

