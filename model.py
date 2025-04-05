import spacy
from sentence_transformers import SentenceTransformer, util
from Levenshtein import ratio
import numpy as np
import re

# Load Spacy model for Named Entity Recognition (NER) and linguistic analysis
nlp = spacy.load("en_core_web_sm")

# Load SentenceTransformer for semantic similarity
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def get_similarity(actual_answer, student_answer):
    """Evaluate student answer using multiple dimensions of assessment."""
    
    # Clean and normalize answers
    actual_answer_clean = clean_text(actual_answer)
    student_answer_clean = clean_text(student_answer)
    
    # Extract key entities and facts
    actual_entities = extract_entities(actual_answer_clean)
    student_entities = extract_entities(student_answer_clean)
    
    # Calculate factual accuracy
    factual_accuracy = check_factual_accuracy(actual_entities, student_entities)
    
    # Calculate semantic similarity
    similarity = calculate_similarity(actual_answer_clean, student_answer_clean)
    
    # Calculate content completeness
    content_completeness = calculate_completeness(actual_answer_clean, student_answer_clean)
    
    # Calculate length ratio (penalize answers that are too short)
    word_count_actual = len(actual_answer_clean.split())
    word_count_student = len(student_answer_clean.split())
    length_ratio = min(word_count_student / max(word_count_actual * 0.6, 1), 1.2)
    
    # Detect contradictory information
    contradictions = detect_contradictions(actual_answer_clean, student_answer_clean)
    
    # Adjust weights based on answer type and length
    if word_count_actual <= 20:  # Short factual answers
        factual_weight = 0.7
        semantic_weight = 0.2
        completeness_weight = 0.1
    elif word_count_actual <= 50:  # Medium-length answers
        factual_weight = 0.5
        semantic_weight = 0.3
        completeness_weight = 0.2
    else:  # Long explanatory answers
        factual_weight = 0.4
        semantic_weight = 0.3
        completeness_weight = 0.3
    
    # Calculate final score with weighted components
    final_score = (
        factual_weight * factual_accuracy + 
        semantic_weight * similarity + 
        completeness_weight * content_completeness
    )
    
    # Apply length penalty for very short answers
    if length_ratio < 0.7:
        final_score *= length_ratio
    
    # Apply contradiction penalty if detected
    if contradictions:
        final_score *= 0.8  # 20% reduction for contradictions
    
    return round(final_score, 3), generate_feedback(final_score, factual_accuracy, length_ratio, content_completeness, contradictions)

