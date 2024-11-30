# planter
Есть мысль сделать этот уже инструмент как

----> ***надстройка к порталу Работа в России (с данных ИНИД)*** <----

чтобы появился какой-то юзкейс именно этого гитхаба (то есть оформить сие творение в библиотеку) однако это все равно будет именно как рабочий инструмента скорее чем либа

---
## Пример работы в картинках
- точка на карте, где будет завод:  
```
point: Point(40.627537, 47.589869)
h3_grid_resolution: 6
search_radius_hours: 1.5
```  

![Example Image](/screenshots/0.%20initial_area_layout_map.png)
![Example Image](/screenshots/0.%20closest_cities.png)
![Example Image](/screenshots/1.%20closest%20cities.png)


- индустрия:
- специальности специалистов и их кол-во:  
```
industr_code: oil_and_gas_ext  
specialties: {"Машинист": 200, "Оператор, аппаратчик": 300}
```  
![Example Image](/screenshots/2.%20closest_cities_params.png)

- город, параметры которого решил оптимизировать:
```
region_city: "Ростовская область, Шахты"
``` 
![Example Image](/screenshots/3.%20optimized_city_params.png)
![Example Image](/screenshots/4.%20city_change_map.png)
![Example Image](/screenshots/5.%20closest_flows_change.png)
![Example Image](/screenshots/6.%20all_flows_in_region.png)