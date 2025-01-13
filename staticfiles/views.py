# MAJOR/FIR/accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import PoliceUserCreationForm, LoginForm
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from .models import FIR, LawSection 
import json
import base64
import os
import logging
from django.conf import settings
from datetime import datetime
import mimetypes
from .speech_processor import SpeechProcessor
from pathlib import Path
from .law_suggestion import LawSuggestionSystem
from django.contrib.auth.hashers import check_password
logger = logging.getLogger(__name__)
# Initialize the system
law_system = LawSuggestionSystem()
law_system.load_laws()
@login_required
def view_fir(request, fir_number):
    fir = get_object_or_404(FIR, number=fir_number)  
    try:
        # Get singleton instance
        law_system = LawSuggestionSystem()
        suggested_laws = law_system.suggest_laws(fir.statement)       
        formatted_suggestions = [
            {
                'section': suggestion['section'],
                'score': suggestion['similarity_score'],
                'matching_terms': suggestion['matching_terms']
            }
            for suggestion in suggested_laws
            if suggestion['section'] is not None
        ]        
    except Exception as e:
        logger.error(f"Error getting law suggestions for FIR {fir_number}: {str(e)}")
        formatted_suggestions = []
    context = {
        'fir': fir,
        'suggested_laws': formatted_suggestions,
        'audio_url': f'/serve_audio/{fir_number}/' if fir.audio_file else None,
    }   
    return render(request, 'accounts/view_fir.html', context)

def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/home.html')

def signup_view(request):
    if request.method == 'POST':
        form = PoliceUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = PoliceUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

def suggest_laws(self,statement, threshhold=0.5, top_k=5):
    """
    Analyze statement and return relevant law sections
    """
    logger.info("Starting law suggestion process...")   
    if not hasattr(self, 'laws_df') or self.laws_df is None:
        logger.info("Loading laws...")
        self.load_laws()
    logger.info(f"Laws DataFrame size: {len(self.laws_df) if self.laws_df is not None else 'None'}")
    logger.info(f"Law embeddings shape: {self.law_embeddings.shape if self.law_embeddings is not None else 'None'}")
    logger.info(f"Model loaded: {self.model is not None}")
    logger.info(f"Statement: {statement}")
    statement_words = set(statement.lower().split())
    relevant_sections = []   
    for section in LawSection.objects.all():
        section_keywords = set(section.get_keywords_list())
        # If any keyword from the section matches words in the statement
        if section_keywords.intersection(statement_words):
            relevant_sections.append(section)   
    return relevant_sections

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                return redirect('dashboard')
            else:
                messages.error(
                    request, 'Invalid username or password. Please try again.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def dashboard_view(request):
    recent_firs = FIR.objects.order_by('-date_filed')[:5]  # Get the 10 most recent FIRs
    return render(request, 'accounts/dashboard.html', {
        'recent_firs': recent_firs
    })

@csrf_exempt
@require_http_methods(["POST"])
def submit_fir(request):
    try:
        # Extract form data
        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        aadhar_number = request.POST.get('aadhar_number')
        mobile_number = request.POST.get('mobile_number')
        incident_place = request.POST.get('incident_place')
        statement = request.POST.get('statement', '')
        
        # Initialize audio_path
        audio_path = None
        full_path = None
        
        # Handle audio file
        audio_blob = request.FILES.get('audio_blob')
        if audio_blob:
            try:
                print(f"Received audio file: {audio_blob.name}")
                
                # Create a unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"fir_audio_{timestamp}_{aadhar_number}.webm"
                
                # Create relative path for database
                audio_path = f'fir_audio/{filename}'
                
                # Create absolute path for file saving
                media_root = Path(settings.MEDIA_ROOT)
                full_path = media_root / 'fir_audio' / filename
                
                # Ensure directory exists
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                print(f"Saving audio to: {full_path}")
                
                # Save the file
                with open(full_path, 'wb+') as destination:
                    for chunk in audio_blob.chunks():
                        destination.write(chunk)
                        
                print("Audio file saved successfully")
                print(f"Audio file type: {type(audio_blob)}")
                print(f"Audio file size: {audio_blob.size}")
                print(f"Audio path being passed to processor: {audio_path}")
                print(f"Full path of saved file: {full_path}")
                # Process speech to text
                if full_path:
                    try:
                        processor = SpeechProcessor()
                        extracted_text = processor.extract_text(audio_path)
                        print(f"Extracted text: {extracted_text}")
                        
                        if extracted_text and extracted_text != "Speech recognition could not understand the audio":
                            statement = extracted_text
                    except Exception as e:
                        print(f"Speech processing error: {str(e)}")
                
            except Exception as e:
                print(f"Error handling audio file: {str(e)}")
                
        # Create and save the FIR
        fir = FIR.objects.create(
            complainant_name=full_name,
            complainant_address=address,
            complainant_aadhar=aadhar_number,
            complainant_phone=mobile_number,
            incident_place=incident_place,
            statement=statement,
            audio_file=audio_path if audio_path else None,
            status='Open'
        )
        
        return JsonResponse({
            'success': True,
            'fir_number': fir.number
        })
        
    except Exception as e:
        print(f"Error in submit_fir: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def serve_audio(request, fir_number):
    """Serve the audio file for a specific FIR"""
    fir = get_object_or_404(FIR, number=fir_number)    
    if fir.audio_file:
        file_path = os.path.join(settings.MEDIA_ROOT, str(fir.audio_file))
        if os.path.exists(file_path):
            content_type, _ = mimetypes.guess_type(file_path)
            response = FileResponse(open(file_path, 'rb'), content_type=content_type)
            return response
    
    return JsonResponse({'error': 'Audio file not found'}, status=404)

@require_POST
def verify_password(request):
    try:
        data = json.loads(request.body)
        password = data.get('password')
        
        # Check if password matches the logged-in user's password
        if check_password(password, request.user.password):
            return JsonResponse({'success': True})
        return JsonResponse({'success': False})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
def update_fir_status(request):
    try:
        data = json.loads(request.body)
        fir_number = data.get('fir_number')
        new_status = data.get('new_status')
        
        # Update FIR status
        fir = FIR.objects.get(number=fir_number)
        fir.status = new_status
        fir.save()
        
        return JsonResponse({'success': True})
    except FIR.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'FIR not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})