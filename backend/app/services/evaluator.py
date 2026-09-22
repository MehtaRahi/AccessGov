import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer

def calculate_metrics(answer: str, reference: str):
    """
    Calculates BLEU and ROUGE overlap scores between an AI answer and a reference ground truth.
    """
    if not answer or not reference:
        return {"error": "Answer and reference must be non-empty strings."}
    
    # 1. BLEU Score Calculation
    try:
        # Basic whitespace tokenization
        ans_tokens = answer.lower().split()
        ref_tokens = reference.lower().split()
        
        # We use a smoothing function because some answers might be short or lack 4-grams
        smoothie = SmoothingFunction().method4
        
        bleu_1 = sentence_bleu([ref_tokens], ans_tokens, weights=(1, 0, 0, 0), smoothing_function=smoothie)
        bleu_4 = sentence_bleu([ref_tokens], ans_tokens, weights=(0.25, 0.25, 0.25, 0.25), smoothing_function=smoothie)
    except Exception as e:
        print(f"Error calculating BLEU: {e}")
        bleu_1, bleu_4 = 0.0, 0.0

    # 2. ROUGE Score Calculation
    try:
        scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        scores = scorer.score(reference, answer)
        
        rouge_1 = scores['rouge1'].fmeasure
        rouge_2 = scores['rouge2'].fmeasure
        rouge_l = scores['rougeL'].fmeasure
    except Exception as e:
        print(f"Error calculating ROUGE: {e}")
        rouge_1, rouge_2, rouge_l = 0.0, 0.0, 0.0

    return {
        "bleu_1": round(bleu_1, 4),
        "bleu_4": round(bleu_4, 4),
        "rouge_1": round(rouge_1, 4),
        "rouge_2": round(rouge_2, 4),
        "rouge_l": round(rouge_l, 4)
    }
