import os
import logging
from datetime import datetime
from collections import Counter

from bson import ObjectId
from bson.errors import InvalidId
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timezone as datetime_timezone
from zoneinfo import ZoneInfo

from .db_connection import (
    products_collection,
    users_collection,
    orders_collection,
    cart_collection,
    reviews_collection,
    followers_collection,
)


# =====================================================
# COMMON HELPER FUNCTIONS
# =====================================================

def get_current_user(request):
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    try:
        return users_collection.find_one({"_id": ObjectId(str(user_id))})
    except (InvalidId, TypeError, ValueError):
        return None


def require_customer(request):
    if not request.session.get("user_id"):
        messages.error(request, "Please sign in first.")
        return redirect("signin")
    return None


def get_product(product_id):
    try:
        return products_collection.find_one({"_id": ObjectId(str(product_id))})
    except (InvalidId, TypeError, ValueError):
        return None


def get_cart_items(user_id):
    """Return cart items in the format expected by cart.html."""
    records = list(cart_collection.find({"user_id": str(user_id)}))
    cart_items = []
    total = 0

    for record in records:
        product = get_product(record.get("product_id", ""))

        if not product:
            continue

        try:
            quantity = int(record.get("quantity", 1))
            price = float(product.get("price", 0) or 0)
        except (TypeError, ValueError):
            continue

        if quantity < 1 or price < 0:
            continue

        product["id"] = str(product["_id"])
        subtotal = price * quantity
        total += subtotal

        cart_items.append({
            "cart_id": str(record["_id"]),
            "id": str(record["_id"]),
            "product_id": str(product["_id"]),
            "product": product,
            "quantity": quantity,
            "price": price,
            "subtotal": round(subtotal, 2),
            "name": product.get("name", "Beauty Product"),
            "brand": product.get("brand", ""),
            "image_url": product.get("image_url", ""),
        })

    return cart_items, round(total, 2)


# =====================================================
# REGISTER
# =====================================================

