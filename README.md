# Password Manager

A secure, multi-tenant password manager with both CLI and Web interfaces.

## Features

✅ **Multi-tenant**: Multiple users with secure authentication  
✅ **List passwords**: View all stored passwords  
✅ **Update passwords**: Modify existing entries  
✅ **Secure storage**: AES encryption + bcrypt hashing  
✅ **Password expiry**: Set expiration dates  
✅ **Strength compliance**: Password strength validation  
✅ **Auto generation**: Secure password generation  

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the backend server:**
   ```bash
   python app.py
   ```
   Server runs on http://localhost:5000

## Usage

### CLI Interface

```bash
# Register new user
python cli.py register --username john --password mypass123

# Login
python cli.py login --username john --password mypass123

# List all passwords
python cli.py list

# Add password (manual)
python cli.py add --title "Gmail" --password "mypass123" --url "https://gmail.com" --username "john@email.com" --expires-days 90

# Add password (auto-generate)
python cli.py add --title "Facebook" --generate --expires-days 60

# Update password
python cli.py update 1 --password "newpass456" --expires-days 120

# Generate password
python cli.py generate --length 16

# Check password strength
python cli.py check "mypassword123"

# Logout
python cli.py logout
```

### Web Interface

1. Open `index.html` in your browser
2. Register/Login with credentials
3. Use the web interface to manage passwords

## Security Features

- **AES Encryption**: All passwords encrypted before storage
- **bcrypt Hashing**: User passwords securely hashed
- **Multi-tenant**: Complete user isolation
- **Password Strength**: Real-time strength validation
- **Expiry Management**: Automatic expiry tracking
- **Secure Generation**: Cryptographically secure password generation

## API Endpoints

- `POST /register` - Register new user
- `POST /login` - User authentication
- `GET /passwords` - List user passwords
- `POST /passwords` - Add new password
- `PUT /passwords/<id>` - Update password
- `POST /generate-password` - Generate secure password
- `POST /check-strength` - Check password strength

## Files

- `app.py` - Flask backend server
- `cli.py` - Command-line interface
- `index.html` - Web interface
- `passwords.db` - SQLite database (auto-created)
- `secret.key` - Encryption key (auto-generated)
- `user_config.json` - CLI session storage
