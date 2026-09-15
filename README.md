# **Vibely – Social Media Platform**

Vibely is a full-stack social media web application developed as part of the CodeAlpha Full Stack Development Internship.
It provides a simple and interactive platform where users can create profiles, connect with other users, share posts and stories, and interact through likes, comments, follows, and notifications.

## 🚀 **Features**

👤 **User Authentication**

- User registration and login
- Secure password authentication
- Separate user sessions
- Automatic profile creation

👥 **User Profiles**

- Profile picture and display name
- Bio
- View user's posts
- Followers and following counts
- Follow and unfollow users
- View other users' profiles

🔍 **Search**

- Search for users by username or name
- Case-insensitive and partial search
- Open a user's profile directly from search results

📝 **Posts**

- Create posts with captions
- Upload images or videos
- Like and unlike posts
- Add comments
- Delete your own posts
- Posts are stored in the database

📖 **Stories**

- Create image or video stories
- Stories automatically expire after 24 hours
- View stories from connected users
- Like and reply to stories
- Story views are recorded
- Story owners can view story insights
- Story owners can delete their stories

🔔 **Notifications**

Users receive notifications for:

- New followers
- Post likes
- Post comments
- Story likes
- Story replies

📱 **Responsive Design**

- Desktop-friendly interface
- Mobile-friendly layout
- Responsive navigation
- Clean and modern social-media-style UI

## 🛠️ **Technologies Used**

- Python
- Django
- HTML5
- CSS3
- JavaScript
- SQLite
- Pillow

## 📂 **Project Structure**

Vibely/
│
├── manage.py
├── requirements.txt
├── .gitignore
├── README.md
│
├── vibely/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── social/
│   ├── __init__.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
│
├── templates/
│
└── static/
    ├── css/
    ├── img/
    └── js/

## ⚙️ **Installation and Setup**

**1. Clone the repository**

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd CodeAlpha_SocialMediaPlatform-Vibely

**2. Create a virtual environment**

python -m venv venv

**3. Activate the virtual environment**

Windows PowerShell:

.\venv\Scripts\Activate.ps1

**4. Install dependencies**

pip install -r requirements.txt

**5. Apply database migrations**

python manage.py migrate

**6. Start the development server**

python manage.py runserver

**7. Open Vibely**

Open the local server URL shown in the terminal, usually:

http://127.0.0.1:8000/

## 🔐 **Security**

Sensitive files and local development files such as the following are excluded from the repository:

.env
venv/
.venv/
db.sqlite3
media/
__pycache__/

API keys, passwords, and other private credentials should never be committed to GitHub.

## 🎯 **Internship Project**

**Internship:** CodeAlpha Full Stack Development Internship

**Project:** Social Media Platform

**Application Name:** Vibely(An application where you share your vibe and connect with others.)

Vibely was developed to demonstrate full-stack web development concepts including user authentication, database management, social interactions, media uploads, responsive UI design, and dynamic web functionality.

## 👩‍💻 **Developed By**

**Ranjani Pullati**

⭐ If you find this project interesting, feel free to explore the repository and its features.
