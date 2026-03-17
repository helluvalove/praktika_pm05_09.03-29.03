SELECT 
    o.id AS order_id,
    c.name AS customer,
    SUM(ol.count * sl.count * (
        SELECT price 
        FROM prices p 
        WHERE p.material_id = sl.material_id 
          AND p.date <= o.date 
          AND p.product_id IS NULL
        ORDER BY p.date DESC 
        LIMIT 1
    )) AS full_material_cost
FROM orders o
JOIN contragents c ON c.id = o.customer_id
JOIN order_lines ol ON ol.order_id = o.id
JOIN specifications s ON s.product_id = ol.product_id
JOIN specification_lines sl ON sl.specification_id = s.id
GROUP BY o.id, c.name
ORDER BY o.id;