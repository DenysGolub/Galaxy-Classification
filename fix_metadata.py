import glob

# Find the file
matches = glob.glob('**/prediction.py', recursive=True)
pred_files = [f for f in matches if 'webapp' in f and 'routes' in f]

if not pred_files:
    print('ERROR: prediction.py not found')
    exit(1)

pred_file = pred_files[0]
print(f'Found: {pred_file}')

# Read the file
with open(pred_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace phot_objid line
content = content.replace(
    '"phot_objid": row["objid"],',
    '"phot_objid": int(row["objid"]) if row.get("objid") is not None else None,'
)

# Replace phot_type line  
content = content.replace(
    '"phot_type": row["type"],',
    '"phot_type": str(row["type"]) if row.get("type") is not None else None,'
)

# Replace flags line
content = content.replace(
    '"flags": row.get("flags")',
    '"flags": int(row.get("flags")) if row.get("flags") is not None else None'
)

# Replace specobjid line
content = content.replace(
    '"specobjid": row["specobjid"],',
    '"specobjid": int(row["specobjid"]) if row.get("specobjid") is not None else None,'
)

# Replace class line
content = content.replace(
    '"class": row.get("class"),',
    '"class": str(row.get("class")) if row.get("class") is not None else None,'
)

# Replace subClass line
content = content.replace(
    '"subClass": row.get("subClass"),',
    '"subClass": str(row.get("subClass")) if row.get("subClass") is not None else None,'
)

# Replace plate line
content = content.replace(
    '"plate": row.get("plate"),',
    '"plate": int(row.get("plate")) if row.get("plate") is not None else None,'
)

# Replace mjd line
content = content.replace(
    '"mjd": row.get("mjd"),',
    '"mjd": int(row.get("mjd")) if row.get("mjd") is not None else None,'
)

# Replace fiberID line
content = content.replace(
    '"fiberID": row.get("fiberID")',
    '"fiberID": int(row.get("fiberID")) if row.get("fiberID") is not None else None'
)

# Write back
with open(pred_file, 'w', encoding='utf-8') as f:
    f.write(content)

print('? Successfully fixed JSON serialization issues')
print('  - Converted all numpy types to native Python types (int, float, str)')
