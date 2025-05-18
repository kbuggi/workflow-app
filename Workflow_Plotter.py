from simple_dag import SimpleDAG
from Workflow_Model import WorkflowStream
import logging
import jsonc, json
import sys, os, argparse, tempfile

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plotsa workflow (typically a recipe) as part of the workflow ecosystem"
    )
    # Define arguments
    parser.add_argument(
        "filename", help="recipe/workflow in json/jsonc format (required)"
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="output file (default: a temp file will be created) ",
    )
    args = parser.parse_args()

    try:
        with open(args.filename, "r") as file:
            recipe_dict = jsonc.load(file)
        w = WorkflowStream(args.filename, recipe_dict)
        logger.info(f"Loaded {w.name}; go_stream_name: {w.go_stream_name}")
    except OSError as e:
        logger.error(f"Uable to open Workflow file {args.filename}:\n{e}")
        sys.exit(1)
    except json.decoder.JSONDecodeError as e:
        critical_error(
            f"Uable to interpret Workflow file {args.filename}\nIt should be JSON/JSONC:\n{e}"
        )
        sys.exit(1)

    warnings = w.build()
    if warnings:
        print("Build warnings", warnings)
    print(w.dag)
    print("\n")

    print("critical_path_length", w.dag.critical_path_length())
    print("\n")

    print("critical_path (filtered)", w.dag.critical_path())
    print("\n")

    print("critical_path (unfiltered)", w.dag.str_critical_path_all())
    print("\n")

    output = (
        args.output
        if args.output
        else tempfile.NamedTemporaryFile(suffix=".svg", delete=False).name
    )
    title = w.name

    w.dag.plot(output, title)
