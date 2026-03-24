import json
import psycopg2

conn = psycopg2.connect(dbname='mk_polesie', user='postgres', password='...')
cur = conn.cursor()

with open('Заказчики.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    for item in data:
        cur.execute(
            "INSERT INTO contragents (name, inn, phone, adress, supplier, customer) VALUES (%s, %s, %s, %s, %s, %s)",
            (item['name'], item.get('inn'), item.get('phone'), item.get('adress'), item.get('supplier'), item.get('customer'))
        )
conn.commit()
conn.close()