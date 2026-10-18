# VELOURA — Beauty E-Commerce Store

**Beauty, of your own aura.**

VELOURA is a beauty e-commerce web application developed using Django and MongoDB. It provides a platform for users to explore beauty products, view detailed product information, manage shopping carts, and place orders through a simple online shopping experience.

---

## Project Overview

The main objective of VELOURA is to provide an organized and user-friendly online beauty shopping experience. The application manages product information and customer-related data using MongoDB, while Django handles URL routing, views, and page rendering.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Django | Web framework |
| HTML5 | Web page structure |
| CSS3 | Styling and responsive layouts |
| MongoDB | Database |
| PyMongo | Django-to-MongoDB connection |
| Git and GitHub | Version control and project hosting |

## Features

- **User Authentication:** User registration and sign-in.
- **Product Catalogue:** Browse beauty products from different brands.
- **Product Details:** View product images, prices, descriptions, ingredients, benefits, and usage instructions.
- **Shopping Cart:** Add products, update quantities, and remove items.
- **Checkout:** Proceed through the order placement process.
- **Order Management:** Store and view order information where implemented.
- **Reviews and Ratings:** Submit and display product reviews where enabled.
- **User Profile:** Manage user information where implemented.
- **Payment Options:** UPI and Cash on Delivery, if enabled in the application.

## Project Structure

The following is a simplified representation of the Django project. The exact files and folders may vary based on the implementation.

```text
CodeAlpha_Ecommercestore/
│
├── manage.py
├── README.md
├── .gitignore
├── requirements.txt
│
├── veloura/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
└── beauty/
    ├── __init__.py
    ├── views.py
    ├── urls.py
    ├── db_connection.py
    │
    ├── templates/
    │   ├── register.html
    │   ├── signin.html
    │   ├── home.html
    │   ├── products.html
    │   ├── product_detail.html
    │   ├── cart.html
    │   ├── checkout.html
    │   ├── order_success.html
    │   ├── my_orders.html
    │   ├── view_order.html
    │   └── profile.html
    │
    └── static/
        ├── css/
        ├── images/
        └── js/
```

**Note:** This structure is illustrative. Keep only the files and folders that actually exist in your project; do not create missing files just to match this diagram.

## Database

VELOURA uses MongoDB to store application data. The development database is named `Beauty_store`.

The collections used in the application include:

- `Products` — beauty product information.
- `Users` — user account information.
- `Cart` — shopping cart data.
- `Orders` — customer order data.

The actual collections and fields depend on the application's implementation.

## Installation and Setup

### Prerequisites

- Python installed on your computer.
- MongoDB installed and running, or a configured MongoDB server.
- Git installed.
- Visual Studio Code or another code editor.

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/CodeAlpha_Ecommercestore.git
cd CodeAlpha_Ecommercestore
```

Replace `YOUR-USERNAME` with the actual GitHub username.

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

If `requirements.txt` is included:

```bash
pip install -r requirements.txt
```

### 4. Configure MongoDB

Make sure MongoDB is running and configure the connection using the appropriate project settings. Do not publish database passwords or other credentials.

### 5. Run the Development Server

From the folder containing `manage.py`, run:

```bash
python manage.py runserver
```

Open the following URL in your browser:

`http://127.0.0.1:8000/`

## Security

- Do not upload passwords, secret keys, or database credentials.
- Keep `.env` and local virtual environment folders out of version control.
- Use secure password handling and appropriate authentication checks.
- Use a properly configured production environment before deploying publicly.

## Project Purpose

VELOURA was developed as a learning and internship project to demonstrate web development using Python, Django, HTML, CSS, and MongoDB.

---

**Project Name:** VELOURA  
**Category:** Beauty E-Commerce Web Application  
**Backend:** Django (Python)  
**Database:** MongoDB  
**Repository:** CodeAlpha_Ecommercestore
