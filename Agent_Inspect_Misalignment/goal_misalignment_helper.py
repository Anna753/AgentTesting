from typing import Dict, Set
import spacy
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

nlp = spacy.load("en_core_web_sm")

IMPORTANT_LABELS = {
    "PERSON", "ORG", "GPE", "LOC", "FAC", "NORP",
    "PRODUCT", "EVENT", "WORK_OF_ART", "LAW", "LANGUAGE",
    "DATE", "TIME", "MONEY", "PERCENT", "QUANTITY",
    "ORDINAL", "CARDINAL"
}

model_names = {
    "bart": "facebook/bart-large-mnli",
    "roberta": "FacebookAI/roberta-large-mnli",
    "deberta": "MoritzLaurer/DeBERTa-v3-base-mnli",
}

models = {}
tokenizers = {}

for name, model_id in model_names.items():
    tokenizers[name] = AutoTokenizer.from_pretrained(model_id)
    models[name] = AutoModelForSequenceClassification.from_pretrained(model_id)

def normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())

def normalize_labels(score_dict: Dict[str, float]) -> Dict[str, float]:
    return {k.lower(): v for k, v in score_dict.items()}

def nli_score(model, tokenizer, premise: str, hypothesis: str) -> Dict[str, float]:
    inputs = tokenizer(premise, hypothesis, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]
    labels = [model.config.id2label[i] for i in range(len(probs))]
    scores = {label: float(prob) for label, prob in zip(labels, probs)}
    return normalize_labels(scores)

def get_multi_model_nli_scores(premise: str, hypothesis: str) -> Dict[str, Dict[str, float]]:
    return {
        model_name: nli_score(models[model_name], tokenizers[model_name], premise, hypothesis)
        for model_name in models
    }

def extract_key_entities(text: str) -> Set[str]:
    doc = nlp(text)
    entities = set()
    for ent in doc.ents:
        if ent.label_ in IMPORTANT_LABELS:
            entities.add(normalize_text(ent.text))
    return entities

def find_entity_coverage_over_premise(query: str, premise: str) -> Dict[str, object]:
    query_entities = extract_key_entities(query)
    premise_entities = extract_key_entities(premise)

    matched_entities = sorted(query_entities.intersection(premise_entities))
    missing_entities = sorted(query_entities.difference(premise_entities))
    extra_entities = sorted(premise_entities.difference(query_entities))

    return {
        "matched_entities": matched_entities,
        "missing_entities": missing_entities,
        "extra_entities": extra_entities,
        "has_extra_entities": len(extra_entities) > 0,
    }

def find_entity_coverage_across_premises(query: str, premises: Dict[str, str]) -> Dict[str, object]:
    query_entities = extract_key_entities(query)
    coverage = {entity: [] for entity in query_entities}
    premise_entities_by_name = {}

    for name, premise in premises.items():
        ents = extract_key_entities(premise)
        premise_entities_by_name[name] = ents
        for entity in query_entities:
            if entity in ents:
                coverage[entity].append(name)

    missing_entities = sorted([entity for entity, covered_by in coverage.items() if not covered_by])

    all_premise_entities = set()
    for ents in premise_entities_by_name.values():
        all_premise_entities.update(ents)

    matched_entities = sorted(query_entities.intersection(all_premise_entities))

    return {
        "query_entities": sorted(query_entities),
        "premise_entities_by_name": {k: sorted(v) for k, v in premise_entities_by_name.items()},
        "coverage": coverage,
        "matched_entities": matched_entities,
        "missing_entities": missing_entities,
        "all_query_entities_present": len(missing_entities) == 0,
    }

def detect_step_misalignment(
    query: str,
    premise: str,
    hypothesis: str,
   
) -> Dict[str, object]:
    nli_results = get_multi_model_nli_scores(premise, hypothesis)

    contradiction_scores = {}
    entailment_scores = {}
    neutral_scores = {}
   

    for model_name, scores in nli_results.items():
        contradiction = scores.get("contradiction", 0.0)
        entailment = scores.get("entailment", 0.0)
        neutral = scores.get("neutral", 0.0)

        contradiction_scores[model_name] = contradiction
        entailment_scores[model_name] = entailment
        neutral_scores[model_name] = neutral

       

    avg_contradiction = sum(contradiction_scores.values()) / len(contradiction_scores)
    avg_entailment = sum(entailment_scores.values()) / len(entailment_scores)
    avg_neutral = sum(neutral_scores.values()) / len(neutral_scores)

    entity_info = find_entity_coverage_over_premise(query, premise)
    print("These are extra entities",entity_info)
    print("This is average contradiction",avg_contradiction)
    step_misalignment = (
        avg_contradiction > 0.1 or len(entity_info["extra_entities"]) > 0 
   
    )

    return {
       
        "step_misalignment": step_misalignment
    }

def detect_trace_task_misalignment(
    query: str,
    premises: Dict[str, str],
    hypothesis: str,
    
):
    step_results = {}

    for name, premise in premises.items():
        step_results[name] = detect_step_misalignment(
            query=query,
            premise=premise,
            hypothesis=hypothesis,
           
        )

    step_flags = [r["step_misalignment"] for r in step_results.values()]
    print("This is step flag",step_flags)
    if all(step_flags):
        check = True
    
    elif False in step_flags:
        last_false_idx = len(step_flags) - 1 - step_flags[::-1].index(False)
        check = all(step_flags[last_false_idx + 1:]) 
        
    else:
        check = False

    trace_misalignment = (
        check
        
    )

    return {
        
        "trace_misalignment": trace_misalignment
    }