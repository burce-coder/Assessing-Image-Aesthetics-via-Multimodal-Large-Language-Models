import os
import json
import argparse
from PIL import Image
from tqdm import tqdm
from mplug_owl2.assessor import Assessment


def main():
    # 1. Argument Parser Configuration
    parser = argparse.ArgumentParser(description="ROC4MLLM Batch Image Quality Assessment Tool")
    parser.add_argument("-i", "--input_dir", type=str, required=True,
                        help="Input directory containing images (recursive)")
    parser.add_argument("-o", "--output_json", type=str, default="results.json",
                        help="Output JSON file path")
    parser.add_argument("-m", "--model_path", type=str, default="./models",
                        help="Path to pretrained model weights")
    parser.add_argument("-p", "--precision", type=int, default=4,
                        help="Number of decimal places for the score")

    args = parser.parse_args()

    # --- New Logic: Calculate Output Path ---
    # Convert to absolute path to avoid confusion
    abs_input_dir = os.path.abspath(args.input_dir)
    parent_dir = os.path.dirname(abs_input_dir)

    if args.output_json is None:
        # Default filename if not provided
        output_filename = "results.json"
        final_output_path = os.path.join(parent_dir, output_filename)
    else:
        # If user provided a filename/path, ensure it's put in the parent directory
        # unless they provided an absolute path
        if os.path.isabs(args.output_json):
            final_output_path = args.output_json
        else:
            final_output_path = os.path.join(parent_dir, args.output_json)
    # ----------------------------------------

    # 2. Initialize Model
    print(f"Loading model from: {args.model_path} ...")
    try:
        assessment = Assessment(pretrained=args.model_path)
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    # 3. Recursively collect image files
    valid_extensions = ('.jpg', '.jpeg', '.png', '.JPG', '.PNG')
    image_tasks = []

    for root, _, files in os.walk(args.input_dir):
        for file in files:
            if file.endswith(valid_extensions):
                full_path = os.path.join(root, file)
                # Calculate relative path for better JSON organization
                rel_path = os.path.relpath(full_path, args.input_dir)
                image_tasks.append((full_path, rel_path))

    if not image_tasks:
        print(f"No valid image files found in: {args.input_dir}")
        return

    print(f"Found {len(image_tasks)} images. Starting assessment...")

    # 4. Processing Loop
    results = []

    # Using tqdm for progress tracking
    for full_path, rel_path in tqdm(image_tasks, desc="Assessing"):
        try:
            # Process image (as per your server logic)
            img = Image.open(full_path).convert('RGB')
            input_img = [img]

            # Based on your server.py: returns (comment_list, score_list)
            answer, score = assessment(input_img, precision=args.precision)

            results.append({
                "file_path": rel_path,
                "score": score[0],
                "comment": answer[0]
            })

        except Exception as e:
            print(f"\nError processing {rel_path}: {e}")
            results.append({
                "file_path": rel_path,
                "score": None,
                "comment": f"Error: {str(e)}"
            })

    # 5. Save results to JSON
    with open(final_output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Assessment finished! Results saved to: {args.output_json}")


if __name__ == "__main__":
    main()