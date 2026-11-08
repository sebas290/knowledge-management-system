"""Component 1 - Classify a document by type, or evaluate the classifier.

Examples:
  python scripts/classify.py --text "The user reports that the monitor flickers..."
  python scripts/classify.py --file new_document.txt
  python scripts/classify.py --evaluate
"""
import argparse
import sys
from pathlib import Path

from _common import load_system, table


def main():
    parser = argparse.ArgumentParser(description="Automated document classification")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="document text to classify")
    group.add_argument("--file", help="path to a .txt file to classify")
    group.add_argument("--evaluate", action="store_true", help="5-fold cross-validation report")
    args = parser.parse_args()

    system = load_system()
    if args.evaluate:
        from kms.evaluation import evaluate_classification
        result = evaluate_classification([d for d in system.documents if d.source == "corpus"])
        print(result["setup"])
        rows = [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()} for r in result["per_class"]]
        print(table(rows))
        print(f"\nMacro precision {result['macro']['precision']:.3f} | macro recall {result['macro']['recall']:.3f}"
              f" | macro F1 {result['macro']['f1']:.3f} | accuracy {result['accuracy']:.3f}")
        print("\nConfusion matrix (rows = true, columns = predicted):", result["classes"])
        for name, row in zip(result["classes"], result["confusion_matrix"]):
            print(f"  {name:18s} {row}")
        return

    if args.file:
        path = Path(args.file)
        if not path.is_file():
            sys.exit(f"File not found: {path}")
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        text = args.text
    try:
        prediction = system.classifier.predict(text)
    except ValueError as error:
        sys.exit(f"Error: {error}")
    print(f"Predicted category: {prediction.category} (confidence {prediction.confidence:.2f})")
    print("Probabilities:", ", ".join(f"{c} {p:.2f}" for c, p in
                                      sorted(prediction.probabilities.items(), key=lambda x: -x[1])))
    print("Evidence terms:", ", ".join(prediction.evidence_terms))
    print("Concepts detected:", ", ".join(system.ontology.detect(text)) or "none")


if __name__ == "__main__":
    main()
