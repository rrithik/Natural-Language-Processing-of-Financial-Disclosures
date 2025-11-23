import wrds

print("Attempting WRDS connection...")

try:
    # If this is your first time, put your username.
    db = wrds.Connection(wrds_username="your_username")     

    print("\nConnected to WRDS successfully!")
    print("Listing first 5 rows of CRSP stock names...\n")

    df = db.raw_sql("""
        SELECT permno, comnam
        FROM crsp.stocknames
        LIMIT 5;
    """)

    print(df)

    db.close()
    print("\nConnection closed normally.")

except Exception as e:
    print("\n❌ WRDS connection failed.")
    print("Error message:")
    print(e)
