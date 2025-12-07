import pandas as pd  # type: ignore[import-untyped]
import wrds  # type: ignore[import-not-found]


def main():
    print("Loading practicelist.csv...")
    df = pd.read_csv("practicelist.csv")

    print("Connecting to WRDS...")
    db = wrds.Connection()  # prompts for username/password

    wrds_records = []

    print("Querying WRDS for matching wrdsfname entries...\n")

    for p in df["path"]:
        query = f"""
            SELECT fname, wrdsfname
            FROM wrdssec.wrds_forms
            WHERE fname = '{p}'
            LIMIT 1;
        """
        try:
            result = db.raw_sql(query)
            if len(result) > 0:
                wrds_records.append(result.iloc[0])
            else:
                wrds_records.append({"fname": p, "wrdsfname": None})
                print(f"NOT FOUND: {p}")
        except Exception as e:
            print(f"Error for {p}: {e}")
            wrds_records.append({"fname": p, "wrdsfname": None})

    out = pd.DataFrame(wrds_records)
    out.to_csv("wrds_mapping.csv", index=False)
    print("\nSaved → wrds_mapping.csv")


if __name__ == "__main__":
    main()
