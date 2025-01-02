from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('category/<str:food>/', views.category_view, name='category_view'),
    path('cart/', views.cart_view, name='cart_view'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update_cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('search_view/', views.search_view, name='search_view'),
    path('add_shipping_address/', views.add_shipping_address, name='add_shipping_address'),
    path('shipping_address_list/', views.shipping_address_list, name='shipping_address_list'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('remove_from_wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('payment/success/<int:product_id>/', views.payment_success, name='payment_success'),
    path('paypal-ipn/', views.paypal_ipn, name='paypal_ipn'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('checkout/<int:product_id>/', views.checkout, name='checkout'),  # Added the corrected pattern here

    


]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
