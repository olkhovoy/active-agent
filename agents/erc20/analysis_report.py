import json
import csv
from typing import List, Dict
from collections import Counter

def load_evaluations(filepath: str) -> List[Dict]:
    """Load JSONL evaluation results"""
    results = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results

def generate_summary_stats(evaluations: List[Dict]) -> Dict:
    """Generate summary statistics"""
    total = len(evaluations)
    labels = Counter(e['label'] for e in evaluations)
    
    # Calculate average reliability and risk by label
    label_stats = {}
    for label in ['investable', 'neutral', 'avoid']:
        label_evals = [e for e in evaluations if e['label'] == label]
        if label_evals:
            avg_reliability = sum(e['reliability'] for e in label_evals) / len(label_evals)
            avg_risk = sum(e['risk'] for e in label_evals) / len(label_evals)
            label_stats[label] = {
                'count': len(label_evals),
                'avg_reliability': round(avg_reliability, 3),
                'avg_risk': round(avg_risk, 3)
            }
    
    # Market cap distribution
    market_caps = [e['market_cap_usd'] for e in evaluations]
    market_caps.sort(reverse=True)
    
    return {
        'total_tokens': total,
        'label_distribution': dict(labels),
        'label_statistics': label_stats,
        'top_market_caps': market_caps[:5],
        'total_market_cap': sum(market_caps)
    }

def generate_recommendations(evaluations: List[Dict]) -> Dict:
    """Generate investment recommendations"""
    # Top reliable tokens
    reliable_tokens = sorted(
        [e for e in evaluations if e['label'] == 'investable'],
        key=lambda x: (x['reliability'], -x['risk']),
        reverse=True
    )[:5]
    
    # High risk tokens to avoid
    avoid_tokens = sorted(
        [e for e in evaluations if e['label'] == 'avoid'],
        key=lambda x: x['risk'],
        reverse=True
    )[:5]
    
    # Neutral tokens with potential
    neutral_tokens = sorted(
        [e for e in evaluations if e['label'] == 'neutral'],
        key=lambda x: x['reliability'],
        reverse=True
    )[:5]
    
    return {
        'top_reliable': reliable_tokens,
        'high_risk_avoid': avoid_tokens,
        'neutral_potential': neutral_tokens
    }

def save_csv_report(evaluations: List[Dict], output_path: str):
    """Save detailed report as CSV"""
    fieldnames = [
        'name', 'symbol', 'contract', 'market_cap_usd', 'volume_24h_usd',
        'label', 'reliability', 'risk', 'rationale'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for eval_data in evaluations:
            row = {field: eval_data.get(field, '') for field in fieldnames}
            writer.writerow(row)

def main():
    base_dir = os.path.dirname(__file__)
    eval_file = os.path.join(base_dir, 'erc20_eval.jsonl')
    csv_output = os.path.join(base_dir, 'erc20_report.csv')
    
    if not os.path.exists(eval_file):
        print("Evaluation file not found. Run evaluator.py first.")
        return
    
    evaluations = load_evaluations(eval_file)
    if not evaluations:
        print("No evaluation data found.")
        return
    
    # Generate reports
    stats = generate_summary_stats(evaluations)
    recommendations = generate_recommendations(evaluations)
    
    # Print summary
    print("=== ERC-20 Token Analysis Report ===\n")
    print(f"Total tokens analyzed: {stats['total_tokens']}")
    print(f"Label distribution: {stats['label_distribution']}")
    print(f"Total market cap: ${stats['total_market_cap']:,.0f}")
    
    print("\n=== Label Statistics ===")
    for label, data in stats['label_statistics'].items():
        print(f"{label.capitalize()}: {data['count']} tokens, "
              f"avg reliability: {data['avg_reliability']}, "
              f"avg risk: {data['avg_risk']}")
    
    print("\n=== Top Reliable Tokens ===")
    for i, token in enumerate(recommendations['top_reliable'], 1):
        print(f"{i}. {token['symbol']} ({token['name']}) - "
              f"Reliability: {token['reliability']}, Risk: {token['risk']}")
    
    print("\n=== High Risk Tokens to Avoid ===")
    for i, token in enumerate(recommendations['high_risk_avoid'], 1):
        print(f"{i}. {token['symbol']} ({token['name']}) - "
              f"Reliability: {token['reliability']}, Risk: {token['risk']}")
    
    # Save CSV report
    save_csv_report(evaluations, csv_output)
    print(f"\nDetailed CSV report saved to: {csv_output}")

if __name__ == '__main__':
    import os
    main()
