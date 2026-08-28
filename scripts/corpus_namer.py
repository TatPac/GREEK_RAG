from pathlib import Path
from datetime import datetime
import hashlib
import json
import shutil


# ============================================================
# PROJECT DIRECTORIES
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CORPUS_ROOT = PROJECT_ROOT / "data" / "corpora"
READY_DIR = CORPUS_ROOT / "ready"
ARCHIVE_DIR = CORPUS_ROOT / "archives"
REPLACE_DIR = CORPUS_ROOT / "replace"
RAW_DIR = CORPUS_ROOT / "raw"

CORPUS_METADATA_PATH = READY_DIR / "corpus.json"


# ============================================================
# SETTINGS
# ============================================================

CORPUS_NAME = "SBLGNT"


# ============================================================
# FILE HASHING
# ============================================================

def calculate_file_hash(file_path):
    """
    Calculate a SHA-256 hash of a file.

    The hash lets us detect whether a source file's contents
    have changed, even if its filename has not changed.
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for block in iter(lambda: file.read(65536), b""):
            sha256.update(block)

    return sha256.hexdigest()


def get_corpus_files(directory):
    """
    Return all TXT files in the specified corpus directory.
    """

    return sorted(directory.glob("*.txt"))



def build_file_metadata(files):
    """
    Build metadata describing the current source files.
    """

    return {
        file_path.name: calculate_file_hash(file_path)
        for file_path in files
    }

# ============================================================
# VALIDATE REPLACEMENT CORPUS
# ============================================================

def validate_replacement_corpus():
    """
    Validate the proposed replacement corpus before making
    any changes to the active corpus.
    """

    print()
    print("Validating replacement corpus...")

    # --------------------------------------------------------
    # Check that TXT files exist.
    # --------------------------------------------------------

    replacement_files = get_corpus_files(
        REPLACE_DIR
    )

    if not replacement_files:

        print()
        print(
            "ERROR: No TXT files found in replace/."
        )

        return False

    print(
        f"  Found {len(replacement_files)} TXT file(s)."
    )

    # --------------------------------------------------------
    # Check for unexpected files.
    # --------------------------------------------------------

    unexpected_files = [
        file_path
        for file_path in REPLACE_DIR.iterdir()
        if file_path.is_file()
        and file_path.suffix.lower() != ".txt"
    ]

    if unexpected_files:

        print()
        print(
            "ERROR: Unexpected files found in replace/:"
        )

        for file_path in unexpected_files:

            print(
                f"  {file_path.name}"
            )

        return False

    # --------------------------------------------------------
    # Check that TXT files are readable and non-empty.
    # --------------------------------------------------------

    for file_path in replacement_files:

        if not file_path.is_file():

            print()
            print(
                f"ERROR: Not a regular file: "
                f"{file_path.name}"
            )

            return False

        if file_path.stat().st_size == 0:

            print()
            print(
                f"ERROR: Empty TXT file: "
                f"{file_path.name}"
            )

            return False

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:

                file.read()

        except UnicodeDecodeError:

            print()
            print(
                f"ERROR: File is not valid UTF-8: "
                f"{file_path.name}"
            )

            return False

        except OSError as error:

            print()
            print(
                f"ERROR: Could not read "
                f"{file_path.name}: {error}"
            )

            return False

    print(
        "  All TXT files passed validation."
    )

    print(
        "Replacement corpus is valid."
    )

    return True

# ============================================================
# LOAD PREVIOUS METADATA
# ============================================================

def load_previous_metadata():
    """
    Load the existing corpus.json if one exists.
    """

    if not CORPUS_METADATA_PATH.exists():
        return None

    with open(
        CORPUS_METADATA_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# ============================================================
# DETERMINE WHETHER CORPUS CHANGED
# ============================================================

def corpus_changed(previous_metadata, current_files):
    """
    Compare the proposed replacement corpus with the
    currently active corpus metadata.
    """

    if previous_metadata is None:
        return True

    previous_files = previous_metadata.get(
        "files",
        {}
    )

    current_file_metadata = build_file_metadata(
        current_files
    )

    return previous_files != current_file_metadata

# ============================================================
# DETERMINE NEXT VERSION
# ============================================================

def get_next_version(previous_metadata):
    """
    Increase the previous corpus version by one.
    """

    if previous_metadata is None:
        return 1

    previous_version = previous_metadata.get(
        "version",
        0
    )

    return previous_version + 1


# ============================================================
# ARCHIVE OLD CORPUS
# ============================================================

def archive_current_corpus(previous_metadata):
    """
    Move the current ready corpus into its archive directory.
    """

    if previous_metadata is None:
        return

    previous_version = previous_metadata.get(
        "version",
        0
    )

    archive_dir = (
        ARCHIVE_DIR
        / f"v{previous_version:03d}"
    )

    archive_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print(
        f"Archiving corpus v{previous_version:03d}..."
    )

    # Move TXT files.
    for file_path in get_corpus_files(READY_DIR):

        destination = archive_dir / file_path.name

        shutil.move(
            str(file_path),
            str(destination)
        )

        print(
            f"  Archived: {file_path.name}"
        )

    # Move corpus.json.
    if CORPUS_METADATA_PATH.exists():

        destination = (
            archive_dir
            / CORPUS_METADATA_PATH.name
        )

        shutil.move(
            str(CORPUS_METADATA_PATH),
            str(destination)
        )

        print(
            "  Archived: corpus.json"
        )

    return archive_dir

# ============================================================
# INSTALL REPLACEMENT CORPUS
# ============================================================

def install_replacement_corpus():
    """
    Move the validated replacement corpus into ready/.
    """

    print()
    print("Installing replacement corpus...")

    replacement_files = get_corpus_files(
        REPLACE_DIR
    )

    for file_path in replacement_files:

        destination = READY_DIR / file_path.name

        shutil.move(
            str(file_path),
            str(destination)
        )

        print(
            f"  Installed: {file_path.name}"
        )

# ============================================================
# CREATE NEW METADATA
# ============================================================

def create_metadata(
    version,
    current_files
):
    """
    Create metadata for the new corpus version.
    """

    file_metadata = build_file_metadata(
        current_files
    )

    return {
        "corpus_name": CORPUS_NAME,

        "corpus_id": (
            f"sblgnt_nt_v{version:03d}"
        ),

        "version": version,

        "created": datetime.now().isoformat(
            timespec="seconds"
        ),

        "file_count": len(current_files),

        "files": file_metadata
    }


# ============================================================
# MAIN
# ============================================================

def main():

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    REPLACE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    READY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    ARCHIVE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print("=" * 60)
    print("CORPUS VERSION MANAGER")
    print("=" * 60)

    previous_metadata = load_previous_metadata()

    # The replacement directory contains the proposed
    # next corpus.
    replacement_files = get_corpus_files(
        REPLACE_DIR
    )

    # --------------------------------------------------------
    # First corpus
    # --------------------------------------------------------

    if previous_metadata is None:

        current_files = get_corpus_files(
            READY_DIR
        )

        if not current_files:

            print()
            print(
                "ERROR: No TXT files found in ready/."
            )

            return

        version = 1

        metadata = create_metadata(
            version,
            current_files
        )

        with open(
            CORPUS_METADATA_PATH,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                metadata,
                file,
                indent=4,
                ensure_ascii=False
            )

        print()
        print(
            f"Created corpus v{version:03d}."
        )

        print(
            f"Corpus ID: "
            f"{metadata['corpus_id']}"
        )

        print(
            f"Files registered: "
            f"{len(current_files)}"
        )

        return

    # --------------------------------------------------------
    # Validate replacement corpus
    # --------------------------------------------------------

    if not validate_replacement_corpus():

        print()
        print(
            "Replacement corpus failed validation."
        )

        print(
            "No changes were made to ready/."
        )

        return

    print(
        f"Replacement TXT files: "
        f"{len(replacement_files)}"
    )

    # --------------------------------------------------------
    # Check whether replacement differs
    # --------------------------------------------------------

    if not corpus_changed(
        previous_metadata,
        replacement_files
    ):

        print()
        print(
            "No corpus changes detected."
        )

        print(
            f"Current version: "
            f"v{previous_metadata['version']:03d}"
        )

        print(
            "Nothing was changed."
        )

        return

    # --------------------------------------------------------
    # Corpus changed
    # --------------------------------------------------------

    version = get_next_version(
        previous_metadata
    )

    # Archive current ready corpus.
    archive_current_corpus(
        previous_metadata
    )

    # Move replacement corpus into ready.
    install_replacement_corpus()

    # Get the newly installed files.
    current_files = get_corpus_files(
        READY_DIR
    )

    # Create metadata for the new corpus.
    metadata = create_metadata(
        version,
        current_files
    )

    with open(
        CORPUS_METADATA_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4,
            ensure_ascii=False
        )

    print()
    print(
        "Corpus changed."
    )

    print(
        f"Previous version: "
        f"v{previous_metadata['version']:03d}"
    )

    print(
        f"New version:      "
        f"v{version:03d}"
    )

    print(
        f"New corpus ID:    "
        f"{metadata['corpus_id']}"
    )

    print()
    print(
        "New corpus metadata:"
    )

    print(
        CORPUS_METADATA_PATH
    )

    print("=" * 60)

if __name__ == "__main__":
    main()
