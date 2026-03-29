# interactive.py

def ask(question: str, options: list = None, allow_random: bool = False) -> str:
    """
    Ask the user a question and return their answer.
    If options provided, validate against them.
    If allow_random, accept 'r' as a shortcut for 'random'.
    """
    if options:
        opts_display = " / ".join(f"[{o}]" for o in options)
        if allow_random:
            opts_display += " / [r] random"
        print(f"{question} {opts_display}")
    else:
        if allow_random:
            print(f"{question} (or 'r' for random)")
        else:
            print(question)

    while True:
        answer = input("> ").strip()

        if allow_random and answer.lower() == "r":
            return "random"

        if options:
            if answer.lower() in [o.lower() for o in options]:
                return answer.lower()
            print(f"  Please enter one of: {', '.join(options)}"
                  + (" or 'r' for random" if allow_random else ""))
        elif answer:
            return answer
        else:
            print("  Please enter a value.")


def get_dirty_config() -> dict:
    """Ask user to configure dirty data injection."""
    print("\n  Outlier rate: what % of numeric values should be outliers?")
    print("  (default 2 — enter a number between 1 and 20)")
    while True:
        try:
            outlier = int(input("> ").strip() or "2")
            if 1 <= outlier <= 20:
                break
            print("  Enter a number between 1 and 20.")
        except ValueError:
            print("  Enter a whole number.")

    print("\n  Null rate: what % of fields should be nulled out?")
    print("  (default 1 — enter a number between 1 and 10)")
    while True:
        try:
            null = int(input("> ").strip() or "1")
            if 1 <= null <= 10:
                break
            print("  Enter a number between 1 and 10.")
        except ValueError:
            print("  Enter a whole number.")

    print("\n  Duplicate rate: what % of rows should be duplicated?")
    print("  (default 1 — enter a number between 1 and 10)")
    while True:
        try:
            dup = int(input("> ").strip() or "1")
            if 1 <= dup <= 10:
                break
            print("  Enter a number between 1 and 10.")
        except ValueError:
            print("  Enter a whole number.")

    return {
        "enabled":        True,
        "outlier_rate":   outlier / 100,
        "null_rate":      null / 100,
        "duplicate_rate": dup / 100
    }


def run_guided() -> dict:
    """
    Walk the user through a series of questions to build a generation spec.
    Returns a spec dict consumed by the generator.
    """
    print("\n=== Guided Mode ===\n")

    # Industry
    industry = ask("What industry?", allow_random=True)
    if industry == "random":
        industry = "any industry of your choice"

    # Data type
    data_type = ask("What kind of data?", allow_random=True)
    if data_type == "random":
        data_type = "any appropriate data type for the industry"

    # Number of files
    num_files_ans = ask("How many files?")
    try:
        num_files = int(num_files_ans)
    except ValueError:
        print("  Defaulting to 1 file.")
        num_files = 1

    # Time period
    time_period = ask(
        "What time period should the data cover? (eg. 'last 6 months', '2023')",
        allow_random=True
    )
    if time_period == "random":
        time_period = "a realistic time period for the data type"

    # Rows per file
    rows_ans = ask("Approximate rows per file? (max 50)", allow_random=True)
    if rows_ans == "random":
        rows_per_file = None
    else:
        try:
            rows_per_file = min(int(rows_ans), 50)
        except ValueError:
            print("  Defaulting to LLM decision (capped at 50).")
            rows_per_file = None

    # Number of columns
    cols_ans = ask("How many columns? (max 7)", allow_random=True)
    if cols_ans == "random":
        num_columns = None
    else:
        try:
            num_columns = min(int(cols_ans), 7)
        except ValueError:
            print("  Defaulting to LLM decision (capped at 7).")
            num_columns = None

    # Dirty data
    dirty_answer = ask("\nInject dirty data?", options=["yes", "no"])
    dirty_config = get_dirty_config() if dirty_answer == "yes" else {"enabled": False}

    return {
        "random":        False,
        "industry":      industry,
        "data_type":     data_type,
        "num_files":     num_files,
        "time_period":   time_period,
        "rows_per_file": rows_per_file,
        "num_columns":   num_columns,
        "dirty_config":  dirty_config
    }

def run_random() -> dict:
    """Random mode — LLM decides everything."""
    print("\n=== Random Mode ===")
    print("LLM will decide industry, schema, row counts and file structure.\n")

    dirty_answer = ask(
        "Inject dirty data?",
        options=["yes", "no"]
    )
    dirty_config = get_dirty_config() if dirty_answer == "yes" else {"enabled": False}

    return {
        "random":       True,
        "dirty_config": dirty_config
    }