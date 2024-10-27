 		Структура базы данных "мероприятия"

Таблица Events

 

| Имя поля | тип |
| :---- | :---- |
| iD (ключ) | integer |
| title | String |
| status | string |
| description | String |
| start\_at | DateTime |
| location | string |
| end\_at | DateTime |
| visitor\_limit() | integer |
| price | integer |
| created\_at  | TIMESTAMP |
| updated\_at | TIMESTAMP |

 

 

Структура таблицы посетители (Visitors)

 

| Имя поля | Тип |
| :---- | :---- |
| ID | Integer(ключ) |
| first\_name | string |
| Lastn\_ame | string |
| Phone\_number | string |
| E-mail\_adress | string  |
| created\_at  | TIMESTAMP |
| updated\_at | TIMESTAMP |

 

 

Структура таблицы регистрации на мероприятие (reg\_for\_the\_event)


 

| Имя поля | Тип |
| :---- | :---- |
| ID (регистрационный номер участника) | integer  |
| Event\_ID (здесь связь по ключу с таблицей Events) | integer |
| Visitor\_ID (здесь связь по ключу с таблицей Visitors) | Integer |
| status | string |
| Price | integer |
| billed\_amount | Integer |
| refund\_amount | Integer |
| billed\_at | TIMESTAMP |
| refunded\_at  | TIMESTAMP |
| created\_at  | TIMESTAMP |
| updated\_at | TIMESTAMP |

 
