import os
import json
import argparse
import shutil
from tqdm import tqdm


def get_args():
    parser = argparse.ArgumentParser(description="Classify images based on score threshold.")
    # 1. Path to the JSON results file
    parser.add_argument("-j", "--json_path", type=str, required=True,
                        help="Path to results.json")
    # 2. Root directory where images are currently stored
    parser.add_argument("-i", "--input_dir", type=str, required=True,
                        help="Source images root directory")
    # 3. Output directory for classified results
    parser.add_argument("-o", "--output_root", type=str, default="./classified_results",
                        help="Root directory for output (default: ./classified_results)")
    # 4. Threshold parameter
    parser.add_argument("-t", "--threshold", type=float, default=5.5,
                        help="Score threshold (default: 5.5)")
    return parser.parse_args()


def main():
    args = get_args()

    # Define pass/fail directories
    pass_dir = os.path.join(args.output_root, "pass")
    fail_dir = os.path.join(args.output_root, "fail")

    # Create directories if they don't exist
    os.makedirs(pass_dir, exist_ok=True)
    os.makedirs(fail_dir, exist_ok=True)

    # Load JSON data
    if not os.path.exists(args.json_path):
        print(f"Error: JSON file not found at {args.json_path}")
        return

    try:
        with open(args.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    print(f"Threshold set to: {args.threshold}")
    print(f"Processing {len(data)} entries...")

    stats = {"pass": 0, "fail": 0, "missing": 0}

    # Iterate through data and copy files
    for item in tqdm(data, desc="Copying images"):
        rel_path = item.get('file_path')
        score = item.get('score')

        if not rel_path or score is None:
            continue

        src_path = os.path.join(args.input_dir, rel_path)

        # Check if source file exists
        if not os.path.exists(src_path):
            stats["missing"] += 1
            continue

        # Determine destination folder
        if score >= args.threshold:
            dest_folder = pass_dir
            stats["pass"] += 1
        else:
            dest_folder = fail_dir
            stats["fail"] += 1

        # Handle nested directory structures in file_path
        # e.g., if file_path is 'subdir/img.jpg', it will be saved as 'pass/img.jpg'
        # To preserve structure, use: os.path.join(dest_folder, rel_path)
        dest_path = os.path.join(dest_folder, os.path.basename(rel_path))

        try:
            shutil.copy2(src_path, dest_path)  # copy2 preserves metadata
        except Exception as e:
            print(f"\nError copying {rel_path}: {e}")

    # Summary report
    print("\n" + "=" * 30)
    print("Classification Complete")
    print("=" * 30)
    print(f"Passed images:  {stats['pass']} -> saved to {pass_dir}")
    print(f"Failed images:  {stats['fail']} -> saved to {fail_dir}")
    print(f"Missing images: {stats['missing']}")
    print("=" * 30)


if __name__ == "__main__":
    main()