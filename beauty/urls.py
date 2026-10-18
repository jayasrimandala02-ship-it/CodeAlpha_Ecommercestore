
from django.urls import path
from . import views

urlpatterns = [
    # Registration, sign-in and customer account
    path("", views.register, name="register"),
    path("register/", views.register, name="register_page"),
    path("sign-in/", views.signin, name="signin"),
    path("logout/", views.logout, name="logout"),
    path("home/", views.home, name="home"),
    path("profile/", views.profile, name="profile"),

    # Products and reviews
    path("products/", views.products, name="products"),
    path(
        "products/<str:product_id>/",
        views.product_detail,
        name="product_detail",
    ),
    path(
        "products/<str:product_id>/review/",
        views.add_review,
        name="add_review",
    ),

    # Shopping cart
    path("cart/", views.cart, name="cart"),
    path(
        "cart/add/<str:product_id>/",
        views.add_to_cart,
        name="add_to_cart",
    ),
    path(
        "cart/update/<str:cart_id>/",
        views.update_cart,
        name="update_cart",
    ),
    path(
        "cart/remove/<str:cart_id>/",
        views.remove_from_cart,
        name="remove_from_cart",
    ),

    # Checkout and payment
    path("checkout/", views.checkout, name="checkout"),
    path(
        "verify-payment/",
        views.verify_payment,
        name="verify_payment",
    ),
    path(
        "order-success/",
        views.order_success,
        name="order_success",
    ),

    # Orders
    path("my-orders/", views.my_orders, name="my_orders"),
    path(
        "view-order/<str:order_id>/",
        views.view_order,
        name="view_order",
    ),

    # Followers and following
    path("followers/", views.followers, name="followers"),
    path(
        "follow/<str:target_user_id>/",
        views.follow_user,
        name="follow_user",
    ),

    # Admin login and protected dashboard
    path("admin-login/", views.admin_login, name="admin_login"),
    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin_dashboard",
    ),
    path("admin-logout/", views.admin_logout, name="admin_logout"),
]

