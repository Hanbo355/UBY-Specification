from uby_time import iso_to_uby, format_full, format_academic_mnemonic

uby = iso_to_uby("2026-01-01T00:00:00Z")
print(format_full(uby))
print(format_academic_mnemonic(-220))
