"""
Ingestion Pipeline using Docling
--------------------------------
Extracts:
- Metadata
- Paragraphs
- Tables (if present)
- Entity extraction using spaCy NER (with fallback to simple extraction)

Supported formats: txt, pdf, docx, csv

Note: For spaCy NER, install spaCy and download a model:
    pip install spacy
    python -m spacy download en_core_web_sm
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import ConversionStatus
import hashlib

# Try to import spaCy for advanced NER
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None


class IngestionPipeline:
    SUPPORTED_EXT = {".txt", ".pdf", ".docx", ".csv"}

    def __init__(self, use_spacy: bool = True, spacy_model: str = "en_core_web_sm"):
        """
        Initialize the Docling document converter and spaCy NER model.
        
        Args:
            use_spacy: If True, use spaCy for entity extraction (default: True)
            spacy_model: spaCy model to use (default: "en_core_web_sm")
        """
        # Use default pipeline options from the installed Docling version.
        # The constructor signature may change across versions, so we avoid
        # passing deprecated/removed keyword arguments like `pipeline_options`.
        self.converter = DocumentConverter()
        
        # Initialize spaCy NER model
        self.use_spacy = use_spacy and SPACY_AVAILABLE
        self.spacy_model_name = spacy_model
        self.nlp = None
        
        if self.use_spacy:
            try:
                # Try to load the specified model
                self.nlp = spacy.load(spacy_model)
                print(f"✅ Loaded spaCy model: {spacy_model}")
            except OSError:
                # Model not found, try to download it or use a fallback
                try:
                    # Try loading a smaller model or default
                    if spacy_model != "en_core_web_sm":
                        self.nlp = spacy.load("en_core_web_sm")
                        print(f"⚠️  Model {spacy_model} not found, using en_core_web_sm")
                    else:
                        # Model needs to be downloaded
                        print(f"⚠️  spaCy model {spacy_model} not found. Please run: python -m spacy download {spacy_model}")
                        print("   Falling back to simple entity extraction.")
                        self.use_spacy = False
                except Exception as e:
                    print(f"⚠️  Could not load spaCy model: {e}")
                    print("   Falling back to simple entity extraction.")
                    self.use_spacy = False
            except Exception as e:
                print(f"⚠️  Error initializing spaCy: {e}")
                self.use_spacy = False

    def run(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single document and return structured JSON.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"No such file: {file_path}")

        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_EXT:
            raise ValueError(f"Unsupported file extension: {ext}")

        # For plain text files, bypass Docling and read directly.
        if ext == ".txt":
            raw_text = path.read_text(encoding="utf-8", errors="ignore")
            tables = []
        else:
            # Convert document using Docling for supported rich formats
            result = self.converter.convert(str(path))
            if result.status != ConversionStatus.SUCCESS:
                raise RuntimeError(f"Docling conversion failed for {file_path}")

            doc = result.document

            # Extract raw text - Docling uses export_to_text() method
            try:
                raw_text = doc.export_to_text() if hasattr(doc, "export_to_text") else ""
            except Exception:
                # Fallback: try to get text from body or other attributes
                raw_text = getattr(doc, "text", "") or getattr(doc, "body", "") or ""
                # If body is an object, try to convert it
                if hasattr(raw_text, "export_to_text"):
                    raw_text = raw_text.export_to_text()
                elif not isinstance(raw_text, str):
                    raw_text = str(raw_text) if raw_text else ""

            # Extract tables if available
            tables = getattr(doc, "tables", [])

        # Split text into paragraphs
        paragraphs = self._split_into_paragraphs(raw_text)

        # Extract entities using spaCy NER (with fallback to simple extraction)
        if self.use_spacy and self.nlp:
            entities, relationships = self._extract_entities_spacy(paragraphs)
        else:
            entities, relationships = self._extract_entities_simple(paragraphs)

        # Metadata
        metadata = {
            "filename": path.name,
            "filesize": path.stat().st_size,
            "extension": path.suffix
        }

        return {
            "source": path.name,
            "type": ext.replace(".", ""),
            "metadata": metadata,
            "paragraphs": paragraphs,
            "tables": tables,
            "entities": entities,
            "relationships": relationships,
        }

    # -------------------- Internal Methods --------------------
    def _split_into_paragraphs(self, raw_text: str) -> List[Dict[str, Any]]:
        """
        Split text into paragraphs. Uses multiple strategies to ensure full text is captured:
        1. Split by double newlines (\n\n) - standard paragraph breaks
        2. If that yields very few paragraphs, also try single newlines
        3. Merge very short fragments with previous paragraph to avoid truncation
        """
        paragraphs = []
        
        # First, try splitting by double newlines (standard paragraph breaks)
        blocks = raw_text.split("\n\n")
        
        # If we get very few blocks and text is long, also try single newlines
        if len(blocks) < 3 and len(raw_text) > 500:
            # Try splitting by single newlines and then grouping
            lines = raw_text.split("\n")
            blocks = []
            current_block = []
            for line in lines:
                line = line.strip()
                if line:
                    current_block.append(line)
                else:
                    if current_block:
                        blocks.append(" ".join(current_block))
                        current_block = []
            if current_block:
                blocks.append(" ".join(current_block))
        
        # Process blocks and merge very short ones to avoid truncation
        idx = 0
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            
            # If block is very short (< 50 chars) and we have a previous paragraph, merge it
            if len(block) < 50 and paragraphs:
                # Merge with previous paragraph to avoid truncation
                paragraphs[-1]["text"] += " " + block
            else:
                # Normalize whitespace but preserve full content
                # Replace multiple spaces with single space, but keep newlines within paragraph
                normalized = " ".join(block.split())
                if normalized:  # Only add if not empty after normalization
                    paragraphs.append({
                        "id": f"p{idx+1}",
                        "text": normalized
                    })
                    idx += 1
        
        # If we still have no paragraphs but have text, create one paragraph with all text
        if not paragraphs and raw_text.strip():
            normalized = " ".join(raw_text.split())
            if normalized:
                paragraphs.append({
                    "id": "p1",
                    "text": normalized
                })
        
        return paragraphs

    def _extract_entities_spacy(self, paragraphs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract entities using spaCy NER (Named Entity Recognition).
        Uses spaCy's advanced NLP capabilities for accurate entity extraction.
        
        Args:
            paragraphs: List of paragraph dictionaries with 'id' and 'text' keys
            
        Returns:
            Tuple of (entities, relationships) where:
            - entities: List of entity dicts with id, label, metadata
            - relationships: List of relationship dicts with start, end, type, metadata
        """
        entities = []
        relationships = []
        entity_map = {}  # Maps entity_id -> entity dict
        entity_text_to_id = {}  # Maps normalized entity text -> entity_id
        
        # Map spaCy labels to our entity labels
        spacy_to_label = {
            "PERSON": "Person",
            "ORG": "Company",
            "GPE": "Location",  # Geopolitical entity (countries, cities, etc.)
            "LOC": "Location",  # Non-geopolitical locations
            "MONEY": "Concept",
            "DATE": "Concept",
            "TIME": "Concept",
            "PERCENT": "Concept",
            "QUANTITY": "Concept",
            "EVENT": "Concept",
            "PRODUCT": "Concept",
            "WORK_OF_ART": "Concept",
            "LAW": "Concept",
            "LANGUAGE": "Concept",
            "NORP": "Concept",  # Nationalities or religious/political groups
        }
        
        # Process each paragraph
        for para in paragraphs:
            para_text = para["text"]
            para_entities = []
            
            # Process paragraph with spaCy
            doc = self.nlp(para_text)
            
            # Extract named entities
            for ent in doc.ents:
                # Skip very short entities (likely false positives)
                if len(ent.text.strip()) < 2:
                    continue
                
                # Get our label mapping
                entity_label = spacy_to_label.get(ent.label_, "Concept")
                
                # Create normalized entity ID from text
                entity_text_normalized = ent.text.strip().lower().replace(" ", "_")
                # Create unique ID using hash to handle duplicates
                entity_id_base = f"e_{entity_text_normalized}"
                entity_id = hashlib.md5(f"{entity_id_base}_{ent.label_}".encode()).hexdigest()[:12]
                entity_id = f"e_{entity_id}"
                
                # Check if we've seen this entity before (by text and label)
                entity_key = (ent.text.strip().lower(), ent.label_)
                if entity_key not in entity_text_to_id:
                    entity_text_to_id[entity_key] = entity_id
                    
                    # Create entity dict
                    entity_dict = {
                        "id": entity_id,
                        "label": entity_label,
                        "metadata": {
                            "name": ent.text.strip(),
                            "spacy_label": ent.label_,
                            "spacy_label_desc": spacy.explain(ent.label_) if SPACY_AVAILABLE and hasattr(spacy, 'explain') else ent.label_,
                            "start_char": ent.start_char,
                            "end_char": ent.end_char
                        }
                    }
                    entity_map[entity_id] = entity_dict
                    entities.append(entity_dict)
                
                entity_id = entity_text_to_id[entity_key]
                para_entities.append(entity_id)
            
            # Extract relationships using dependency parsing
            # Look for common relationship patterns
            for token in doc:
                # Pattern: PERSON works at ORG
                if token.dep_ == "nsubj" and token.head.pos_ == "VERB":
                    # Find the subject (person) and object (company/location)
                    subject_ent = None
                    object_ent = None
                    
                    # Find entity for subject
                    for ent in doc.ents:
                        if ent.start <= token.i < ent.end:
                            if ent.label_ == "PERSON":
                                subject_ent = ent
                            break
                    
                    # Find entity for object (dobj or pobj)
                    for child in token.head.children:
                        if child.dep_ in ["dobj", "pobj", "prep"]:
                            for ent in doc.ents:
                                if ent.start <= child.i < ent.end:
                                    if ent.label_ in ["ORG", "GPE", "LOC"]:
                                        object_ent = ent
                                    break
                    
                    # Create relationship if we found both
                    if subject_ent and object_ent:
                        subj_id = entity_text_to_id.get((subject_ent.text.strip().lower(), subject_ent.label_))
                        obj_id = entity_text_to_id.get((object_ent.text.strip().lower(), object_ent.label_))
                        
                        if subj_id and obj_id:
                            # Determine relationship type based on verb
                            verb_text = token.head.text.lower()
                            rel_type = "RELATED_TO"
                            
                            if any(v in verb_text for v in ["work", "employed", "hired"]):
                                rel_type = "WORKS_AT"
                            elif any(v in verb_text for v in ["live", "located", "based"]):
                                rel_type = "LOCATED_IN"
                            elif any(v in verb_text for v in ["found", "create", "establish"]):
                                rel_type = "FOUNDED"
                            elif any(v in verb_text for v in ["own", "acquire", "purchase"]):
                                rel_type = "OWNS"
                            
                            # Check if relationship already exists
                            rel_key = (subj_id, obj_id, rel_type)
                            if not any(r["start"] == subj_id and r["end"] == obj_id and r["type"] == rel_type 
                                     for r in relationships):
                                relationships.append({
                                    "start": subj_id,
                                    "end": obj_id,
                                    "type": rel_type,
                                    "metadata": {
                                        "source": para["id"],
                                        "verb": token.head.text,
                                        "confidence": "medium"
                                    }
                                })
            
            # Also create simple co-occurrence relationships for entities in same paragraph
            # If multiple entities of different types appear together, create relationships
            person_entities = [eid for eid in para_entities 
                             if entity_map.get(eid, {}).get("label") == "Person"]
            company_entities = [eid for eid in para_entities 
                              if entity_map.get(eid, {}).get("label") == "Company"]
            location_entities = [eid for eid in para_entities 
                               if entity_map.get(eid, {}).get("label") == "Location"]
            
            # Person-Company relationships
            for person_id in person_entities:
                for company_id in company_entities:
                    rel_key = (person_id, company_id, "WORKS_AT")
                    if not any(r["start"] == person_id and r["end"] == company_id and r["type"] == "WORKS_AT" 
                             for r in relationships):
                        relationships.append({
                            "start": person_id,
                            "end": company_id,
                            "type": "WORKS_AT",
                            "metadata": {
                                "source": para["id"],
                                "confidence": "low",
                                "method": "co_occurrence"
                            }
                        })
            
            # Company-Location relationships
            for company_id in company_entities:
                for location_id in location_entities:
                    rel_key = (company_id, location_id, "LOCATED_IN")
                    if not any(r["start"] == company_id and r["end"] == location_id and r["type"] == "LOCATED_IN" 
                             for r in relationships):
                        relationships.append({
                            "start": company_id,
                            "end": location_id,
                            "type": "LOCATED_IN",
                            "metadata": {
                                "source": para["id"],
                                "confidence": "low",
                                "method": "co_occurrence"
                            }
                        })
            
            # Store entity_ids in paragraph for later use
            para["entity_ids"] = para_entities
        
        return entities, relationships

    def _extract_entities_simple(self, paragraphs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Simple entity extraction from paragraphs.
        Uses keyword-based extraction for common entities.
        In production, use NER models like spaCy or transformers.
        """
        entities = []
        relationships = []
        entity_map = {}
        
        # Common entity patterns (can be expanded)
        person_keywords = ["alice", "bob", "john", "mary", "david", "sarah", "engineer", "developer", "manager", "director", "ceo", "cto"]
        company_keywords = ["company", "corporation", "inc", "ltd", "llc", "organization", "firm", "enterprise"]
        location_keywords = ["bangalore", "mumbai", "delhi", "new york", "london", "san francisco", "city", "location"]
        tech_keywords = ["ai", "machine learning", "deep learning", "neural network", "algorithm", "database", "graph", "vector"]
        
        for para in paragraphs:
            text_lower = para["text"].lower()
            para_entities = []
            
            # Extract persons (check for person keywords first, then capitalized names)
            words = para["text"].split()
            for word in words:
                word_clean = word.strip(".,!?;:").lower()
                # Check if it's a known person keyword
                if word_clean in person_keywords:
                    entity_id = f"e_{word_clean}"
                    if entity_id not in entity_map:
                        entity_map[entity_id] = {
                            "id": entity_id,
                            "label": "Person",
                            "metadata": {"name": word.strip(".,!?;:").capitalize()}
                        }
                        entities.append(entity_map[entity_id])
                    para_entities.append(entity_id)
                # Check for capitalized names (but skip if it's a company keyword)
                elif (word[0].isupper() and len(word) > 3 and 
                      word_clean not in ["the", "this", "that", "there", "company", "corporation"] and
                      not any(ck in word_clean for ck in company_keywords)):
                    # Only add if not already added as company
                    entity_id = f"e_{word_clean}"
                    if entity_id not in entity_map:
                        entity_map[entity_id] = {
                            "id": entity_id,
                            "label": "Person",
                            "metadata": {"name": word.strip(".,!?;:")}
                        }
                        entities.append(entity_map[entity_id])
                    if entity_id not in para_entities:
                        para_entities.append(entity_id)
            
            # Extract companies/organizations (check for capitalized company names)
            # Look for capitalized words that might be company names
            words = para["text"].split()
            for i, word in enumerate(words):
                word_clean = word.strip(".,!?;:").lower()
                # Check if next word is a company keyword
                if i < len(words) - 1:
                    next_word = words[i+1].strip(".,!?;:").lower()
                    if next_word in company_keywords or any(ck in next_word for ck in company_keywords):
                        company_name = word.strip(".,!?;:")
                        entity_id = f"e_{company_name.lower().replace(' ', '_')}"
                        if entity_id not in entity_map:
                            entity_map[entity_id] = {
                                "id": entity_id,
                                "label": "Company",
                                "metadata": {"name": company_name}
                            }
                            entities.append(entity_map[entity_id])
                        para_entities.append(entity_id)
                # Also check if word itself contains company indicators
                elif any(ck in word_clean for ck in company_keywords):
                    if i > 0:
                        company_name = words[i-1].strip(".,!?;:")
                        entity_id = f"e_{company_name.lower().replace(' ', '_')}"
                        if entity_id not in entity_map:
                            entity_map[entity_id] = {
                                "id": entity_id,
                                "label": "Company",
                                "metadata": {"name": company_name}
                            }
                            entities.append(entity_map[entity_id])
                        para_entities.append(entity_id)
            
            # Extract locations
            for keyword in location_keywords:
                if keyword in text_lower:
                    entity_id = f"e_{keyword}"
                    if entity_id not in entity_map:
                        entity_map[entity_id] = {
                            "id": entity_id,
                            "label": "Location",
                            "metadata": {"name": keyword.capitalize()}
                        }
                        entities.append(entity_map[entity_id])
                    para_entities.append(entity_id)
            
            # Extract tech concepts
            for keyword in tech_keywords:
                if keyword in text_lower:
                    entity_id = f"e_{keyword.replace(' ', '_')}"
                    if entity_id not in entity_map:
                        entity_map[entity_id] = {
                            "id": entity_id,
                            "label": "Concept",
                            "metadata": {"name": keyword, "type": "technology"}
                        }
                        entities.append(entity_map[entity_id])
                    para_entities.append(entity_id)
            
            # Store entity_ids in paragraph for later use
            para["entity_ids"] = para_entities
            
            # Create relationships (simple: if person and company in same paragraph, create WORKS_AT)
            person_entities = [e for e in para_entities if entity_map.get(e, {}).get("label") == "Person"]
            company_entities = [e for e in para_entities if entity_map.get(e, {}).get("label") == "Company"]
            
            for person_id in person_entities:
                for company_id in company_entities:
                    relationships.append({
                        "start": person_id,
                        "end": company_id,
                        "type": "WORKS_AT",
                        "metadata": {"source": para["id"]}
                    })
        
        return entities, relationships
