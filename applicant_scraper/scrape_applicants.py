# Requires: pip install XlsxWriter

import os
import urllib.request
import urllib.parse
import bs4
import xlsxwriter
import toml


app_url = toml.load('scrape.toml')['url']
base = urllib.parse.splitquery(app_url)[0].rsplit('/', 1)[0]

if not os.path.exists('_data.html'):
    print('Downloading applications...')
    with urllib.request.urlopen(app_url) as response:
        html = response.read()
        with open('_data.html', 'wb') as f:
            f.write(html)
else:
    print('Re-using cached page')


with open('_data.html') as f:
    data = f.read()

bs = bs4.BeautifulSoup(data, 'html.parser')

workbook = xlsxwriter.Workbook('applications.xlsx')
worksheet = workbook.add_worksheet()
bold = workbook.add_format({'bold': True})

head = ('name', 'application', 'interview', 'selected', 'contract', 'comment', 'email')
for col, h in enumerate(head):
    worksheet.write(0, col, h, bold)

row_nr = 1

for row in bs.find_all('tr'):
    columns = row.find_all('td')

    if len(columns) == 0:
        continue

    name, app_text, interview, selected, _, comment, email = [c.text for c in columns]

    app_url = base + '/' + columns[1].find('a')['href']
    contract_url = base + '/' + columns[4].find('a')['href']

    worksheet.write(row_nr, 0, name)
    worksheet.write(row_nr, 1, app_url, None, app_text)
    worksheet.write(row_nr, 2, interview)
    worksheet.write(row_nr, 3, selected)
    worksheet.write(row_nr, 4, contract_url, None, 'Create LC')
    worksheet.write(row_nr, 5, comment)
    worksheet.write(row_nr, 6, email)

    row_nr += 1

workbook.close()
print("Wrote applications to applications.xlsx")
