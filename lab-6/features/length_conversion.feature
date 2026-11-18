Feature: Преобразование длины между системами мер
  Чтобы сравнивать значения длины, пользователь переводит величину
  из единиц СИ, США и выбранных старорусских единиц.

  Scenario Outline: Корректное преобразование длины
    Given исходное значение "<value>"
    And единицы измерения "<source>" и "<target>"
    When выполняется конвертация
    Then результат равен "<expected>" с точностью "<tolerance>"

    Examples: Между системами и внутри них
      | value | source  | target  | expected       | tolerance      |
      | 1     | m       | cm      | 100            | 0              |
      | 250   | cm      | m       | 2.5            | 0              |
      | 5.5   | km      | m       | 5500           | 0              |
      | 1     | cm      | cm      | 1              | 0              |
      | 1     | in      | mm      | 25.4           | 0              |
      | 12    | in      | ft      | 1              | 0              |
      | 1     | ft      | m       | 0.3048         | 0              |
      | 1     | mi      | km      | 1.609344       | 0              |
      | 2.5   | yd      | in      | 90             | 0              |
      | 1     | mi      | ft      | 5280           | 0              |
      | 1     | m       | ft      | 3.280839895013 | 0.000000000001 |
      | 16    | vershok | arshin  | 1              | 0              |
      | 3     | arshin  | sazhen  | 1              | 0              |
      | 1     | versta  | sazhen  | 500            | 0              |
      | 1     | versta  | km      | 1.0668         | 0              |
      | 1     | arshin  | in      | 28             | 0              |
      | 1     | sazhen  | ft      | 7              | 0              |
      | 0.1   | arshin  | cm      | 7.112          | 0              |
      | 50    | vershok | cm      | 222.25         | 0              |
      | 1     | M       | cm      | 100            | 0              |

    Examples: Граничные допустимые значения
      | value         | source | target | expected    | tolerance |
      | 0             | m      | ft     | 0           | 0         |
      | -0            | m      | ft     | 0           | 0         |
      | 0.000000000001| m      | mm     | 0.000000001 | 0         |
      | 1000000000000 | mm     | km     | 1000000     | 0         |
      | 1e-12         | m      | mm     | 0.000000001 | 0         |

  Scenario Outline: Обратное преобразование восстанавливает значение
    Given исходное значение "<value>"
    And единицы измерения "<source>" и "<target>"
    When величина переводится в целевую единицу и обратно
    Then результат равен "<value>" с точностью "0.000000000000000000000001"

    Examples: Обратные переводы между системами
      | value | source  | target |
      | 3.5   | m       | in     |
      | 2.2   | arshin  | km     |
      | 5280  | ft      | mi     |
      | 1     | versta  | yd     |
      | 1     | in      | mm     |

  Scenario Outline: Некорректный ввод отклоняется с объяснением
    Given исходное значение "<value>"
    And единицы измерения "<source>" и "<target>"
    When выполняется конвертация
    Then ошибка имеет код "<error>"

    Examples: Проверка числа, диапазона и единиц
      | value              | source | target    | error         |
      | -1                 | m      | ft        | negative      |
      | -0.000000000001    | m      | ft        | negative      |
      | 0.0000000000009    | m      | ft        | out_of_range  |
      | 1000000000000.1    | m      | ft        | out_of_range  |
      | NaN                | m      | ft        | invalid_number|
      | Infinity           | m      | ft        | invalid_number|
      | abc                | m      | ft        | invalid_number|
      |                    | m      | ft        | invalid_number|
      | 1,5                | m      | ft        | invalid_number|
      | 1                  | league | m         | unknown_unit  |
      | 1                  | m      | league    | unknown_unit  |
      | 1                  |        | m         | unknown_unit  |
      | 1e999999999999999999999999999 | m | ft    | invalid_number|
