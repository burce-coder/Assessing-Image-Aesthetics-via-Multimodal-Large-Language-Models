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
    # Threshold and classification arguments
    parser.add_argument("-t", "--threshold", type=float, default=5.5,
                        help="Score threshold for qualification (default: 5.5)")
    parser.add_argument("--passed_dir", type=str, default="passed",
                        help="Directory name for qualified images")
    parser.add_argument("--failed_dir", type=str, default="failed",
                        help="Directory name for unqualified images")

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

    # Determine absolute paths for passed/failed directories
    passed_root = os.path.join(parent_dir, args.passed_dir)
    failed_root = os.path.join(parent_dir, args.failed_dir)

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
            answer, score_list = assessment(input_img, precision=args.precision)
            score = score_list[0]
            comment = answer[0]

            # Threshold logic and target path determination
            if score >= args.threshold:
                target_base = passed_root
                status = "passed"
            else:
                target_base = failed_root
                status = "failed"

            # Build destination path while maintaining folder structure
            dest_path = os.path.join(target_base, rel_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # Copy the file (preserving metadata)
            shutil.copy2(full_path, dest_path)

            results.append({
                "file_path": rel_path,
                "new_path": os.path.normpath(dest_path),
                "status": status,
                "score": score,
                "comment": comment
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

    print(f"\n✅ Processing complete!")
    print(f"📊 Results saved to: {final_output_path}")
    print(f"📁 Qualified images copied to: {passed_root}")
    print(f"📁 Unqualified images copied to: {failed_root}")


if __name__ == "__main__":
    main()