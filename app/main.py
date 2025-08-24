from fastapi import FastAPI, HTTPException
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
class RoadmapRequest(BaseModel):
    query: str

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
EMAIL_USER = os.getenv("EMAIL_USER", "your-email@gmail.com")  # Set this in .env
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

@app.get("/")
def read_root():
    return {"message": "Paper Roadmap API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Backend is running"}

# Import roadmap module only when needed to avoid startup issues
def get_roadmap_module():
    try:
        from app import roadmap
        return roadmap
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Backend services not ready: {str(e)}")

@app.post("/roadmap/")
async def get_roadmap(request: RoadmapRequest):
    roadmap = get_roadmap_module()
    
    # Validate request
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query is required")
    
    try:
        generated_roadmap = roadmap.generate_roadmap(request.query)
        return {"roadmap": generated_roadmap}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating roadmap: {str(e)}")

@app.get("/paper/{paper_id}/summary")
async def get_summary(paper_id: str):
    roadmap = get_roadmap_module()
    
    try:
        paper = roadmap.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        summary = llm.generate_response(command="summary", abstract=paper.abstract)
        return {"paper_id": paper_id, "summary": summary}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@app.get("/paper/{paper_id}/jargon")
async def get_jargon(paper_id: str):
    roadmap = get_roadmap_module()
    
    try:
        paper = roadmap.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        jargon_list = llm.generate_response("jargon", paper.abstract)
        return {"paper_id": paper_id, "jargon": jargon_list}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting jargon: {str(e)}")

# Authentication endpoints
@app.post("/api/register")
async def register(request: RegisterRequest):
    try:
        # Simple mock registration - in a real app, you'd use a database
        # Hash the password
        hashed_password = hashlib.sha256(request.password.encode()).hexdigest()
        
        # Create a simple token (base64 encoded user data)
        token_data = f"{request.email}:{request.firstName}:{request.lastName}:{datetime.utcnow().timestamp()}"
        token = base64.b64encode(token_data.encode()).decode()
        
        # Create user object
        user = {
            "id": "user_" + hashlib.md5(request.email.encode()).hexdigest()[:8],
            "firstName": request.firstName,
            "lastName": request.lastName,
            "email": request.email,
            "newsletter": request.newsletter
        }
        
        return {
            "success": True,
            "message": "Account created successfully! Welcome to setosa.",
            "token": token,
            "user": user
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Registration failed: {str(e)}"
        }

@app.post("/api/login")
async def login(request: LoginRequest):
    try:
        # Simple mock login - in a real app, you'd verify against a database
        # For demo purposes, accept any email/password combination
        if not request.email or not request.password:
            return {
                "success": False,
                "message": "Email and password are required"
            }
        
        # Create a simple token (base64 encoded user data)
        token_data = f"{request.email}:{datetime.utcnow().timestamp()}"
        token = base64.b64encode(token_data.encode()).decode()
        
        # Create user object (mock data)
        user = {
            "id": "user_" + hashlib.md5(request.email.encode()).hexdigest()[:8],
            "firstName": request.email.split('@')[0].title(),
            "lastName": "User",
            "email": request.email
        }
        
        return {
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": user
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Login failed: {str(e)}"
        }

@app.post("/api/resend-verification")
async def resend_verification(request: ResendVerificationRequest):
    try:
        # Generate verification code
        verification_code = generate_verification_code()
        
        # Store the code with timestamp
        verification_codes[request.email] = {
            "code": verification_code,
            "timestamp": datetime.utcnow()
        }
        
        # Send verification email
        if EMAIL_USER == "your-email@gmail.com" or EMAIL_PASSWORD == "your-app-password":
            # If email credentials are not configured, return mock response
            print(f"Mock verification code for {request.email}: {verification_code}")
            return {
                "success": True,
                "message": f"Verification email sent successfully! Mock code: {verification_code}"
            }
        else:
            # Send actual email
            email_sent = send_verification_email(request.email, verification_code)
            if email_sent:
                return {
                    "success": True,
                    "message": "Verification email sent successfully! Please check your inbox."
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to send verification email. Please try again."
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to send verification email: {str(e)}"
        }