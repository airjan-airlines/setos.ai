from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app import llm
import hashlib
import os
import base64
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
from supabase import Client

from app import roadmap
from app.models import RoadmapRequest, RoadmapResponse, SummaryResponse, JargonResponse
from . import database

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5500", "http://127.0.0.1:5500"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    firstName: str
    lastName: str
    email: str
    password: str
    newsletter: Optional[bool] = False

class ResendVerificationRequest(BaseModel):
    email: str

# Email configuration
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = os.getenv("EMAIL_USER", "your-email @gmail.com")  # Set this in .env
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-app-password")  # Set this in .env

# Store verification codes (in production, use a database)
verification_codes = {}

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email: str, code: str):
    """Send verification email using Gmail SMTP"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = email
        msg['Subject'] = "Verify your setosa account"
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>Welcome to setosa!</h2>
            <p>Thank you for creating an account. Please use the following verification code to complete your registration:</p>
            <h1 style="color: #6366f1; font-size: 2rem; text-align: center; padding: 20px; background: #f8fafc; border-radius: 10px; margin: 20px 0;">{code}</h1>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't create an account with setosa, please ignore this email.</p>
            <br>
            <p>Best regards,<br>The setosa Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to SMTP server
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(EMAIL_USER, email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email sending error: {e}")
        return False

@app.get("/api/")
def read_root():
    return {"message": "Paper Roadmap API is running"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "message": "Backend is running"}

@app.get("/api/test")
def test_endpoint():
    return {"message": "Test endpoint working"}

@app.post(path="/api/roadmap/", response_model=RoadmapResponse)
async def get_roadmap(request: RoadmapRequest, client: Client = Depends(database.get_python_client)):
    generated_roadmap = roadmap.generate_roadmap(request.query, client)
    return {"roadmap": generated_roadmap}

@app.get("/api/paper/{paper_id}/summary", response_model=SummaryResponse)
async def get_summary(paper_id: str, client: Client = Depends(database.get_python_client)):
    paper = roadmap.get_paper_by_id(paper_id, client)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    summary = llm.generate_response(command = "summary", abstract = paper.abstract)
    return {"paper_id": paper_id, "summary": summary}

@app.get("/api/paper/{paper_id}/jargon", response_model=JargonResponse)
async def get_jargon(paper_id: str, client: Client = Depends(database.get_python_client)):
    paper = roadmap.get_paper_by_id(paper_id, client)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    jargon_list = llm.generate_response("jargon", paper.abstract)
    return {"paper_id": paper_id, "jargon": jargon_list}

@app.post("/api/register")
async def register(request: RegisterRequest, client: Client = Depends(database.get_python_client)):
    # Check if user already exists
    response = client.table('users').select('email').eq('email', request.email).execute()
    if response.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password
    hashed_password = hashlib.sha256(request.password.encode()).hexdigest()

    # Create user
    user_data = {
        "first_name": request.firstName,
        "last_name": request.lastName,
        "email": request.email,
        "password": hashed_password,
        "newsletter": request.newsletter,
    }
    response = client.table('users').insert(user_data).execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create user")

    # Generate and send verification email
    code = generate_verification_code()
    verification_codes[request.email] = {
        "code": code,
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }
    
    if not send_verification_email(request.email, code):
        raise HTTPException(status_code=500, detail="Failed to send verification email")

    return {"message": "Registration successful. Please check your email for a verification code."}

@app.post("/api/login")
async def login(request: LoginRequest, client: Client = Depends(database.get_python_client)):
    # Find user by email
    response = client.table('users').select('*').eq('email', request.email).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")

    user = response.data[0]
    
    # Verify password
    hashed_password = hashlib.sha256(request.password.encode()).hexdigest()
    if user["password"] != hashed_password:
        raise HTTPException(status_code=401, detail="Incorrect password")

    # Check if verified
    if not user["is_verified"]:
        raise HTTPException(status_code=401, detail="Account not verified. Please check your email.")

    return {"message": "Login successful"}

@app.post("/api/verify")
async def verify(email: str, code: str, client: Client = Depends(database.get_python_client)):
    if email not in verification_codes:
        raise HTTPException(status_code=400, detail="Invalid verification request")

    stored_code = verification_codes[email]
    if stored_code["code"] != code or datetime.utcnow() > stored_code["expires_at"]:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    # Update user's verification status
    response = client.table('users').update({"is_verified": True}).eq('email', email).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to verify user")

    del verification_codes[email]  # Clean up used code
    return {"message": "Account verified successfully"}

@app.post("/api/resend-verification")
async def resend_verification(request: ResendVerificationRequest, client: Client = Depends(database.get_python_client)):
    # Check if user exists
    response = client.table('users').select('email').eq('email', request.email).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate and send new verification email
    code = generate_verification_code()
    verification_codes[request.email] = {
        "code": code,
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }
    
    if not send_verification_email(request.email, code):
        raise HTTPException(status_code=500, detail="Failed to send verification email")

    return {"message": "Verification code resent successfully"}
