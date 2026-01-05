#"from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form"
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from motor import motor_asyncio
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import bcrypt
import jwt
from bson import ObjectId
import base64
import gridfs
import io

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Note: GridFS setup - we'll use base64 encoding for files instead of GridFS for simplicity
# GridFS requires synchronous MongoDB client, but we're using async motor

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 30

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix=\"/api\")
security = HTTPBearer()

# Helper function to convert ObjectId to string
def serialize_doc(doc):
    if doc and '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

# Helper to extract year from email
def extract_year_from_email(email: str) -> int:
    \"\"\"Extract year from email pattern: cb.sc.u4cse{YY}XXX@cb.students.amrita.edu\"\"\"
    try:
        # Extract the YY part
        parts = email.split('@')[0].split('.')
        code = parts[-1]  # u4cse23XXX
        year_code = code[5:7]  # Get '23' from 'u4cse23XXX'
        
        # Map year code to actual year
        year_map = {
            '25': 1,  # 1st year
            '24': 2,  # 2nd year
            '23': 3,  # 3rd year
            '22': 4   # 4th year
        }
        return year_map.get(year_code, 1)
    except:
        return 1

# ==================== MODELS ====================

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    roll_no: str
    section: Optional[str] = \"A\"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    name: str
    email: EmailStr
    roll_no: str
    year: int
    semester: int
    program: str = \"B.Tech CSE\"
    section: str = \"A\"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Subject(BaseModel):
    code: str
    name: str
    category: str  # ENGG, CSE, PRJ, HUM
    credits: int
    year: int
    semester: int
    lecture_hours: int = 0
    tutorial_hours: int = 0
    practical_hours: int = 0
    evaluation_pattern: str = \"70-30\"

class Assignment(BaseModel):
    subject_id: str
    title: str
    description: str
    deadline: datetime
    max_marks: int
    file_base64: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AssignmentSubmission(BaseModel):
    assignment_id: str
    student_id: str
    file_base64: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = \"submitted\"  # submitted, late, not_submitted
    marks: Optional[int] = None
    feedback: Optional[str] = None

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int  # Index of correct option

class Quiz(BaseModel):
    subject_id: str
    title: str
    description: str
    duration_minutes: int
    max_marks: int
    questions: List[QuizQuestion]
    start_time: datetime
    end_time: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class QuizAttempt(BaseModel):
    quiz_id: str
    student_id: str
    answers: List[int]  # List of selected option indices
    score: int = 0
    time_taken: int = 0  # in seconds
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = \"completed\"

class StudyMaterial(BaseModel):
    subject_id: str
    title: str
    description: Optional[str] = None
    file_type: str  # pdf, ppt, doc, video
    file_base64: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class Fee(BaseModel):
    student_id: str
    semester: int
    year: int
    tuition_fee: int = 50000
    hostel_fee: int = 20000
    other_fees: int = 5000
    total_amount: int = 75000
    paid_amount: int = 0
    due_amount: int = 75000
    due_date: datetime
    status: str = \"pending\"  # paid, pending, overdue

class FeePayment(BaseModel):
    fee_id: str
    student_id: str
    amount: int
    payment_method: str = \"razorpay\"
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    payment_date: datetime = Field(default_factory=datetime.utcnow)
    status: str = \"success\"

class Result(BaseModel):
    student_id: str
    subject_id: str
    semester: int
    year: int
    assignment_marks: int = 0
    quiz_marks: int = 0
    mid_sem: int = 0
    end_sem: int = 0
    internal_total: int = 0
    grade: Optional[str] = None

class Registration(BaseModel):
    student_id: str
    semester: int
    year: int
    selected_subjects: List[str]
    electives: List[str]
    status: str = \"pending\"  # pending, approved, rejected
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

class LibraryBook(BaseModel):
    title: str
    author: str
    isbn: str
    category: str
    total_copies: int = 1
    available_copies: int = 1

class LibraryIssue(BaseModel):
    student_id: str
    book_id: str
    issue_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: datetime
    return_date: Optional[datetime] = None
    fine_amount: int = 0
    status: str = \"issued\"  # issued, returned, overdue

