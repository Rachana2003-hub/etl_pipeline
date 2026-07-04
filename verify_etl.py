import etl_pipeline
import config


def verify():
    print("--- Starting Local Verification of Extract & Transform ---")

    # 1. Test Extract
    try:
        df_extracted = etl_pipeline.extract(config.CSV_FILE_PATH)
        print(f"\n[Extract Success] Loaded {len(df_extracted)} rows from CSV.")
        print("\nExtracted Data Sample (first 5 rows):")
        print(df_extracted.head())
    except Exception as e:
        print(f"[Extract Failed] {e}")
        return

    # 2. Test Transform
    try:
        df_transformed = etl_pipeline.transform(df_extracted)
        print(f"\n[Transform Success] Transformed data has {len(df_transformed)} rows.")
        print("\nTransformed Data Sample (first 10 rows):")
        cols_to_print = [
            "Transaction_ID",
            "Date",
            "Customer_Name",
            "Product",
            "Price",
            "Quantity",
            "Total",
        ]
        print(df_transformed[cols_to_print].head(10))

        # Verify Transformation Requirements
        print("\nChecking transformation results:")

        # A. Remove duplicates
        has_duplicates = df_transformed.duplicated().any()
        print(
            f"- Duplicate records check: {'FAIL (duplicates exist)' if has_duplicates else 'PASS (no duplicates)'}"
        )

        # B. Handle missing values
        missing_names = df_transformed["Customer_Name"].isnull().sum()
        missing_prices = df_transformed["Price"].isnull().sum()
        missing_quantities = df_transformed["Quantity"].isnull().sum()
        print(f"- Missing customer names: {missing_names} (should be 0)")
        print(f"- Missing prices: {missing_prices} (should be 0)")
        print(f"- Missing quantities: {missing_quantities} (should be 0)")

        # C. Convert customer names to uppercase
        any_name_not_upper = (
            df_transformed["Customer_Name"]
            != df_transformed["Customer_Name"].str.upper()
        ).any()
        print(
            f"- Customer name uppercase check: {'FAIL' if any_name_not_upper else 'PASS (all uppercase)'}"
        )

        # D. Create a new column Total = Price * Quantity
        incorrect_totals = (
            df_transformed["Total"]
            != df_transformed["Price"] * df_transformed["Quantity"]
        ).sum()
        print(
            f"- Total column math verification: {'FAIL' if incorrect_totals > 0 else 'PASS (all matches)'}"
        )

    except Exception as e:
        print(f"[Transform Failed] {e}")
        return


if __name__ == "__main__":
    verify()