def clean_text(text):
    """Clean and normalize text for better comparison."""
    # Convert to lowercase
    text = text.lower()
    # Standardize units and symbols
    text = re.sub(r'(\d+)\s*°\s*c', r'\1 degrees celsius', text)
    text = re.sub(r'(\d+)\s*km', r'\1 kilometers', text)
    text = re.sub(r'(\d+)\s*miles', r'\1 miles', text)
    # Replace common abbreviations
    text = re.sub(r'\bww2\b', 'world war 2', text)
    text = re.sub(r'\bu\.s\.a?\b', 'united states', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_entities(text):
    """Extract named entities, important nouns, numbers, and key facts from the text."""
    doc = nlp(text)
    
    # Extract named entities, nouns, and numbers
    entities = set()
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"]:
            entities.add(token.lemma_.lower())
        elif token.pos_ == "NUM":
            entities.add(token.text.lower())
    
    # Extract named entities
    for ent in doc.ents:
        entities.add(ent.text.lower())
    
    # Extract noun chunks (important concepts)
    for chunk in doc.noun_chunks:
        if len(chunk.text.split()) <= 3:  # Limit to reasonable size chunks
            entities.add(chunk.text.lower())
    
    # Extract numerical facts (with context)
    for token in doc:
        if token.like_num:
            # Get context (2 words before and after)
            start = max(0, token.i - 2)
            end = min(len(doc), token.i + 3)
            context = doc[start:end].text.lower()
            entities.add(context)
    
    return entities

def check_factual_accuracy(actual_entities, student_entities):
    """Check if key facts and entities are retained in the student answer."""
    if not actual_entities:
        return 1.0
    
    # Calculate percentage of actual entities that have a match in student entities
    matched_count = 0
    for ent in actual_entities:
        if get_best_match(ent, student_entities):
            matched_count += 1
    
    return round(matched_count / len(actual_entities), 2)

def get_best_match(entity, student_entities):
    """Find best match for an entity in student answer with fuzzy matching."""
    # Direct match
    if entity in student_entities:
        return True
    
    # Fuzzy match for longer entities
    if len(entity) > 3:
        for student_entity in student_entities:
            # Use higher threshold for short entities to prevent false matches
            min_threshold = 0.8 if len(entity) < 6 else 0.7
            if ratio(entity, student_entity) > min_threshold:
                return True
    
    return False

def calculate_similarity(actual_answer, student_answer):
    """Compute semantic similarity between the two answers."""
    embeddings1 = model.encode(actual_answer, convert_to_tensor=True)
    embeddings2 = model.encode(student_answer, convert_to_tensor=True)
    return round(util.pytorch_cos_sim(embeddings1, embeddings2)[0][0].item(), 3)

def calculate_completeness(actual_answer, student_answer):
    """Assess how complete the student's answer is compared to the expected answer."""
    # Split answers into sentences
    actual_sentences = nlp(actual_answer).sents
    
    # Count key concepts in each
    actual_doc = nlp(actual_answer)
    student_doc = nlp(student_answer)
    
    # Extract key concepts (entities, main verbs, etc.)
    actual_concepts = set()
    for token in actual_doc:
        if token.pos_ in ["NOUN", "PROPN", "VERB"] and not token.is_stop:
            actual_concepts.add(token.lemma_.lower())
    
    student_concepts = set()
    for token in student_doc:
        if token.pos_ in ["NOUN", "PROPN", "VERB"] and not token.is_stop:
            student_concepts.add(token.lemma_.lower())
    
    # Calculate concept overlap
    if not actual_concepts:
        return 1.0
    
    # Count concepts that match (exact or fuzzy)
    matched_concepts = 0
    for concept in actual_concepts:
        if concept in student_concepts or any(ratio(concept, sc) > 0.85 for sc in student_concepts if len(concept) > 3):
            matched_concepts += 1
    
    return round(matched_concepts / len(actual_concepts), 2)

def detect_contradictions(actual_answer, student_answer):
    """Detect contradictory information between the actual and student answers."""
    # Detect numbers and their context
    def extract_numerical_facts(text):
        doc = nlp(text)
        numerical_facts = {}
        
        for token in doc:
            if token.like_num:
                # Find the nearest noun to associate this number with
                associated_noun = None
                for potential_noun in doc:
                    if potential_noun.pos_ in ["NOUN", "PROPN"] and abs(potential_noun.i - token.i) <= 3:
                        associated_noun = potential_noun.lemma_.lower()
                        break
                
                if associated_noun:
                    numerical_facts[associated_noun] = token.text
        
        return numerical_facts
    
    actual_facts = extract_numerical_facts(actual_answer)
    student_facts = extract_numerical_facts(student_answer)
    
    # Look for contradictions (same concept, different numbers)
    contradictions = []
    for concept, actual_value in actual_facts.items():
        if concept in student_facts and student_facts[concept] != actual_value:
            # Check if the numbers are significantly different (not just rounding differences)
            try:
                actual_num = float(re.sub(r'[^0-9.]', '', actual_value))
                student_num = float(re.sub(r'[^0-9.]', '', student_facts[concept]))
                
                # If values differ by more than 10%, consider it a contradiction
                if abs(actual_num - student_num) / max(actual_num, 1) > 0.1:
                    contradictions.append((concept, actual_value, student_facts[concept]))
            except:
                # If we can't convert to numbers, consider it a contradiction anyway
                contradictions.append((concept, actual_value, student_facts[concept]))
    
    return contradictions

def generate_feedback(score, factual_accuracy, length_ratio, completeness, contradictions=None):
    """Generate detailed feedback based on multiple assessment dimensions."""
    
    # Very short answers get specific feedback
    if length_ratio < 0.5:
        return "⚠️ Answer is too brief. Provide more details."
    
    # Contradictions take priority
    if contradictions and len(contradictions) > 0:
        return "⚠️ Contains contradictory information. Please check your facts."
    
    # Major factual errors
    if factual_accuracy < 0.4:
        return "⚠️ Significant factual errors. Requires substantial revision."
    
    # Low completeness but otherwise accurate
    if completeness < 0.4 and factual_accuracy > 0.7:
        return "⚠️ Answer covers only some key points. Expand your response to include more details."
    
    # Generate general feedback based on overall score
    if score > 0.9:
        return "✅ Excellent answer! Well-matched with key facts."
    elif score > 0.8:
        return "✅ Very good answer! Accurate and well-structured."
    elif score > 0.7:
        return "👍 Good answer with minor improvements needed."
    elif score > 0.5:
        return "🤔 Partially correct. Needs more specific details."
    elif score > 0.3:
        return "⚠️ Answer has some correct elements but needs significant improvement."
    else:
        return "⚠️ Significant errors. Requires substantial revision."