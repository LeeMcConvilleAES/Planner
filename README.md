# AES Transport Planner — Streamlit Setup Guide

## Step 1 — GitHub
1. Create a free account at github.com
2. Click "New repository" — name it `aes-transport-planner`
3. Upload all files in this folder to the repository

## Step 2 — Google Service Account (for Sheets connection)
1. Go to console.cloud.google.com
2. Create a new project called "AES Planner"
3. Enable the Google Sheets API and Google Drive API
4. Go to IAM & Admin > Service Accounts > Create Service Account
5. Name it "aes-planner" — click Create
6. Click the service account > Keys > Add Key > JSON
7. Download the JSON file — you'll need the contents for Step 4

## Step 3 — Share your Google Sheet with the service account
1. Open your "AES Transport Planner" Google Sheet
2. Click Share
3. Add the service account email (looks like aes-planner@xxx.iam.gserviceaccount.com)
4. Give it Editor access

## Step 4 — Deploy on Streamlit Cloud
1. Go to share.streamlit.io — sign in with GitHub
2. Click "New app"
3. Select your aes-transport-planner repository
4. Main file path: app.py
5. Click "Advanced settings" > Secrets
6. Paste in the contents of your service account JSON like this:

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "abc123"
private_key = "-----BEGIN RSA PRIVATE KEY-----\n..."
client_email = "aes-planner@your-project.iam.gserviceaccount.com"
...etc

7. Click Deploy!

## Your links
- Team link: https://your-app-name.streamlit.app
- Read-only: same link — team members switch to Read Only mode
- For a separate read-only URL, deploy the app again with mode locked to readonly
