import pandas as pd

s = pd.read_csv('../spelling_equivalences.csv')

# Finding words that are in both columns
nonst_w = set(s['nonstandard'])
st_w = set(s['standard'])
both_w = nonst_w.intersection(st_w)
s = s[~s['nonstandard'].isin(both_w)]

# Removing duplicates
s = s.drop_duplicates(subset=['nonstandard', 'standard'])
d = s.duplicated(subset=['nonstandard'], keep=False)
print(s[d]) # This shows that Byz is NOT standardised!

s = s.drop_duplicates(subset=['nonstandard'])
s.to_csv('spelling_equivalences_depurated.csv', index=False)
