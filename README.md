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

---

## ✨ **Features**

### 🎵 **Core Music Features**
- ✅ **MP3 Upload & Streaming** - Upload and stream your music files
- ✅ **LRC Lyrics Sync** - Real-time line-by-line lyrics highlighting
- ✅ **Cover Art Support** - Automatic extraction from MP3 files
- ✅ **Metadata Editor** - Edit title, artist, album, year
- ✅ **Album Management** - Create and organize albums with cover art
- ✅ **Playlist Support** - Create and manage custom playlists

### 👥 **Collaborative Features**
- ✅ **Real-time Rooms** - Create collaborative listening rooms
- ✅ **Shared Queue** - Add and manage songs together
- ✅ **Playback Sync** - Everyone hears the same moment
- ✅ **Room Member Management** - See who's listening
- ✅ **Skip Voting** - Democratic song skipping

### 🤖 **Telegram Integration**
- ✅ **Bot Login** - Quick authentication via Telegram
- ✅ **Remote Control** - Play songs from Telegram
- ✅ **Deep Linking** - Open web player directly from bot
- ✅ **Room Management** - Create/join rooms via Telegram
- ✅ **Playlist Sharing** - Share playlists via Telegram

### 🎨 **Premium UI**
- ✅ **Modern Design** - Clean and intuitive interface
- ✅ **Mobile-First** - Fully responsive on all devices
- ✅ **Dark Theme** - AMOLED-friendly design
- ✅ **Animations** - Smooth transitions and interactions
- ✅ **Keyboard Shortcuts** - Control playback with keyboard

### 🔐 **Admin Panel**
- ✅ Track Management - Hide/delete tracks
- ✅ Album Management - Hide/delete albums
- ✅ User Management - View and manage users
- ✅ Pin Featured Content - Highlight important tracks/albums

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