class Announcement(BaseModel):
    title: str
    message: str
    target_audience: str = \"all\"  # all, year1, year2, year3, year4
    priority: str = \"normal\"  # high, normal, low
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Notification(BaseModel):
    student_id: str
    title: str
    message: str
    type: str  # assignment, quiz, fee, announcement, exam
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ==================== AUTHENTICATION ====================

def create_token(user_id: str, email: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail=\"Token has expired\")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail=\"Invalid token\")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    user = await db.users.find_one({'_id': ObjectId(payload['user_id'])})
    if not user:
        raise HTTPException(status_code=401, detail=\"User not found\")
    return serialize_doc(user)

# ==================== AUTH ENDPOINTS ====================

@api_router.post(\"/auth/register\")
async def register(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({'email': user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail=\"User already exists\")
    
    # Hash password
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
    
    # Extract year from email
    year = extract_year_from_email(user_data.email)
    semester = (year * 2) if year <= 4 else 8  # Calculate semester based on year
    
    # Create user
    user = {
        'name': user_data.name,
        'email': user_data.email,
        'password': hashed_password.decode('utf-8'),
        'roll_no': user_data.roll_no,
        'year': year,
        'semester': semester,
        'program': 'B.Tech CSE',
        'section': user_data.section,
        'created_at': datetime.utcnow()
    }
    
    result = await db.users.insert_one(user)
    user_id = str(result.inserted_id)
    
    # Create token
    token = create_token(user_id, user_data.email)
    
    return {
        'token': token,
        'user': {
            '_id': user_id,
            'name': user_data.name,
            'email': user_data.email,
            'roll_no': user_data.roll_no,
            'year': year,
            'semester': semester,
            'program': 'B.Tech CSE',
            'section': user_data.section
        }
    }

@api_router.post(\"/auth/login\")
async def login(credentials: UserLogin):
    # Find user
    user = await db.users.find_one({'email': credentials.email})
    if not user:
        raise HTTPException(status_code=401, detail=\"Invalid credentials\")
    
    # Verify password
    if not bcrypt.checkpw(credentials.password.encode('utf-8'), user['password'].encode('utf-8')):
        raise HTTPException(status_code=401, detail=\"Invalid credentials\")
    
    # Create token
    user_id = str(user['_id'])
    token = create_token(user_id, credentials.email)
    
    return {
        'token': token,
        'user': serialize_doc({
            '_id': user_id,
            'name': user['name'],
            'email': user['email'],
            'roll_no': user['roll_no'],
            'year': user['year'],
            'semester': user['semester'],
            'program': user.get('program', 'B.Tech CSE'),
            'section': user.get('section', 'A')
        })
    }

@api_router.get(\"/auth/me\")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

# ==================== DASHBOARD ====================

@api_router.get(\"/dashboard\")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    # Get announcements
    announcements = await db.announcements.find().sort('created_at', -1).limit(3).to_list(3)
    
    # Get pending assignments count
    student_subjects = await db.enrollments.find({'student_id': current_user['_id']}).to_list(100)
    subject_ids = [str(enrollment['subject_id']) for enrollment in student_subjects]
    
    pending_assignments = await db.assignments.count_documents({
        'subject_id': {'$in': subject_ids},
        'deadline': {'$gte': datetime.utcnow()}
    })
    
    # Get upcoming quizzes
    upcoming_quizzes = await db.quizzes.count_documents({
        'subject_id': {'$in': subject_ids},
        'start_time': {'$gte': datetime.utcnow()}
    })
    
    # Get fee status
    fee = await db.fees.find_one({'student_id': current_user['_id'], 'semester': current_user['semester']})
    fee_due = fee['due_amount'] if fee else 0
    
    # Get notifications count
    unread_notifications = await db.notifications.count_documents({
        'student_id': current_user['_id'],
        'read': False
    })
    
    return {
        'announcements': [serialize_doc(a) for a in announcements],
        'stats': {
            'pending_assignments': pending_assignments,
            'upcoming_quizzes': upcoming_quizzes,
            'fee_due': fee_due,
            'unread_notifications': unread_notifications
        }
    }

# ==================== SUBJECTS ====================

@api_router.get(\"/subjects\")
async def get_subjects(current_user: dict = Depends(get_current_user)):
    # Get subjects for user's year and semester
    subjects = await db.subjects.find({
        'year': current_user['year'],
        'semester': current_user['semester']
    }).to_list(100)
    
    return [serialize_doc(s) for s in subjects]

@api_router.get(\"/subjects/{subject_id}\")
async def get_subject(subject_id: str, current_user: dict = Depends(get_current_user)):
    subject = await db.subjects.find_one({'_id': ObjectId(subject_id)})
    if not subject:
        raise HTTPException(status_code=404, detail=\"Subject not found\")
    return serialize_doc(subject)

# ==================== ASSIGNMENTS ====================

@api_router.get(\"/subjects/{subject_id}/assignments\")
async def get_assignments(subject_id: str, current_user: dict = Depends(get_current_user)):
    assignments = await db.assignments.find({'subject_id': subject_id}).sort('deadline', -1).to_list(100)
    
    # Get submission status for each assignment
    result = []
    for assignment in assignments:
        assignment_dict = serialize_doc(assignment)
        submission = await db.assignment_submissions.find_one({
            'assignment_id': str(assignment['_id']),
            'student_id': current_user['_id']
        })
        assignment_dict['submission'] = serialize_doc(submission) if submission else None
        result.append(assignment_dict)
    
    return result

@api_router.post(\"/assignments/{assignment_id}/submit\")
async def submit_assignment(
    assignment_id: str,
    file_base64: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    # Check if assignment exists
    assignment = await db.assignments.find_one({'_id': ObjectId(assignment_id)})
    if not assignment:
        raise HTTPException(status_code=404, detail=\"Assignment not found\")
    
    # Check if already submitted
    existing_submission = await db.assignment_submissions.find_one({
        'assignment_id': assignment_id,
        'student_id': current_user['_id']
    })
    
    # Determine status (late or on-time)
    status = \"late\" if datetime.utcnow() > assignment['deadline'] else \"submitted\"
    
    submission = {
        'assignment_id': assignment_id,
        'student_id': current_user['_id'],
        'file_base64': file_base64,
        'submitted_at': datetime.utcnow(),
        'status': status,
        'marks': None,
        'feedback': None
    }
    
    if existing_submission:
        await db.assignment_submissions.update_one(
            {'_id': existing_submission['_id']},
            {'$set': submission}
        )
        submission_id = str(existing_submission['_id'])
    else:
        result = await db.assignment_submissions.insert_one(submission)
        submission_id = str(result.inserted_id)
    
    # Create notification
    await db.notifications.insert_one({
        'student_id': current_user['_id'],
        'title': 'Assignment Submitted',
        'message': f'You have successfully submitted assignment: {assignment[\"title\"]}',
        'type': 'assignment',
        'read': False,
        'created_at': datetime.utcnow()
    })
    
    return {'message': 'Assignment submitted successfully', 'submission_id': submission_id}

# ==================== QUIZZES ====================

@api_router.get(\"/subjects/{subject_id}/quizzes\")
async def get_quizzes(subject_id: str, current_user: dict = Depends(get_current_user)):
    quizzes = await db.quizzes.find({'subject_id': subject_id}).sort('start_time', -1).to_list(100)
    
    # Get attempt status for each quiz
    result = []
    for quiz in quizzes:
        quiz_dict = serialize_doc(quiz)
        # Remove correct answers from response
        quiz_dict['questions'] = [
            {'question': q['question'], 'options': q['options']}
            for q in quiz_dict.get('questions', [])
        ]
        
        attempt = await db.quiz_attempts.find_one({
            'quiz_id': str(quiz['_id']),
            'student_id': current_user['_id']
        })
        quiz_dict['attempt'] = serialize_doc(attempt) if attempt else None
        result.append(quiz_dict)
    
    return result

@api_router.get(\"/quizzes/{quiz_id}\")
async def get_quiz(quiz_id: str, current_user: dict = Depends(get_current_user)):
    quiz = await db.quizzes.find_one({'_id': ObjectId(quiz_id)})
    if not quiz:
        raise HTTPException(status_code=404, detail=\"Quiz not found\")
    
    # Check if already attempted
    attempt = await db.quiz_attempts.find_one({
        'quiz_id': quiz_id,
        'student_id': current_user['_id']
    })
    
    if attempt:
        raise HTTPException(status_code=400, detail=\"Quiz already attempted\")
    
    # Check if quiz is available
    now = datetime.utcnow()
    if now < quiz['start_time']:
        raise HTTPException(status_code=400, detail=\"Quiz not started yet\")
    if now > quiz['end_time']:
        raise HTTPException(status_code=400, detail=\"Quiz has ended\")
    
    # Return quiz without correct answers
    quiz_dict = serialize_doc(quiz)
    quiz_dict['questions'] = [
        {'question': q['question'], 'options': q['options']}
        for q in quiz_dict.get('questions', [])
    ]
    
    return quiz_dict

@api_router.post(\"/quizzes/{quiz_id}/submit\")
async def submit_quiz(
    quiz_id: str,
    answers: List[int],
    time_taken: int,
    current_user: dict = Depends(get_current_user)
):
    # Get quiz
    quiz = await db.quizzes.find_one({'_id': ObjectId(quiz_id)})
    if not quiz:
        raise HTTPException(status_code=404, detail=\"Quiz not found\")
    
    # Check if already attempted
    existing_attempt = await db.quiz_attempts.find_one({
        'quiz_id': quiz_id,
        'student_id': current_user['_id']
    })
    
    if existing_attempt:
        raise HTTPException(status_code=400, detail=\"Quiz already attempted\")
    
    # Calculate score
    score = 0
    total_questions = len(quiz['questions'])
    for i, answer in enumerate(answers):
        if i < total_questions and answer == quiz['questions'][i]['correct_answer']:
            score += 1
    
    # Calculate marks
    marks = int((score / total_questions) * quiz['max_marks'])
    
    # Save attempt
    attempt = {
        'quiz_id': quiz_id,
        'student_id': current_user['_id'],
        'answers': answers,
        'score': marks,
        'time_taken': time_taken,
        'submitted_at': datetime.utcnow(),
        'status': 'completed'
    }
    
    result = await db.quiz_attempts.insert_one(attempt)
    
    # Create notification
    await db.notifications.insert_one({
        'student_id': current_user['_id'],
        'title': 'Quiz Completed',
        'message': f'You scored {marks}/{quiz[\"max_marks\"]} in {quiz[\"title\"]}',
        'type': 'quiz',
        'read': False,
        'created_at': datetime.utcnow()
    })
    
    return {
        'message': 'Quiz submitted successfully',
        'score': marks,
        'total': quiz['max_marks'],
        'correct_answers': score,
        'total_questions': total_questions
    }

# ==================== STUDY MATERIALS ====================

@api_router.get(\"/subjects/{subject_id}/materials\")
async def get_study_materials(subject_id: str, current_user: dict = Depends(get_current_user)):
    materials = await db.study_materials.find({'subject_id': subject_id}).sort('uploaded_at', -1).to_list(100)
    return [serialize_doc(m) for m in materials]

# ==================== RESULTS ====================

@api_router.get(\"/results\")
async def get_results(current_user: dict = Depends(get_current_user)):
    results = await db.results.find({'student_id': current_user['_id']}).to_list(100)
    
    # Populate subject details
    result_list = []
    for result in results:
        result_dict = serialize_doc(result)
        subject = await db.subjects.find_one({'_id': ObjectId(result['subject_id'])})
        result_dict['subject'] = serialize_doc(subject) if subject else None
        result_list.append(result_dict)
    
    return result_list

@api_router.get(\"/results/semester/{semester}\")
async def get_semester_results(semester: int, current_user: dict = Depends(get_current_user)):
    results = await db.results.find({
        'student_id': current_user['_id'],
        'semester': semester
    }).to_list(100)
    
    # Calculate SGPA
    total_credits = 0
    total_points = 0
    
    result_list = []
    for result in results:
        result_dict = serialize_doc(result)
        subject = await db.subjects.find_one({'_id': ObjectId(result['subject_id'])})
        if subject:
            result_dict['subject'] = serialize_doc(subject)
            # Simple grade calculation
            total = result.get('internal_total', 0) + result.get('end_sem', 0)
            if total >= 90:
                grade = 'O'
                grade_point = 10
            elif total >= 80:
                grade = 'A+'
                grade_point = 9
            elif total >= 70:
                grade = 'A'
                grade_point = 8
            elif total >= 60:
                grade = 'B+'
                grade_point = 7
            elif total >= 50:
                grade = 'B'
                grade_point = 6
            else:
                grade = 'C'
                grade_point = 5
            
            result_dict['grade'] = grade
            total_credits += subject.get('credits', 0)
            total_points += grade_point * subject.get('credits', 0)
        
        result_list.append(result_dict)
    
    sgpa = total_points / total_credits if total_credits > 0 else 0.0
    
    return {
        'results': result_list,
        'sgpa': round(sgpa, 2),
        'total_credits': total_credits
    }

# ==================== FEES ====================

@api_router.get(\"/fees\")
async def get_fees(current_user: dict = Depends(get_current_user)):
    fees = await db.fees.find({'student_id': current_user['_id']}).sort('year', -1).to_list(100)
    return [serialize_doc(f) for f in fees]

@api_router.get(\"/fees/current\")
async def get_current_fee(current_user: dict = Depends(get_current_user)):
    fee = await db.fees.find_one({
        'student_id': current_user['_id'],
        'semester': current_user['semester'],
        'year': current_user['year']
    })
    
    if not fee:
        # Create fee entry if not exists
        fee = {
            'student_id': current_user['_id'],
            'semester': current_user['semester'],
            'year': current_user['year'],
            'tuition_fee': 50000,
            'hostel_fee': 20000,
            'other_fees': 5000,
            'total_amount': 75000,
            'paid_amount': 0,
            'due_amount': 75000,
            'due_date': datetime.utcnow() + timedelta(days=30),
            'status': 'pending'
        }
        result = await db.fees.insert_one(fee)
        fee['_id'] = result.inserted_id
    
    return serialize_doc(fee)

@api_router.post(\"/fees/{fee_id}/create-order\")
async def create_razorpay_order(fee_id: str, current_user: dict = Depends(get_current_user)):
    # This is a mock implementation - in production, integrate with actual Razorpay
    fee = await db.fees.find_one({'_id': ObjectId(fee_id)})
    if not fee:
        raise HTTPException(status_code=404, detail=\"Fee not found\")
    
    # Mock Razorpay order
    order_id = f\"order_{uuid.uuid4().hex[:16]}\"
    
    return {
        'order_id': order_id,
        'amount': fee['due_amount'],
        'currency': 'INR',
        'key_id': 'rzp_test_key'  # Mock key
    }

@api_router.post(\"/fees/{fee_id}/payment\")
async def record_payment(
    fee_id: str,
    razorpay_order_id: str = Form(...),
    razorpay_payment_id: str = Form(...),
    amount: int = Form(...),
    current_user: dict = Depends(get_current_user)
):
    # Record payment
    payment = {
        'fee_id': fee_id,
        'student_id': current_user['_id'],
        'amount': amount,
        'payment_method': 'razorpay',
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'payment_date': datetime.utcnow(),
        'status': 'success'
    }
    
    await db.fee_payments.insert_one(payment)
    
    # Update fee
    await db.fees.update_one(
        {'_id': ObjectId(fee_id)},
        {
            '$inc': {'paid_amount': amount},
            '$set': {
                'due_amount': 0,
                'status': 'paid'
            }
        }
    )
    
    # Create notification
    await db.notifications.insert_one({
        'student_id': current_user['_id'],
        'title': 'Payment Successful',
        'message': f'Your payment of ₹{amount} has been received',
        'type': 'fee',
        'read': False,
        'created_at': datetime.utcnow()
    })
    
    return {'message': 'Payment recorded successfully'}

# ==================== REGISTRATION ====================

@api_router.get(\"/registrations\")
async def get_registrations(current_user: dict = Depends(get_current_user)):
    registrations = await db.registrations.find({'student_id': current_user['_id']}).sort('submitted_at', -1).to_list(100)
    return [serialize_doc(r) for r in registrations]

@api_router.post(\"/registrations\")
async def create_registration(
    selected_subjects: List[str],
    electives: List[str],
    current_user: dict = Depends(get_current_user)
):
    # Check if registration already exists for current semester
    existing = await db.registrations.find_one({
        'student_id': current_user['_id'],
        'semester': current_user['semester'],
        'year': current_user['year']
    })
    
    if existing and existing['status'] != 'rejected':
        raise HTTPException(status_code=400, detail=\"Registration already submitted for this semester\")
    
    registration = {
        'student_id': current_user['_id'],
        'semester': current_user['semester'],
        'year': current_user['year'],
        'selected_subjects': selected_subjects,
        'electives': electives,
        'status': 'pending',
        'submitted_at': datetime.utcnow()
    }
    
    result = await db.registrations.insert_one(registration)
    
    # Create enrollments
    for subject_id in selected_subjects + electives:
        await db.enrollments.insert_one({
            'student_id': current_user['_id'],
            'subject_id': subject_id,
            'semester': current_user['semester'],
            'year': current_user['year'],
            'enrolled_at': datetime.utcnow()
        })
    
    # Create notification
    await db.notifications.insert_one({
        'student_id': current_user['_id'],
        'title': 'Registration Submitted',
        'message': 'Your course registration has been submitted for approval',
        'type': 'registration',
        'read': False,
        'created_at': datetime.utcnow()
    })
    
    return {'message': 'Registration submitted successfully', 'registration_id': str(result.inserted_id)}

# ==================== LIBRARY ====================

@api_router.get(\"/library/books\")
async def search_books(query: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if query:
        books = await db.library_books.find({
            '$or': [
                {'title': {'$regex': query, '$options': 'i'}},
                {'author': {'$regex': query, '$options': 'i'}},
                {'isbn': {'$regex': query, '$options': 'i'}}
            ]
        }).to_list(50)
    else:
        books = await db.library_books.find().limit(50).to_list(50)
    
    return [serialize_doc(b) for b in books]

@api_router.get(\"/library/issued\")
async def get_issued_books(current_user: dict = Depends(get_current_user)):
    issues = await db.library_issues.find({
        'student_id': current_user['_id'],
        'status': {'$in': ['issued', 'overdue']}
    }).to_list(100)
    
    # Populate book details
    result = []
    for issue in issues:
        issue_dict = serialize_doc(issue)
        book = await db.library_books.find_one({'_id': ObjectId(issue['book_id'])})
        issue_dict['book'] = serialize_doc(book) if book else None
        result.append(issue_dict)
    
    return result

# ==================== NOTIFICATIONS ====================

@api_router.get(\"/notifications\")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    notifications = await db.notifications.find({
        'student_id': current_user['_id']
    }).sort('created_at', -1).limit(50).to_list(50)
    
    return [serialize_doc(n) for n in notifications]

@api_router.put(\"/notifications/{notification_id}/read\")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    await db.notifications.update_one(
        {'_id': ObjectId(notification_id), 'student_id': current_user['_id']},
        {'$set': {'read': True}}
    )
    return {'message': 'Notification marked as read'}

# ==================== ANNOUNCEMENTS ====================

@api_router.get(\"/announcements\")
async def get_announcements(current_user: dict = Depends(get_current_user)):
    # Get announcements for all or specific year
    year_target = f\"year{current_user['year']}\"
    announcements = await db.announcements.find({
        'target_audience': {'$in': ['all', year_target]}
    }).sort('created_at', -1).limit(20).to_list(20)
    
    return [serialize_doc(a) for a in announcements]

# ==================== ADMIN/SEED DATA (FOR TESTING) ====================

@api_router.post(\"/admin/seed-data\")
async def seed_data():
    \"\"\"Seed initial data for testing\"\"\"
    # Clear existing data
    await db.subjects.delete_many({})
    await db.assignments.delete_many({})
    await db.quizzes.delete_many({})
    await db.announcements.delete_many({})
    
    # Seed subjects for Semester 6 (3rd year)
    subjects_data = [
        {'code': '23CSE311', 'name': 'Software Engineering', 'category': 'ENGG', 'credits': 4, 'year': 3, 'semester': 6, 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 2, 'evaluation_pattern': '70-30'},
        {'code': '23CSE312', 'name': 'Distributed Systems', 'category': 'ENGG', 'credits': 4, 'year': 3, 'semester': 6, 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 2, 'evaluation_pattern': '70-30'},
        {'code': '23CSE313', 'name': 'Foundations of Cyber Security', 'category': 'CSE', 'credits': 3, 'year': 3, 'semester': 6, 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 0, 'evaluation_pattern': '70-30'},
        {'code': '23CSE314', 'name': 'Compiler Design', 'category': 'CSE', 'credits': 4, 'year': 3, 'semester': 6, 'lecture_hours': 3, 'tutorial_hours': 0, 'practical_hours': 2, 'evaluation_pattern': '70-40'},
        {'code': '23CSE399', 'name': 'Project Phase-I', 'category': 'PRJ', 'credits': 3, 'year': 3, 'semester': 6, 'lecture_hours': 0, 'tutorial_hours': 0, 'practical_hours': 6, 'evaluation_pattern': '70-30'},
        {'code': '23LSE311', 'name': 'Life Skills for Engineers IV', 'category': 'HUM', 'credits': 2, 'year': 3, 'semester': 6, 'lecture_hours': 1, 'tutorial_hours': 0, 'practical_hours': 2, 'evaluation_pattern': '50-50'},
    ]
    
    subject_ids = []
    for subject in subjects_data:
        result = await db.subjects.insert_one(subject)
        subject_ids.append(str(result.inserted_id))
    
    # Create sample assignment
    if subject_ids:
        assignment = {
            'subject_id': subject_ids[0],
            'title': 'Software Requirements Specification',
            'description': 'Create an SRS document for a library management system',
            'deadline': datetime.utcnow() + timedelta(days=7),
            'max_marks': 20,
            'file_base64': None,
            'created_at': datetime.utcnow()
        }
        await db.assignments.insert_one(assignment)
        
        # Create sample quiz
        quiz = {
            'subject_id': subject_ids[1],
            'title': 'Distributed Systems - Unit 1',
            'description': 'Quiz on basic concepts of distributed systems',
            'duration_minutes': 30,
            'max_marks': 10,
            'questions': [
                {
                    'question': 'What is a distributed system?',
                    'options': [
                        'A system with multiple processors',
                        'A collection of autonomous computers connected through a network',
                        'A single computer system',
                        'A mainframe computer'
                    ],
                    'correct_answer': 1
                },
                {
                    'question': 'Which is NOT a characteristic of distributed systems?',
                    'options': [
                        'Concurrency',
                        'No global clock',
                        'Single point of failure',
                        'Independent failures'
                    ],
                    'correct_answer': 2
                }
            ],
            'start_time': datetime.utcnow(),
            'end_time': datetime.utcnow() + timedelta(days=30),
            'created_at': datetime.utcnow()
        }
        await db.quizzes.insert_one(quiz)
    
    # Create announcements
    announcements = [
        {
            'title': 'Mid-Semester Exams',
            'message': 'Mid-semester examinations will be held from 15th March to 25th March 2025',
            'target_audience': 'all',
            'priority': 'high',
            'created_at': datetime.utcnow()
        },
        {
            'title': 'Project Submission Deadline',
            'message': 'All 3rd year students must submit their project proposals by 10th March 2025',
            'target_audience': 'year3',
            'priority': 'high',
            'created_at': datetime.utcnow()
        }
    ]
    
    for announcement in announcements:
        await db.announcements.insert_one(announcement)
    
    return {'message': 'Sample data seeded successfully', 'subjects_created': len(subject_ids)}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[\"*\"],
    allow_methods=[\"*\"],
    allow_headers=[\"*\"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event(\"shutdown\")
async def shutdown_db_client():
    client.close()
"