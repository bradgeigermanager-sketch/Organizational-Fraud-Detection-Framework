python
import re
import pandas as pd


def clean_string(val):
    """Normalize text by stripping spaces and converting to lowercase."""
    if pd.isna(val):
        return ""
    return str(val).strip().lower()


def extract_digits(val):
    """Extract only numeric digits (useful for comparing bank accounts/SSNs)."""
    if pd.isna(val):
        return ""
    return re.sub(r"\D", "", str(val))


def run_employee_vendor_match(hr_file_path, vendor_file_path, output_path):
    print("⏳ Loading data files...")
    df_hr = pd.read_csv(hr_file_path)
    df_vendor = pd.read_csv(vendor_file_path)

    # 1. Clean data fields for strict matching
    print("🧹 Cleaning and standardizing fields...")
    df_hr["clean_address"] = df_hr["address"].apply(clean_string)
    df_vendor["clean_address"] = df_vendor["address"].apply(clean_string)

    df_hr["clean_bank"] = df_hr["bank_account"].apply(extract_digits)
    df_vendor["clean_bank"] = df_vendor["bank_account"].apply(extract_digits)

    df_hr["clean_tax_id"] = df_hr["ssn_or_tax_id"].apply(extract_digits)
    df_vendor["clean_tax_id"] = df_vendor["tax_id"].apply(extract_digits)

    matches = []

    # 2. Check for Address Matches
    print("🔍 Scanning for matching physical addresses...")
    addr_match = df_hr.merge(
        df_vendor, on="clean_address", suffixes=("_emp", "_vendor")
    )
    for _, row in addr_match.iterrows():
        matches.append(
            {
                "Alert Type": "Address Match",
                "Employee Name": f"{row['first_name']} {row['last_name']}",
                "Employee ID": row["employee_id"],
                "Vendor Name": row["vendor_name"],
                "Vendor ID": row["vendor_id"],
                "Matching Data": row["address_emp"],
            }
        )

    # 3. Check for Bank Account Matches
    print("🔍 Scanning for matching bank accounts...")
    bank_match = df_hr.merge(
        df_vendor, on="clean_bank", suffixes=("_emp", "_vendor")
    )
    for _, row in bank_match.iterrows():
        matches.append(
            {
                "Alert Type": "Bank Account Match",
                "Employee Name": f"{row['first_name']} {row['last_name']}",
                "Employee ID": row["employee_id"],
                "Vendor Name": row["vendor_name"],
                "Vendor ID": row["vendor_id"],
                "Matching Data": row["bank_account_emp"],
            }
        )

    # 4. Check for P.O. Box & Mail Drops in Vendor File
    print("🔍 Scanning vendors for hidden P.O. Boxes / Mail Drops...")
    po_box_pattern = r"\b(p\.?\s*o\.?\s*box|box|pmb|post\s*office\s*box)\b"
    df_po_boxes = df_vendor[
        df_vendor["address"].str.contains(po_box_pattern, case=False, na=False)
    ]
    for _, row in df_po_boxes.iterrows():
        matches.append(
            {
                "Alert Type": "Vendor Using P.O. Box",
                "Employee Name": "N/A (Vendor Check)",
                "Employee ID": "N/A",
                "Vendor Name": row["vendor_name"],
                "Vendor ID": row["vendor_id"],
                "Matching Data": row["address"],
            }
        )

    # 5. Compile and Export Results
    df_alerts = pd.DataFrame(matches)
    if not df_alerts.empty:
        df_alerts.to_csv(output_path, index=False)
        print(
            f"🚨 Match complete! {len(df_alerts)} potential risks found. Report exported to: {output_path}"
        )
    else:
        print("✅ Match complete! No overlapping employee-vendor indicators found.")


# Example execution:
# run_employee_vendor_match('hr_master.csv', 'vendor_master.csv', 'employee_vendor_fraud_alerts.csv')
