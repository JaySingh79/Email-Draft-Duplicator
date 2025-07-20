# Email-Draft-Duplicator
Easily duplicate any gmail draft into as many copies as you wish.

## 🚀 Features

- View your Gmail drafts
- Select any draft and duplicate it N times
- Works seamlessly with a Chrome extension UI
- OAuth-based Gmail authentication (first time only)

## 🛠️ Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) (Windows/macOS)  
  OR  
  Docker CLI (`docker`, `docker-compose`) on Linux

- A Google Cloud Project with Gmail API enabled  
  ([Enable Gmail API here](https://console.developers.google.com/))

---

## 🔐 One-time Gmail Authentication Setup

### 1. Create OAuth Credentials
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Enable **Gmail API**
- Create OAuth credentials → Choose "Desktop App"
- Download the `credentials.json` file


## Add the extension folder in Google extentions (click "load unpacked" -- search internet for better results)

## 🐳 Run with Docker

```bash
git clone https://github.com/yourname/project.git
cd project
docker-compose up --build
