# accounts/law_suggestion.py
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from django.conf import settings
from pathlib import Path
from django.core.cache import cache
from .models import LawSection
import logging

logger = logging.getLogger(__name__)

class LawSuggestionSystem:
    _instance = None
    _initialized = False   
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LawSuggestionSystem, cls).__new__(cls)
        return cls._instance
    def __init__(self):
        # Only initialize if explicitly called via initialize()
        pass
    def initialize(self):
        """Explicit initialization method"""
        if not self._initialized:
            try:
                logger.info("Initializing BERT model...")
                self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
                self.model = AutoModel.from_pretrained('bert-base-uncased')
                self.laws_df = None
                self.law_embeddings = None               
                # Cache check moved to load_laws to avoid early DB access
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize LawSuggestionSystem: {str(e)}")
                self.tokenizer = None
                self.model = None
    def load_laws(self):
        """Load laws from Excel file and update database"""
        logger.info("Starting load_laws...")
        if not self._initialized:
            logger.info("System not initialized, initializing now...")
            self.initialize()
        excel_path = settings.DATA_DIR / 'laws.xlsx'
        logger.info(f"Loading from {excel_path}")       
        try:
            # Try to get from cache first
            cached_embeddings = cache.get('law_embeddings')
            if cached_embeddings is not None:
                self.law_embeddings = cached_embeddings
                self.laws_df = cache.get('laws_df')
                return
            self.laws_df = pd.read_excel(excel_path)
            logger.info(f"Successfully loaded {len(self.laws_df)} laws from {excel_path}")           
            # Compute embeddings if BERT is available
            if self.model is not None:
                combined_texts = [
                    f"{row['Description']} {row['Keywords']}"
                    for _, row in self.laws_df.iterrows()
                ]
                self.law_embeddings = self._get_embeddings(combined_texts)
                # Cache the embeddings and dataframe
                cache.set('law_embeddings', self.law_embeddings, timeout=86400)
                cache.set('laws_df', self.laws_df, timeout=86400)
                logger.info("Successfully computed and cached law embeddings")           
        except Exception as e:
            logger.error(f"Error loading laws file: {str(e)}")
            self._load_from_database()
    def _load_from_database(self):
        """Fallback method to load laws from database"""
        try:
            laws = LawSection.objects.all()
            if not laws.exists():
                logger.warning("No laws found in database")
                self.laws_df = pd.DataFrame()
                return
            data = {
                'SectionNumber': [],
                'Description': [],
                'Keywords': [],
                'Penalties': []
            }            
            for law in laws:
                data['SectionNumber'].append(f"{law.act_name} {law.section_number}")
                data['Description'].append(law.description)
                data['Keywords'].append(law.keywords)
                data['Penalties'].append(law.punishment)            
            self.laws_df = pd.DataFrame(data)
            logger.info("Successfully loaded laws from database")            
        except Exception as e:
            logger.error(f"Error loading laws from database: {str(e)}")
            self.laws_df = pd.DataFrame()
    def _get_embeddings(self, texts):
        """Get BERT embeddings for a list of texts"""
        if not self.model:
            return None            
        embeddings = []
        with torch.no_grad():
            for text in texts:
                inputs = self.tokenizer(
                    text, 
                    return_tensors='pt', 
                    padding=True, 
                    truncation=True, 
                    max_length=512
                )
                outputs = self.model(**inputs)
                embedding = outputs.last_hidden_state[:, 0, :].numpy()
                embeddings.append(embedding[0])
        return np.array(embeddings)
    def suggest_laws(self, statement, threshold=0.5, top_k=5):
        """Suggest most relevant laws for a given statement"""
        logger.info("Starting law suggestion process...")
        if not hasattr(self, 'laws_df') or self.laws_df is None:
            logger.info("Loading laws...")
            self.load_laws()
            logger.info(f"Laws DataFrame size: {len(self.laws_df) if self.laws_df is not None else 'None'}")
            logger.info(f"Law embeddings shape: {self.law_embeddings.shape if self.law_embeddings is not None else 'None'}")
            logger.info(f"Model loaded: {self.model is not None}")
            logger.info(f"Statement: {statement}")
        if self.model is None or self.law_embeddings is None:
            return self._fallback_suggest_laws(statement, top_k)
        try:
            statement_embedding = self._get_embeddings([statement])
            similarities = cosine_similarity(statement_embedding, self.law_embeddings)[0]            
            top_indices = similarities.argsort()[-top_k:][::-1]
            suggestions = []
            
            for idx in top_indices:
                if similarities[idx] >= threshold:
                    section_parts = self.laws_df.iloc[idx]['SectionNumber'].split()
                    act_name = section_parts[0]
                    section_number = ' '.join(section_parts[1:]) if len(section_parts) > 1 else section_parts[0]            
                    try:
                        law_section = LawSection.objects.get(
                            act_name=act_name,
                            section_number=section_number
                        )                
                        suggestions.append({
                            'section': law_section,
                            'similarity_score': float(similarities[idx]),
                            'matching_terms': self.laws_df.iloc[idx]['Keywords'].split(',')
                        })
                    except LawSection.DoesNotExist:
                        continue         
            return suggestions     
        except Exception as e:
            logger.error(f"Error in BERT-based suggestion: {str(e)}")
            return self._fallback_suggest_laws(statement, top_k)
    def _fallback_suggest_laws(self, statement, top_k=5):
        """Simple keyword-based fallback method"""
        suggestions = []
        statement_words = set(statement.lower().split())    
        for law in LawSection.objects.all():
            keywords = set(k.strip().lower() for k in law.keywords.split(','))
            matching_words = keywords.intersection(statement_words)
            
            if matching_words:
                suggestions.append({
                    'section': law,
                    'similarity_score': len(matching_words) / len(keywords),
                    'matching_terms': list(matching_words)
                })     
        return sorted(suggestions, 
                     key=lambda x: x['similarity_score'], 
                     reverse=True)[:top_k]