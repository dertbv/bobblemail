#!/usr/bin/env python3
"""
Fix missing country names in the database
"""
import sqlite3

# Country code to name mapping
country_names = {
    'US': 'United States',
    'GB': 'United Kingdom',
    'RU': 'Russia',
    'ZA': 'South Africa',
    'ID': 'Indonesia',
    'NL': 'Netherlands',
    'DE': 'Germany',
    'IN': 'India',
    'CN': 'China',
    'CA': 'Canada',
    'FR': 'France',
    'BR': 'Brazil',
    'IL': 'Israel',
    'TH': 'Thailand',
    'SK': 'Slovakia',
    'PL': 'Poland',
    'PE': 'Peru',
    'MX': 'Mexico',
    'MD': 'Moldova',
    'CO': 'Colombia',
    'EU': 'European Union',
    'AU': 'Australia',
    'JP': 'Japan',
    'KR': 'South Korea',
    'ES': 'Spain',
    'IT': 'Italy',
    'SE': 'Sweden',
    'NO': 'Norway',
    'FI': 'Finland',
    'DK': 'Denmark',
    'CH': 'Switzerland',
    'AT': 'Austria',
    'BE': 'Belgium',
    'NZ': 'New Zealand',
    'AR': 'Argentina',
    'CL': 'Chile',
    'VE': 'Venezuela',
    'EC': 'Ecuador',
    'UY': 'Uruguay',
    'PY': 'Paraguay',
    'BO': 'Bolivia',
    'CR': 'Costa Rica',
    'PA': 'Panama',
    'GT': 'Guatemala',
    'HN': 'Honduras',
    'NI': 'Nicaragua',
    'SV': 'El Salvador',
    'DO': 'Dominican Republic',
    'CU': 'Cuba',
    'JM': 'Jamaica',
    'TT': 'Trinidad and Tobago',
    'BB': 'Barbados',
    'BS': 'Bahamas',
    'BZ': 'Belize',
    'GY': 'Guyana',
    'SR': 'Suriname',
    'PH': 'Philippines',
    'MY': 'Malaysia',
    'SG': 'Singapore',
    'VN': 'Vietnam',
    'KH': 'Cambodia',
    'LA': 'Laos',
    'MM': 'Myanmar',
    'LK': 'Sri Lanka',
    'BD': 'Bangladesh',
    'NP': 'Nepal',
    'PK': 'Pakistan',
    'AF': 'Afghanistan',
    'IR': 'Iran',
    'IQ': 'Iraq',
    'SA': 'Saudi Arabia',
    'AE': 'United Arab Emirates',
    'QA': 'Qatar',
    'KW': 'Kuwait',
    'OM': 'Oman',
    'YE': 'Yemen',
    'JO': 'Jordan',
    'LB': 'Lebanon',
    'SY': 'Syria',
    'TR': 'Turkey',
    'EG': 'Egypt',
    'LY': 'Libya',
    'TN': 'Tunisia',
    'DZ': 'Algeria',
    'MA': 'Morocco',
    'SD': 'Sudan',
    'ET': 'Ethiopia',
    'KE': 'Kenya',
    'UG': 'Uganda',
    'TZ': 'Tanzania',
    'RW': 'Rwanda',
    'BI': 'Burundi',
    'MW': 'Malawi',
    'ZM': 'Zambia',
    'ZW': 'Zimbabwe',
    'BW': 'Botswana',
    'NA': 'Namibia',
    'MZ': 'Mozambique',
    'AO': 'Angola',
    'CD': 'Democratic Republic of Congo',
    'CG': 'Republic of Congo',
    'CM': 'Cameroon',
    'GA': 'Gabon',
    'GQ': 'Equatorial Guinea',
    'CF': 'Central African Republic',
    'TD': 'Chad',
    'NE': 'Niger',
    'NG': 'Nigeria',
    'BJ': 'Benin',
    'TG': 'Togo',
    'GH': 'Ghana',
    'CI': 'Ivory Coast',
    'BF': 'Burkina Faso',
    'ML': 'Mali',
    'SN': 'Senegal',
    'GN': 'Guinea',
    'SL': 'Sierra Leone',
    'LR': 'Liberia',
    'MR': 'Mauritania',
    'GM': 'Gambia',
    'CV': 'Cape Verde',
    'ST': 'Sao Tome and Principe',
    'GW': 'Guinea-Bissau'
}

# Connect to database
db_path = "/Users/Badman/Desktop/email/REPOS/Atlas_Email/data/mail_filter.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Update country names based on country codes
    updated_total = 0
    for code, name in country_names.items():
        cursor.execute("""
            UPDATE processed_emails_bulletproof
            SET sender_country_name = ?
            WHERE sender_country_code = ? AND sender_country_name IS NULL
        """, (name, code))
        updated_total += cursor.rowcount
        if cursor.rowcount > 0:
            print(f"Updated {cursor.rowcount} records for {code} -> {name}")
    
    conn.commit()
    print(f"\nTotal records updated: {updated_total}")
    
    # Verify the update
    cursor.execute("""
        SELECT sender_country_code, sender_country_name, COUNT(*) as count
        FROM processed_emails_bulletproof 
        WHERE sender_country_code IS NOT NULL
        GROUP BY sender_country_code, sender_country_name
        ORDER BY count DESC
        LIMIT 10
    """)
    
    print("\nTop 10 countries after update:")
    for row in cursor.fetchall():
        print(f"{row[0]} - {row[1]}: {row[2]} emails")

finally:
    conn.close()