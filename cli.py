#!/usr/bin/env python3
import click
import requests
import json
import getpass
from datetime import datetime

BASE_URL = "http://localhost:5000"
CONFIG_FILE = "user_config.json"

def load_user_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

@click.group()
def cli():
    """Password Manager CLI"""
    pass

@cli.command()
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, hide_input=True, help='Password')
def register(username, password):
    """Register a new user"""
    response = requests.post(f"{BASE_URL}/register", 
                           json={"username": username, "password": password})
    
    if response.status_code == 200:
        click.echo("✓ User registered successfully!")
    else:
        click.echo(f"✗ Error: {response.json().get('error', 'Registration failed')}")

@cli.command()
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, hide_input=True, help='Password')
def login(username, password):
    """Login and save session"""
    response = requests.post(f"{BASE_URL}/login", 
                           json={"username": username, "password": password})
    
    if response.status_code == 200:
        user_id = response.json()['user_id']
        save_user_config({"user_id": user_id, "username": username})
        click.echo("✓ Login successful!")
    else:
        click.echo(f"✗ Error: {response.json().get('error', 'Login failed')}")

@cli.command()
def list():
    """List all passwords"""
    config = load_user_config()
    if not config.get('user_id'):
        click.echo("✗ Please login first")
        return
    
    response = requests.get(f"{BASE_URL}/passwords", 
                          params={"user_id": config['user_id']})
    
    if response.status_code == 200:
        passwords = response.json()
        if not passwords:
            click.echo("No passwords found")
            return
        
        click.echo("\n📋 Your Passwords:")
        click.echo("-" * 80)
        for p in passwords:
            status = "🔴 EXPIRED" if p['expired'] else "🟢 Active"
            click.echo(f"ID: {p['id']} | {p['title']} | {p['username']} | {status}")
            if p['url']:
                click.echo(f"   URL: {p['url']}")
            click.echo(f"   Password: {p['password']}")
            if p['expires_at']:
                click.echo(f"   Expires: {p['expires_at'][:10]}")
            click.echo("-" * 80)
    else:
        click.echo("✗ Error fetching passwords")

@cli.command()
@click.option('--title', prompt=True, help='Password title')
@click.option('--password', help='Password (leave empty to generate)')
@click.option('--url', default='', help='Website URL')
@click.option('--username', default='', help='Username/Email')
@click.option('--expires-days', type=int, help='Expiry in days')
@click.option('--generate', is_flag=True, help='Generate password')
def add(title, password, url, username, expires_days, generate):
    """Add a new password"""
    config = load_user_config()
    if not config.get('user_id'):
        click.echo("✗ Please login first")
        return
    
    if generate or not password:
        # Generate password
        gen_response = requests.post(f"{BASE_URL}/generate-password", 
                                   json={"length": 16, "include_symbols": True})
        if gen_response.status_code == 200:
            password = gen_response.json()['password']
            strength = gen_response.json()['strength']
            click.echo(f"🔐 Generated password: {password}")
            click.echo(f"💪 Strength: {strength['strength']}")
        else:
            click.echo("✗ Error generating password")
            return
    else:
        # Check password strength
        strength_response = requests.post(f"{BASE_URL}/check-strength", 
                                        json={"password": password})
        if strength_response.status_code == 200:
            strength = strength_response.json()
            click.echo(f"💪 Password strength: {strength['strength']}")
            if strength['missing']:
                click.echo(f"⚠️  Missing: {', '.join(strength['missing'])}")
    
    response = requests.post(f"{BASE_URL}/passwords", json={
        "user_id": config['user_id'],
        "title": title,
        "password": password,
        "url": url,
        "username": username,
        "expires_days": expires_days
    })
    
    if response.status_code == 200:
        click.echo("✓ Password added successfully!")
    else:
        click.echo(f"✗ Error: {response.json().get('error', 'Failed to add password')}")

@cli.command()
@click.argument('password_id', type=int)
@click.option('--title', help='New title')
@click.option('--password', help='New password')
@click.option('--url', help='New URL')
@click.option('--username', help='New username')
@click.option('--expires-days', type=int, help='New expiry in days')
def update(password_id, title, password, url, username, expires_days):
    """Update a password"""
    config = load_user_config()
    if not config.get('user_id'):
        click.echo("✗ Please login first")
        return
    
    if password:
        # Check password strength
        strength_response = requests.post(f"{BASE_URL}/check-strength", 
                                        json={"password": password})
        if strength_response.status_code == 200:
            strength = strength_response.json()
            click.echo(f"💪 Password strength: {strength['strength']}")
    
    update_data = {"user_id": config['user_id']}
    if title: update_data['title'] = title
    if password: update_data['password'] = password
    if url is not None: update_data['url'] = url
    if username is not None: update_data['username'] = username
    if expires_days is not None: update_data['expires_days'] = expires_days
    
    response = requests.put(f"{BASE_URL}/passwords/{password_id}", json=update_data)
    
    if response.status_code == 200:
        click.echo("✓ Password updated successfully!")
    else:
        click.echo(f"✗ Error: {response.json().get('error', 'Failed to update password')}")

@cli.command()
@click.option('--length', default=16, help='Password length')
@click.option('--no-symbols', is_flag=True, help='Exclude symbols')
def generate(length, no_symbols):
    """Generate a secure password"""
    response = requests.post(f"{BASE_URL}/generate-password", json={
        "length": length,
        "include_symbols": not no_symbols
    })
    
    if response.status_code == 200:
        data = response.json()
        click.echo(f"🔐 Generated password: {data['password']}")
        click.echo(f"💪 Strength: {data['strength']['strength']}")
    else:
        click.echo("✗ Error generating password")

@cli.command()
@click.argument('password')
def check(password):
    """Check password strength"""
    response = requests.post(f"{BASE_URL}/check-strength", json={"password": password})
    
    if response.status_code == 200:
        strength = response.json()
        click.echo(f"💪 Strength: {strength['strength']} ({strength['score']}/5)")
        if strength['missing']:
            click.echo(f"⚠️  Missing: {', '.join(strength['missing'])}")
    else:
        click.echo("✗ Error checking password strength")

@cli.command()
def logout():
    """Logout and clear session"""
    try:
        import os
        os.remove(CONFIG_FILE)
        click.echo("✓ Logged out successfully!")
    except FileNotFoundError:
        click.echo("✓ Already logged out")

if __name__ == '__main__':
    cli()