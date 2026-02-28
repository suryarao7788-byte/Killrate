import json
from team_meta import _resolve_cyrac, _canonical, CYRAC_RANK

cyrac = json.load(open('data/cyrac_tiers.json', encoding='utf-8'))
kt    = json.load(open('data/killteams.json', encoding='utf-8'))
kt_names = [t['killteamName'] for t in kt]

ignore = {'Non-Player Operatives', 'Strike Force Variel', 'Titus Mission Pack'}
for name in sorted(kt_names):
    if name in ignore: continue
    canon = _canonical(name)
    resolved = _resolve_cyrac(name)
    rank = CYRAC_RANK.get(resolved)
    if rank is None:
        print(f'MISSING: {name!r} -> canon={canon!r} -> resolved={resolved!r}')