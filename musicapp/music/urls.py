from . import views
from django.urls import path
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name="about"),
    path('artists/', views.ArtistsView.as_view(), name="artists"),
    path('albums/', views.AlbumsView.as_view(), name="albums"),
    path('playlist/', views.PlaylistView.as_view(), name="playlist"),
    path('premium/', views.PremiumView.as_view(), name="premium"),
    path('settings/', views.SettingsView.as_view(), name="settings"),
    path('office/', views.OfficeView.as_view(), name="office"),
    path('artist/<slug:slug>/', views.ArtistDetailView.as_view(), name='artist_detail'),
    path('song/<int:id>/', views.SongView.as_view(), name='song'),
    path('album/<int:id>/', views.AlbumDetailView.as_view(), name='album'),
    path('mix/<int:id>/', views.MixDetailView.as_view(), name='mix'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.LogInView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('add_to_favorites/<int:song_id>/', views.AddToFavoritesView.as_view(), name='add_to_favorites'),
]
