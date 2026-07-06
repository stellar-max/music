markdown
# 🎵 SimpleWebPlayer

<div align="center">

![SimpleWebPlayer Logo](https://img.shields.io/badge/SimpleWebPlayer-Music_Player-6C63FF?style=for-the-badge&logo=music&logoColor=white)
![Version](https://img.shields.io/badge/version-1.0.0-blue?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11+-green?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/flask-2.3+-red?style=flat-square&logo=flask)
![License](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)
![Socket.IO](https://img.shields.io/badge/Socket.IO-Realtime-010101?style=flat-square&logo=socket.io)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=flat-square&logo=telegram)

**A modern, self-hosted music streaming web app with real-time collaborative rooms, synchronized LRC lyrics, and Telegram bot integration.**

[![Deploy to Render](https://img.shields.io/badge/🚀-Deploy_to_Render-46C3C8?style=for-the-badge&logo=render)](https://render.com/deploy)
[![Deploy to Heroku](https://img.shields.io/badge/🚀-Deploy_to_Heroku-430098?style=for-the-badge&logo=heroku)](https://heroku.com/deploy)
[![Deploy to Vercel](https://img.shields.io/badge/🚀-Deploy_to_Vercel-000000?style=for-the-badge&logo=vercel)](https://vercel.com/new/clone)
[![Docker Pulls](https://img.shields.io/badge/🐳-Docker_Hub-2496ED?style=for-the-badge&logo=docker)](https://hub.docker.com/r/simplewebplayer)

</div>

---

## 📸 **Screenshots**

### 🏠 **Main Library View**
<div align="center">
  <img src="https://via.placeholder.com/800x400/1a1a2e/6C63FF?text=SimpleWebPlayer+Main+Library" alt="Main Library" width="800">
  <br>
  <em>Browse tracks and albums with a modern, dark UI</em>
</div>

### 🎵 **Player View with Lyrics**
<div align="center">
  <img src="https://via.placeholder.com/800x400/1a1a2e/FF6B6B?text=Player+with+Lyrics+Sync" alt="Player" width="800">
  <br>
  <em>Beautiful player with synchronized lyrics highlighting</em>
</div>

### 👥 **Collaborative Rooms**
<div align="center">
  <img src="https://via.placeholder.com/800x400/1a1a2e/6C63FF?text=Collaborative+Rooms" alt="Rooms" width="800">
  <br>
  <em>Create and join listening rooms with friends</em>
</div>

### 🤖 **Telegram Bot**
<div align="center">
  <img src="https://via.placeholder.com/400x600/1a1a2e/6C63FF?text=Telegram+Bot" alt="Telegram Bot" width="400">
  <br>
  <em>Control playback and join rooms from Telegram</em>
</div>

### 📱 **Mobile View**
<div align="center">
  <img src="https://via.placeholder.com/400x800/1a1a2e/6C63FF?text=Mobile+View" alt="Mobile View" width="400">
  <br>
  <em>Fully responsive design that works on all devices</em>
</div>

### ⚙️ **Admin Panel**
<div align="center">
  <img src="https://via.placeholder.com/800x400/1a1a2e/6C63FF?text=Admin+Panel" alt="Admin Panel" width="800">
  <br>
  <em>Manage tracks, albums, and users with ease</em>
</div>

### 🎨 **Player Controls**
<div align="center">
  <img src="https://via.placeholder.com/800x200/1a1a2e/6C63FF?text=Player+Controls" alt="Player Controls" width="800">
  <br>
  <em>Intuitive player controls with volume, progress, and playback options</em>
</div>

---

## ✨ **Features**

### 🎵 **Core Music Features**
- ✅ **MP3 Upload & Streaming** - Upload and stream your music files
- ✅ **LRC Lyrics Sync** - Real-time line-by-line lyrics highlighting
- ✅ **Cover Art Support** - Automatic extraction from MP3 files
- ✅ **Metadata Editor** - Edit title, artist, album, year
- ✅ **Album Management** - Create and organize albums with cover art
- ✅ **Playlist Support** - Create and manage custom playlists
- ✅ **Search Functionality** - Search tracks, albums, and artists

### 👥 **Collaborative Features**
- ✅ **Real-time Rooms** - Create collaborative listening rooms
- ✅ **Shared Queue** - Add and manage songs together
- ✅ **Playback Sync** - Everyone hears the same moment
- ✅ **Room Member Management** - See who's listening
- ✅ **Skip Voting** - Democratic song skipping
- ✅ **Room Invites** - Share room links with friends

### 🤖 **Telegram Integration**
- ✅ **Bot Login** - Quick authentication via Telegram
- ✅ **Remote Control** - Play songs from Telegram
- ✅ **Deep Linking** - Open web player directly from bot
- ✅ **Room Management** - Create/join rooms via Telegram
- ✅ **Playlist Sharing** - Share playlists via Telegram
- ✅ **Notifications** - Get notified about room activities

### 🎨 **Premium UI**
- ✅ **Modern Design** - Clean and intuitive interface
- ✅ **Mobile-First** - Fully responsive on all devices
- ✅ **Dark Theme** - AMOLED-friendly design
- ✅ **Animations** - Smooth transitions and interactions
- ✅ **Keyboard Shortcuts** - Control playback with keyboard
- ✅ **Touch Gestures** - Swipe controls for mobile

### 🔐 **Admin Panel**
- ✅ Track Management - Hide/delete tracks
- ✅ Album Management - Hide/delete albums
- ✅ User Management - View and manage users
- ✅ Pin Featured Content - Highlight important tracks/albums
- ✅ Analytics Dashboard - View usage statistics
- ✅ Content Moderation - Moderate user content

---

## 🛠️ **Local Setup**

### 📋 **Prerequisites**

Before you begin, ensure you have the following installed:

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| **Python** | 3.11+ | `python --version` |
| **pip** | Latest | `pip --version` |
| **Git** | Latest | `git --version` |
| **SQLite** | 3.x | `sqlite3 --version` |

### 📥 **Installation Steps**

#### **Step 1: Clone the Repository**
```bash
# Clone the project
git clone https://github.com/superboygisan/simple_webm.git
cd simple_webm

# Or if you're using the swagPlayer repo
git clone https://github.com/superboygisan/swagPlayer.git
cd swagPlayer
Step 2: Create Virtual Environment
bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/Mac:
source venv/bin/activate

# On Windows (Command Prompt):
venv\Scripts\activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
Step 3: Install Dependencies
bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
Step 4: Set Environment Variables
bash
# On Linux/Mac:
export BOT_TOKEN=your_telegram_bot_token
export SECRET_KEY=your_super_secret_key_here
export WEBAPP_URL=http://localhost:5024

# On Windows (Command Prompt):
set BOT_TOKEN=your_telegram_bot_token
set SECRET_KEY=your_super_secret_key_here
set WEBAPP_URL=http://localhost:5024

# On Windows (PowerShell):
$env:BOT_TOKEN="your_telegram_bot_token"
$env:SECRET_KEY="your_super_secret_key_here"
$env:WEBAPP_URL="http://localhost:5024"
Step 5: Run the Application
bash
# Run in development mode
python app.py

# Or run using the start script
./start.sh  # On Linux/Mac
start.bat   # On Windows
Step 6: Access the Application
Open your browser and go to:

text
http://127.0.0.1:5024
Default Admin Credentials:

Username: admin

Password: admin123

📁 Project Structure
text
simple_webm/
├── app.py                 # Main application entry point
├── bot.py                 # Telegram bot
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore file
├── README.md             # This file
├── render.yaml           # Render deployment config
├── Procfile              # Heroku deployment config
├── Dockerfile            # Docker deployment config
├── docker-compose.yml    # Docker Compose config
├── start.sh              # Startup script (Linux/Mac)
├── start.bat             # Startup script (Windows)
├── routes/               # Blueprint routes
│   ├── __init__.py
│   ├── auth.py           # Authentication
│   ├── tracks.py         # Track CRUD
│   ├── albums.py         # Album CRUD
│   ├── admin.py          # Admin panel
│   └── rooms.py          # Collaborative rooms
├── services/             # Business logic
│   ├── __init__.py
│   └── room_service.py   # Room management
├── templates/            # HTML templates
│   ├── unified.html      # Main player
│   ├── app.html          # Telegram Web App
│   ├── rooms.html        # Rooms list
│   ├── room_detail.html  # Individual room
│   ├── library.html      # User library
│   ├── admin_login.html  # Admin login
│   ├── admin_new.html    # Admin dashboard
│   └── components/       # Reusable components
│       ├── track_card.html
│       ├── album_card_grid.html
│       ├── player_card.html
│       └── album_card.html
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Premium styles
│   ├── js/
│   │   └── player.js     # Player logic
│   └── images/
├── uploads/              # User uploads
│   └── .gitkeep
└── scripts/              # Helper scripts
    ├── setup_env.sh      # Environment setup
    └── deploy.sh         # VPS deployment
🚀 Deployment Guide
Option 1: Render (Recommended - Free)
Render is the best choice for your app because it fully supports Flask + Socket.IO with WebSockets.

One-Click Deploy:
https://render.com/images/deploy-to-render-button.svg

Manual Steps:

bash
# 1. Push code to GitHub
git add .
git commit -m "Deploy to Render"
git push origin main

# 2. Go to render.com and create a new Web Service
# 3. Connect your GitHub repository
# 4. Use these settings:
#    - Name: simplewebplayer
#    - Environment: Python 3
#    - Build Command: pip install -r requirements.txt
#    - Start Command: gunicorn --worker-class eventlet -w 1 app:app

# 5. Add environment variables:
#    - BOT_TOKEN: your_telegram_bot_token
#    - SECRET_KEY: your_super_secret_key
#    - WEBAPP_URL: https://simplewebplayer.onrender.com
Option 2: Heroku (Paid)
bash
# Install Heroku CLI
# Mac: brew tap heroku/brew && brew install heroku
# Windows: Download from heroku.com

# Login
heroku login

# Create app
heroku create simplewebplayer

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set BOT_TOKEN=your_token
heroku config:set SECRET_KEY=your_secret
heroku config:set WEBAPP_URL=https://simplewebplayer.herokuapp.com

# Deploy
git push heroku main

# Scale app
heroku ps:scale web=1

# Open app
heroku open
Option 3: VPS (Full Control)
bash
# Connect to VPS
ssh root@your_server_ip

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3-pip python3-venv git nginx supervisor certbot python3-certbot-nginx

# Clone repository
git clone https://github.com/superboygisan/swagPlayer.git
cd swagPlayer

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
BOT_TOKEN=your_telegram_bot_token
SECRET_KEY=your_super_secret_key
WEBAPP_URL=https://your-domain.com
FLASK_DEBUG=False
EOF

# Configure supervisor
nano /etc/supervisor/conf.d/simplewebplayer.conf
Supervisor Configuration:

ini
[program:simplewebplayer]
command=/root/swagPlayer/venv/bin/gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:5024 app:app
directory=/root/swagPlayer
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/simplewebplayer/err.log
stdout_logfile=/var/log/simplewebplayer/out.log
environment=
    BOT_TOKEN="your_token",
    SECRET_KEY="your_secret",
    WEBAPP_URL="https://your-domain.com"
bash
# Create log directory
mkdir -p /var/log/simplewebplayer

# Reload supervisor
supervisorctl reread
supervisorctl update
supervisorctl start simplewebplayer

# Configure nginx
nano /etc/nginx/sites-available/simplewebplayer
Nginx Configuration:

nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5024;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }

    location /socket.io/ {
        proxy_pass http://127.0.0.1:5024/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400;
    }

    location /uploads/ {
        alias /root/swagPlayer/uploads/;
    }

    location /static/ {
        alias /root/swagPlayer/static/;
    }
}
bash
# Enable site
ln -s /etc/nginx/sites-available/simplewebplayer /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# Setup SSL
certbot --nginx -d your-domain.com -d www.your-domain.com
Option 4: Docker
bash
# Using Docker Compose (Recommended)
docker-compose up -d

# Or build and run manually
docker build -t simplewebplayer .
docker run -p 5024:5024 \
  -e BOT_TOKEN=your_token \
  -e SECRET_KEY=your_secret \
  -e WEBAPP_URL=http://localhost:5024 \
  simplewebplayer
🎯 API Endpoints
Authentication
Method	Endpoint	Description
POST	/api/auth/telegram	Login via Telegram
POST	/api/auth/logout	Logout user
GET	/api/auth/profile	Get user profile
Tracks
Method	Endpoint	Description
GET	/api/tracks	List tracks
POST	/api/tracks	Upload track
PUT	/api/tracks/<id>	Update track
DELETE	/api/tracks/<id>	Delete track
POST	/api/tracks/<id>/like	Toggle like
POST	/api/tracks/<id>/play	Count play
POST	/api/tracks/<id>/toggle-visibility	Hide/show track
Albums
Method	Endpoint	Description
GET	/api/albums	List albums
POST	/api/albums	Create album
PUT	/api/albums/<id>	Update album
DELETE	/api/albums/<id>	Delete album
POST	/api/albums/<id>/like	Toggle like
POST	/api/albums/<id>/play	Count play
GET	/api/albums/<id>/tracks	Get album tracks
Rooms
Method	Endpoint	Description
GET	/api/rooms	List rooms
POST	/api/rooms	Create room
GET	/api/rooms/<id>	Get room details
POST	/api/rooms/<id>/join	Join room
POST	/api/rooms/<id>/leave	Leave room
POST	/api/rooms/<id>/queue	Add to queue
POST	/api/rooms/<id>/play-next	Play next track
🤖 Telegram Bot Commands
Command	Description	Example
/start	Welcome and login	/start
/login	Get web player login link	/login
/play <song>	Play a song on your web player	/play Bohemian Rhapsody
/room	Manage collaborative rooms	/room
/help	Show help message	/help
🔧 Environment Variables
Variable	Required	Description	Example
BOT_TOKEN	✅ Yes	Telegram Bot Token from @BotFather	123456:ABC-DEF
SECRET_KEY	✅ Yes	Secret key for Flask sessions	your-super-secret-key
WEBAPP_URL	✅ Yes	Your application URL	https://simplewebplayer.onrender.com
FLASK_DEBUG	❌ No	Enable debug mode	False
PORT	❌ No	Port to run on	5024
HOST	❌ No	Host to bind to	0.0.0.0
DATABASE_URL	❌ No	PostgreSQL database URL	postgresql://...
⌨️ Keyboard Shortcuts
Shortcut	Action
Space	Play/Pause
→	Forward 5 seconds
←	Rewind 5 seconds
↑	Volume up
↓	Volume down
F	Fullscreen
M	Mute/Unmute
L	Like current track
🐛 Troubleshooting
Common Issues and Solutions
1. App won't start
bash
# Check if virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Check if all dependencies are installed
pip install -r requirements.txt

# Check for errors
python app.py
2. Socket.IO not working
bash
# Make sure eventlet is installed
pip install eventlet

# Check start command
gunicorn --worker-class eventlet -w 1 app:app
3. Database errors
bash
# Delete database and restart
rm music.db
python app.py
4. Port already in use
bash
# Find process using port 5024
lsof -i :5024  # Linux/Mac
netstat -ano | findstr :5024  # Windows

# Kill the process
kill -9 PID  # Linux/Mac
taskkill /PID PID /F  # Windows
5. Upload errors
bash
# Check upload folder permissions
chmod 755 uploads

# Check disk space
df -h
6. Telegram bot not responding
bash
# Check if BOT_TOKEN is set correctly
echo $BOT_TOKEN

# Check bot logs
tail -f bot.log
📊 Database Schema
Users Table
sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    avatar_url TEXT,
    nickname TEXT UNIQUE,
    display_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
Tracks Table
sql
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    artist TEXT,
    filename TEXT,
    cover_filename TEXT,
    lyrics TEXT,
    sort_order INTEGER DEFAULT 0,
    hidden INTEGER DEFAULT 0,
    slug TEXT,
    is_pinned INTEGER DEFAULT 0,
    plays_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
Rooms Table
sql
CREATE TABLE rooms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    host_id INTEGER NOT NULL,
    current_track_id INTEGER,
    is_playing INTEGER DEFAULT 0,
    current_time REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (host_id) REFERENCES users(id)
);
🤝 Contributing
How to Contribute
Fork the repository

Create your feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some AmazingFeature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request

Contributing Guidelines
Follow PEP 8 style guide

Write clear commit messages

Add comments for complex code

Update documentation when needed

Add tests if possible

Keep code DRY (Don't Repeat Yourself)

🐛 Bug Reports & Feature Requests
Bug Reports: Create an issue

Feature Requests: Create an issue

Support: Join Telegram Group

📧 Contact
Telegram: @dreamcatch_r

GitHub: @superboygisan

Support Group: t.me/swagplayer_support

Email: dreamcatch.r@proton.me

⭐ Support the Project
If you like this project, please consider:

⭐ Starring the repository on GitHub

🐛 Reporting bugs and issues

💡 Suggesting new features

🧑‍💻 Contributing code

📢 Sharing with others

💰 Donating (if applicable)

📊 Project Status
Aspect	Status
Development	🟢 Active
Documentation	🟢 Complete
Testing	🟡 In Progress
Deployment	🟢 Ready
Production	🟢 Stable
Security	🟢 Good
🔮 Roadmap
Version 1.0.0 (Current)
✅ Basic music playback

✅ LRC lyrics sync

✅ Album management

✅ Telegram bot integration

✅ Collaborative rooms

Version 1.1.0 (Coming Soon)
🔄 Spotify integration

🔄 YouTube Music integration

🔄 Podcast support

🔄 Smart playlists

Version 2.0.0 (Future)
🔄 Mobile app (React Native)

🔄 Desktop app (Electron)

🔄 AI recommendations

🔄 Social features

🔄 Live streaming

📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

🙏 Acknowledgments
WebMusicPlayer - UI inspiration

StreamXBot - Room logic reference

Flask-SocketIO - Real-time communication

Python-Telegram-Bot - Telegram Bot framework

Tailwind CSS - CSS framework

Font Awesome - Icons

<div align="center">
Made with ❤️ for music lovers

https://img.shields.io/github/stars/superboygisan/swagPlayer?style=social
https://img.shields.io/github/forks/superboygisan/swagPlayer?style=social
https://img.shields.io/github/watchers/superboygisan/swagPlayer?style=social
https://img.shields.io/github/followers/superboygisan?style=social

⬆ Back to Top

</div> ```
