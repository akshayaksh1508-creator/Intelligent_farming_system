with open('static/pages/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_del = None
end_del = None

for i, line in enumerate(lines):
    if '.sim-container { display: grid; grid-template-columns: 1fr 380px' in line and start_del is None:
        start_del = i - 2
    if 'sim-container -->' in line and start_del is not None:
        end_del = i + 1
        break

print(f'Deleting lines {start_del} to {end_del} (total {end_del - start_del} lines)')
if start_del is not None and end_del is not None:
    new_lines = lines[:start_del] + lines[end_del:]
    with open('static/pages/dashboard.html', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print('Done!')
else:
    print('Pattern not found, searching for markers...')
    for i, line in enumerate(lines[830:850], start=830):
        print(f'{i}: {line[:80].rstrip()}')