def register(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not full_name or not password or not confirm_password:
            messages.error(request, "Please fill in all fields.")

        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")

        elif len(password) < 8:
            messages.error(
                request,
                "Password must contain at least 8 characters."
            )

        elif users_collection.find_one({"full_name": full_name}):
            messages.error(
                request,
                "This name is already registered. Please sign in."
            )

        else:
            users_collection.insert_one({
                "full_name": full_name,
                "password": make_password(password),
            })
            messages.success(
                request,
                "Registration successful. Please sign in."
            )
            return redirect("signin")

    return render(request, "register.html")


# =====================================================
# SIGN IN AND LOGOUT
# =====================================================

def signin(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        password = request.POST.get("password", "")

        user = users_collection.find_one({"full_name": full_name})

        if user and check_password(password, user.get("password", "")):
            request.session.flush()
            request.session["user_id"] = str(user["_id"])
            request.session["full_name"] = user.get("full_name", "")
            request.session.set_expiry(60 * 60 * 24 * 7)
            return redirect("home")

        messages.error(request, "Invalid name or password.")

    return render(request, "signin.html")


def logout(request):
    request.session.flush()
    messages.success(request, "You have signed out.")
    return redirect("signin")


# =====================================================
# HOME
# =====================================================

def home(request):
    featured_products = list(
        products_collection.find({"is_active": True}).limit(8)
    )

    for product in featured_products:
        product["id"] = str(product["_id"])

    return render(request, "home.html", {
        "products": featured_products,
        "full_name": request.session.get("full_name", ""),
    })


# =====================================================
# PRODUCTS
# =====================================================

def products(request):
    search_query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    query = {"is_active": True}

    if search_query:
        query["$or"] = [
            {"name": {"$regex": search_query, "$options": "i"}},
            {"brand": {"$regex": search_query, "$options": "i"}},
            {"description": {"$regex": search_query, "$options": "i"}},
        ]

    if category:
        query["category"] = category

    product_list = list(products_collection.find(query))

    for product in product_list:
        product["id"] = str(product["_id"])

    categories = products_collection.distinct(
        "category",
        {"is_active": True},
    )

    return render(request, "products.html", {
        "products": product_list,
        "categories": categories,
        "search_query": search_query,
        "selected_category": category,
    })


# =====================================================
# PRODUCT DETAILS
# =====================================================


def product_detail(request, product_id):
    product = get_product(product_id)

    if not product or not product.get("is_active", True):
        messages.error(request, "Product not found.")
        return redirect("products")

    product["id"] = str(product["_id"])

    # Fetch all reviews for this product
    reviews = list(
        reviews_collection.find({
            "product_id": str(product["_id"])
        }).sort("_id", -1)
    )

    # Prepare reviews for the HTML template
    for review in reviews:
        review["id"] = str(review["_id"])
        review["user_name"] = (
            review.get("user_name")
            or review.get("full_name")
            or "Customer"
        )
        review["comment"] = (
            review.get("comment")
            or review.get("review_text")
            or ""
        )

    # Calculate average rating
    ratings = [
        int(review["rating"])
        for review in reviews
        if str(review.get("rating", "")).isdigit()
        and 1 <= int(review["rating"]) <= 5
    ]

    review_count = len(ratings)
    average_rating = (
        round(sum(ratings) / review_count, 1)
        if review_count
        else 0
    )

    # Find the current user's existing review
    user_id = request.session.get("user_id")
    full_name = request.session.get("full_name", "")
    existing_review = None

    if user_id:
        existing_review = reviews_collection.find_one({
            "product_id": str(product["_id"]),
            "user_id": str(user_id),
        })

        if existing_review:
            existing_review["comment"] = (
                existing_review.get("comment")
                or existing_review.get("review_text")
                or ""
            )

    return render(request, "product_detail.html", {
        "product": product,
        "reviews": reviews,
        "full_name": full_name,
        "existing_review": existing_review,
        "average_rating": average_rating,
        "review_count": review_count,
    })

# =====================================================
# PRODUCT REVIEWS
# =====================================================


def add_review(request, product_id):
    login_redirect = require_customer(request)
    if login_redirect:
        return login_redirect

    if request.method != "POST":
        return redirect(
            "product_detail",
            product_id=product_id,
        )

    product = get_product(product_id)

    if not product or not product.get("is_active", True):
        messages.error(request, "Product not found.")
        return redirect("products")

    # Read the exact field names sent by product_detail.html
    comment = request.POST.get("comment", "").strip()
    rating_text = request.POST.get("rating", "").strip()

    try:
        rating = int(rating_text)
    except (TypeError, ValueError):
        rating = 0

    if not comment:
        messages.error(request, "Please write your review.")
        return redirect("product_detail", product_id=product_id)

    if len(comment) > 1000:
        messages.error(
            request,
            "Review must be 1000 characters or fewer.",
        )
        return redirect("product_detail", product_id=product_id)

    if rating < 1 or rating > 5:
        messages.error(
            request,
            "Please select a rating from 1 to 5.",
        )
        return redirect("product_detail", product_id=product_id)

    user_id = str(request.session.get("user_id", ""))
    full_name = request.session.get("full_name", "Customer")

    if not user_id:
        messages.error(request, "Please sign in to submit a review.")
        return redirect("signin")

    product_id_string = str(product["_id"])

    review_data = {
        "product_id": product_id_string,
        "user_id": user_id,
        "user_name": full_name,
        "rating": rating,
        "comment": comment,
        "created_at": datetime.now(),
    }

    # Update this user's review if one already exists;
    # otherwise insert a new review.
    existing_review = reviews_collection.find_one({
        "product_id": product_id_string,
        "user_id": user_id,
    })
    

    if existing_review:
        reviews_collection.update_one(
            {"_id": existing_review["_id"]},
            {"$set": review_data},
        )
        messages.success(
            request,
            "Your review has been updated!",
        )
    else:
        reviews_collection.insert_one(review_data)
        messages.success(
            request,
            "Your review was submitted successfully!",
        )

    return redirect(
        "product_detail",
        product_id=product_id,
    )




# =====================================================
# ADD TO CART
# =====================================================

def add_to_cart(request, product_id):
    login_redirect = require_customer(request)

    if login_redirect:
        return login_redirect

    if request.method != "POST":
        return redirect("products")

    product = get_product(product_id)

    if not product or not product.get("is_active", True):
        messages.error(request, "This product is not available.")
        return redirect("products")

    user_id = str(request.session["user_id"])
    product_id = str(product["_id"])

    existing = cart_collection.find_one({
        "user_id": user_id,
        "product_id": product_id,
    })

    if existing:
        try:
            quantity = int(existing.get("quantity", 1))
        except (TypeError, ValueError):
            quantity = 1

        if quantity >= 99:
            messages.error(request, "Maximum quantity is 99.")
        else:
            cart_collection.update_one(
                {"_id": existing["_id"], "user_id": user_id},
                {"$set": {"quantity": quantity + 1}},
            )
            messages.success(request, "Cart quantity updated.")
    else:
        cart_collection.insert_one({
            "user_id": user_id,
            "product_id": product_id,
            "quantity": 1,
        })
        messages.success(request, "Product added to your cart.")

    return redirect("cart")


# =====================================================
# SHOPPING CART
# =====================================================

def cart(request):
    login_redirect = require_customer(request)

    if login_redirect:
        return login_redirect

    user_id = str(request.session["user_id"])
    cart_items, total = get_cart_items(user_id)

    return render(request, "cart.html", {
        "cart_items": cart_items,
        "items": cart_items,
        "total": total,
        "cart_total": total,
    })


def update_cart(request, cart_id):
    login_redirect = require_customer(request)

    if login_redirect:
        return login_redirect

    if request.method != "POST":
        return redirect("cart")

    try:
        cart_object_id = ObjectId(cart_id)
    except (InvalidId, TypeError, ValueError):
        messages.error(request, "Invalid cart item.")
        return redirect("cart")

    user_id = str(request.session["user_id"])

    item = cart_collection.find_one({
        "_id": cart_object_id,
        "user_id": user_id,
    })

    if not item:
        messages.error(request, "Cart item not found.")
        return redirect("cart")

    try:
        quantity = int(request.POST.get("quantity", "1"))
    except (TypeError, ValueError):
        quantity = 0

    if quantity < 1 or quantity > 99:
        messages.error(request, "Quantity must be between 1 and 99.")
    else:
        cart_collection.update_one(
            {"_id": cart_object_id, "user_id": user_id},
            {"$set": {"quantity": quantity}},
        )
        messages.success(request, "Cart updated.")

    return redirect("cart")


def remove_from_cart(request, cart_id):
    login_redirect = require_customer(request)

    if login_redirect:
        return login_redirect

    if request.method != "POST":
        return redirect("cart")

    try:
        cart_object_id = ObjectId(cart_id)
    except (InvalidId, TypeError, ValueError):
        messages.error(request, "Invalid cart item.")
        return redirect("cart")

    result = cart_collection.delete_one({
        "_id": cart_object_id,
        "user_id": str(request.session["user_id"]),
    })

    if result.deleted_count:
        messages.success(request, "Item removed from your cart.")
    else:
        messages.error(request, "Cart item not found.")

    return redirect("cart")


# =====================================================
# CHECKOUT
# =====================================================

def checkout(request):
    login_redirect = require_customer(request)

    if login_redirect:
        return login_redirect

    user_id = str(request.session["user_id"])
    cart_items, total = get_cart_items(user_id)

    if not cart_items:
        messages.error(request, "Your shopping cart is empty.")
        return redirect("cart")

    if request.method == "POST":
        full_name = (
            request.POST.get("full_name", "").strip()
            or request.POST.get("customer_name", "").strip()
            or request.session.get("full_name", "").strip()
        )

        phone = request.POST.get("phone", "").strip()

        address = (
            request.POST.get("address", "").strip()
            or request.POST.get("delivery_address", "").strip()
        )

        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        pincode = request.POST.get("pincode", "").strip()

        payment_method = (
            request.POST.get("payment_method", "COD").strip().upper()
        )

        if payment_method in ("UPI", "UPI_TEST"):
            messages.error(
                request,
                "Currently, only Cash on Delivery (COD) is available. "
                "Please select COD."
            )

        elif payment_method != "COD":
            messages.error(
                request,
                "Please select Cash on Delivery (COD)."
            )

        elif not full_name:
            messages.error(request, "Please enter your full name.")

        elif not address:
            messages.error(request, "Please enter your delivery address.")

        elif not phone.isdigit() or len(phone) != 10:
            messages.error(
                request,
                "Please enter a valid 10-digit phone number."
            )

        elif pincode and (
            not pincode.isdigit() or len(pincode) != 6
        ):
            messages.error(
                request,
                "Please enter a valid 6-digit PIN code."
            )

        else:
            cart_items, total = get_cart_items(user_id)

            if not cart_items:
                messages.error(request, "Your shopping cart is empty.")
                return redirect("cart")

            order_items = []

            for item in cart_items:
                product = item["product"]

                order_items.append({
                    "product_id": item["product_id"],
                    "name": product.get("name", "Beauty Product"),
                    "brand": product.get("brand", ""),
                    "image_url": product.get("image_url", ""),
                    "price": item["price"],
                    "quantity": item["quantity"],
                    "subtotal": item["subtotal"],
                })

            now = timezone.now()

            order = {
                "user_id": user_id,
                "customer_name": full_name,
                "phone": phone,
                "delivery_address": {
                    "full_name": full_name,
                    "phone": phone,
                    "address": address,
                    "city": city,
                    "state": state,
                    "pincode": pincode,
                },
                "items": order_items,
                "total": total,
                "payment_method": "COD",
                "payment_status": "Pending - Pay on Delivery",
                "order_status": "Placed",
                "order_date": now,
                "created_at": now,
            }

            try:
                result = orders_collection.insert_one(order)

                cart_collection.delete_many({
                    "user_id": user_id
                })

                request.session["last_order_id"] = str(
                    result.inserted_id
                )

                messages.success(
                    request,
                    "Your COD order has been placed successfully!"
                )

                return redirect("order_success")

            except Exception:
                messages.error(
                    request,
                    "We could not save your order. Please try again."
                )

    cart_items, total = get_cart_items(user_id)

    if not cart_items:
        messages.error(request, "Your shopping cart is empty.")
        return redirect("cart")

    return render(request, "checkout.html", {
        "cart_items": cart_items,
        "items": cart_items,
        "total": total,
        "cart_total": total,
        "full_name": request.session.get("full_name", ""),
        "upi_payment_ready": False,
        "upi_unavailable": True,
    })


def verify_payment(request):
    """Online payment is not configured; never mark an order as paid here."""
    messages.error(
        request,
        "UPI payment is currently unavailable. "
        "Please choose Cash on Delivery (COD)."
    )
    return redirect("checkout")


# =====================================================
# ORDER SUCCESS
# =====================================================


def order_success(request):
    login_redirect = require_customer(request)

    if login_redirect:
        return login_redirect

    order = None
    order_id = request.session.get("last_order_id")

    if order_id:
        try:
            order = orders_collection.find_one({
                "_id": ObjectId(order_id),
                "user_id": str(request.session["user_id"]),
            })
        except (InvalidId, TypeError, ValueError):
            order = None

    if order:
        order["id"] = str(order["_id"])

        # Convert MongoDB order datetime to the correct local timezone
        order_datetime = order.get("order_date") or order.get("created_at")

        if order_datetime:
            from datetime import timezone as datetime_timezone
            from zoneinfo import ZoneInfo

            # PyMongo may return a naive datetime representing UTC
            if order_datetime.tzinfo is None:
                order_datetime = order_datetime.replace(
                    tzinfo=datetime_timezone.utc
                )

            order["display_order_date"] = order_datetime.astimezone(
                ZoneInfo("Asia/Kolkata")
            )

    return render(
        request,
        "order_success.html",
        {"order": order, "order_id": order_id},
    )

# =====================================================
# MY ORDERS
# =====================================================

def add_order_display_datetime(order):
    """Prepare an order datetime for display in Indian Standard Time."""
    order_datetime = order.get("order_date") or order.get("created_at")

    if order_datetime:
        # PyMongo returns naive datetimes as UTC by default.
        if order_datetime.tzinfo is None:
            order_datetime = order_datetime.replace(
                tzinfo=datetime_timezone.utc
            )

        order["display_order_date"] = order_datetime.astimezone(
            ZoneInfo("Asia/Kolkata")
        )

    return order

def my_orders(request):
    login_redirect = require_customer(request)

    if login_redirect:
        return login_redirect

    order_list = list(
        orders_collection.find({
            "user_id": str(request.session["user_id"])
        }).sort("_id", -1)
    )

    for order in order_list:
        order["id"] = str(order["_id"])

        order_datetime = (
            order.get("order_date") or order.get("created_at")
        )

        if order_datetime:
            # MongoDB/PyMongo naive datetime values are treated as UTC.
            if order_datetime.tzinfo is None:
                order_datetime = order_datetime.replace(
                    tzinfo=datetime_timezone.utc
                )

            order["display_order_date"] = order_datetime.astimezone(
                ZoneInfo("Asia/Kolkata")
            )

    return render(
        request,
        "my_orders.html",
        {
            "orders": order_list,
            "order_list": order_list,
        },
    )




# =====================================================
# VIEW ORDER
# =====================================================

def view_order(request, order_id):
    login_redirect = require_customer(request)

    if login_redirect:
        return login_redirect

    try:
        order = orders_collection.find_one({
            "_id": ObjectId(order_id),
            "user_id": str(request.session["user_id"]),
        })
    except (InvalidId, TypeError, ValueError):
        order = None

    if not order:
        messages.error(request, "Order not found.")
        return redirect("my_orders")

    order["id"] = str(order["_id"])

    delivery = order.get("delivery_address", {})

    if not isinstance(delivery, dict):
        delivery = {"address": str(delivery)}

    order["delivery"] = delivery

    order.setdefault("order_status", "Placed")
    order.setdefault("payment_method", "COD")
    order.setdefault("payment_status", "Pending")
    order.setdefault("items", [])
    order.setdefault("total", 0)

    return render(request, "view_order.html", {
        "order": order,
        "delivery": delivery,
        "order_id": order["id"],
    })


# =====================================================
# CUSTOMER PROFILE
# =====================================================

def profile(request):
    login_redirect = require_customer(request)

    if login_redirect:
        return login_redirect

    user = get_current_user(request)

    if not user:
        request.session.flush()
        messages.error(request, "Please sign in again.")
        return redirect("signin")

    user["id"] = str(user["_id"])

    return render(request, "profile.html", {
        "profile": user,
        "user": user,
    })


# =====================================================
# FOLLOWERS
# =====================================================

def follow_user(request, target_user_id):
    login_redirect = require_customer(request)

    if login_redirect:
        return login_redirect

    if request.method != "POST":
        return redirect("followers")

    current_user_id = str(request.session["user_id"])

    try:
        target_object_id = ObjectId(target_user_id)
    except (InvalidId, TypeError, ValueError):
        messages.error(request, "Invalid user.")
        return redirect("followers")

    target_user = users_collection.find_one({
        "_id": target_object_id
    })

    if not target_user:
        messages.error(request, "User not found.")
        return redirect("followers")

    if current_user_id == target_user_id:
        messages.error(request, "You cannot follow yourself.")
        return redirect("followers")

    existing = followers_collection.find_one({
        "follower_id": current_user_id,
        "following_id": target_user_id,
    })

    if existing:
        followers_collection.delete_one({
            "_id": existing["_id"]
        })
        messages.success(request, "You unfollowed this user.")
    else:
        followers_collection.insert_one({
            "follower_id": current_user_id,
            "following_id": target_user_id,
        })
        messages.success(request, "You are now following this user.")

    return redirect("followers")


def followers(request):
    login_redirect = require_customer(request)

    if login_redirect:
        return login_redirect

    current_user_id = str(request.session["user_id"])

    following_records = list(
        followers_collection.find({
            "follower_id": current_user_id
        })
    )

    following_users = []

    for record in following_records:
        try:
            user = users_collection.find_one({
                "_id": ObjectId(record["following_id"])
            })
        except (InvalidId, KeyError, TypeError, ValueError):
            user = None

        if user:
            following_users.append({
                "id": str(user["_id"]),
                "full_name": user.get("full_name", "Customer"),
            })

    try:
        current_object_id = ObjectId(current_user_id)
    except (InvalidId, TypeError, ValueError):
        request.session.flush()
        messages.error(request, "Please sign in again.")
        return redirect("signin")

    other_users = list(
        users_collection.find(
            {"_id": {"$ne": current_object_id}},
            {"full_name": 1},
        ).limit(100)
    )

    for user in other_users:
        user["id"] = str(user["_id"])

    return render(request, "followers.html", {
        "following_users": following_users,
        "other_users": other_users,
    })


# =====================================================
# ADMIN LOGIN
# =====================================================

def admin_login(request):
    if request.session.get("is_veloura_admin") is True:
        return redirect("admin_dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        expected_username = os.getenv("VELOURA_ADMIN_USERNAME")
        expected_password = os.getenv("VELOURA_ADMIN_PASSWORD")

        if not expected_username:
            messages.error(
                request,
                "Admin username is missing. Restart Django from the configured terminal."
            )
        elif not expected_password:
            messages.error(
                request,
                "Admin password is missing. Restart Django from the configured terminal."
            )
        elif (
            username == expected_username
            and password == expected_password
        ):
            request.session.flush()
            request.session["is_veloura_admin"] = True
            request.session["veloura_admin_username"] = username
            request.session.set_expiry(3600)

            return redirect("admin_dashboard")
        else:
            messages.error(
                request,
                "Invalid admin username or password."
            )

    return render(request, "admin_login.html")
# =====================================================
# ADMIN DASHBOARD WITH GRAPHS
# =====================================================

def admin_dashboard(request):
    if request.session.get("is_veloura_admin") is not True:
        messages.error(request, "Please log in as admin first.")
        return redirect("admin_login")

    # -------------------------------------------------
    # RECENT PRODUCTS - LATEST 100
    # -------------------------------------------------
    recent_products = list(
        products_collection.find(
            {},
            {
                "name": 1,
                "brand": 1,
                "price": 1,
                "is_active": 1,
            },
        ).sort("_id", -1).limit(100)
    )

    for product in recent_products:
        product["id"] = str(product["_id"])

        try:
            product["price"] = float(
                product.get("price", 0) or 0
            )
        except (TypeError, ValueError):
            product["price"] = 0

    # -------------------------------------------------
    # ORDER STATISTICS
    # -------------------------------------------------
    all_orders = list(orders_collection.find({}))

    sales_total = 0.0
    cod_orders = 0
    pending_orders = 0

    for saved_order in all_orders:
        try:
            sales_total += float(
                saved_order.get("total", 0) or 0
            )
        except (TypeError, ValueError):
            pass

        if str(
            saved_order.get("payment_method", "")
        ).upper() == "COD":
            cod_orders += 1

        if "pending" in str(
            saved_order.get("payment_status", "")
        ).lower():
            pending_orders += 1

    # -------------------------------------------------
    # DASHBOARD COUNTS
    # -------------------------------------------------
    total_products = products_collection.count_documents({})
    active_products = products_collection.count_documents({
        "is_active": True
    })
    total_users = users_collection.count_documents({})
    total_orders = orders_collection.count_documents({})
    total_cart_items = cart_collection.count_documents({})

    # -------------------------------------------------
    # GRAPH 1: MONTHLY SALES - LAST 6 MONTHS
    # -------------------------------------------------
    now = timezone.now()
    month_dates = []

    for offset in range(5, -1, -1):
        month_number = now.month - offset
        year = now.year

        while month_number <= 0:
            month_number += 12
            year -= 1

        month_dates.append((year, month_number))

    monthly_sales_labels = [
        datetime(year, month, 1).strftime("%b %Y")
        for year, month in month_dates
    ]

    monthly_sales_values = [0.0] * 6

    month_index = {
        (year, month): index
        for index, (year, month) in enumerate(month_dates)
    }

    for order in all_orders:
        order_date = (
            order.get("order_date")
            or order.get("created_at")
        )

        if not isinstance(order_date, datetime):
            continue

        key = (order_date.year, order_date.month)

        if key not in month_index:
            continue

        try:
            amount = float(order.get("total", 0) or 0)
        except (TypeError, ValueError):
            amount = 0

        monthly_sales_values[month_index[key]] += amount

    monthly_sales_values = [
        round(value, 2)
        for value in monthly_sales_values
    ]

    # -------------------------------------------------
    # GRAPH 2: ORDER STATUS + PAYMENT STATUS
    # -------------------------------------------------
    status_counter = Counter()

    for order in all_orders:
        order_status = str(
            order.get("order_status", "Unknown")
        ).strip()

        status_counter[order_status or "Unknown"] += 1

        payment_status = str(
            order.get("payment_status", "Pending")
        ).strip()

        payment_status = payment_status or "Pending"

        status_counter[
            f"Payment {payment_status}"
        ] += 1

    order_status_labels = list(status_counter.keys())
    order_status_values = list(status_counter.values())

    if not order_status_labels:
        order_status_labels = ["No Orders"]
        order_status_values = [0]

    # -------------------------------------------------
    # GRAPH 3: BEST-SELLING PRODUCTS
    # -------------------------------------------------
    product_quantities = Counter()

    for order in all_orders:
        items = order.get("items", [])

        if not isinstance(items, list):
            continue

        for item in items:
            if not isinstance(item, dict):
                continue

            name = str(
                item.get("name", "Beauty Product")
            )

            try:
                quantity = int(
                    item.get("quantity", 0) or 0
                )
            except (TypeError, ValueError):
                quantity = 0

            if quantity > 0:
                product_quantities[name] += quantity

    best_selling = product_quantities.most_common(10)

    best_selling_labels = [
        name for name, quantity in best_selling
    ]

    best_selling_values = [
        quantity for name, quantity in best_selling
    ]

    if not best_selling_labels:
        best_selling_labels = ["No Sales Yet"]
        best_selling_values = [0]

    # -------------------------------------------------
    # SEND DATA TO TEMPLATE
    # -------------------------------------------------
    context = {
        "admin_username": request.session.get(
            "veloura_admin_username", "Admin"
        ),
        "total_products": total_products,
        "active_products": active_products,
        "total_users": total_users,
        "total_orders": total_orders,
        "total_cart_items": total_cart_items,
        "recent_products": recent_products,
        "sales_total": round(sales_total, 2),
        "cod_orders": cod_orders,
        "pending_orders": pending_orders,
        "monthly_sales_labels": monthly_sales_labels,
        "monthly_sales_values": monthly_sales_values,
        "order_status_labels": order_status_labels,
        "order_status_values": order_status_values,
        "best_selling_labels": best_selling_labels,
        "best_selling_values": best_selling_values,
    }

    return render(
        request,
        "admin_dashboard.html",
        context,
    )

# =====================================================
# ADMIN LOGOUT
# =====================================================

def admin_logout(request):
    if request.session.get("is_veloura_admin") is not True:
        return redirect("admin_login")

    request.session.flush()
    messages.success(
        request,
        "Admin signed out successfully."
    )
    return redirect("admin_login")
