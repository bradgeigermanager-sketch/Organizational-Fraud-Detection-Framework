python
import pandas as pd


def audit_erp_permissions(user_roles_file, output_path):
    print("⏳ Importing ERP user access permissions...")
    # Expected format: CSV with ['user_id', 'username', 'email', 'role']
    df = pd.read_csv(user_roles_file)

    # Group roles per user to handle employees holding multiple profiles
    print("📊 Aggregating roles per unique user...")
    user_profiles = df.groupby(["user_id", "username", "email"])[
        "role"
    ].apply(set)

    # Define Toxic Combinations based on the POL-FIN-042 Policy Matrix
    toxic_combinations = {
        "Requester + Approver": {"Requester", "Approver"},
        "Procurement + AP Invoice Entry": {"Buyer", "Accounts Payable"},
        "Vendor Master Setup + Payment Execution": {"Buyer", "Accounts Payable"},
    }

    conflicts_found = []

    print("🔎 Auditing accounts against Segregation of Duties matrix...")
    for (user_id, username, email), roles in user_profiles.items():
        for rule_name, toxic_set in toxic_combinations.items():
            # Check if the user's roles contain ALL roles within a toxic pair
            if toxic_set.issubset(roles):
                conflicts_found.append(
                    {
                        "User ID": user_id,
                        "Username": username,
                        "Email": email,
                        "Assigned Roles": ", ".join(roles),
                        "SoD Policy Violation": rule_name,
                        "Risk Level": "HIGH - Immediate Revocation Required",
                    }
                )

    # Export Report
    df_violations = pd.DataFrame(conflicts_found)
    if not df_violations.empty:
        df_violations.to_csv(output_path, index=False)
        print(
            f"🚨 SoD Audit Complete! {len(df_violations)} toxic profiles found. Report exported to: {output_path}"
        )
    else:
        print("✅ SoD Audit Complete! All system profiles comply with policy.")


# Example execution:
# audit_erp_permissions('erp_user_roles.csv', 'sod_violation_report.csv')
