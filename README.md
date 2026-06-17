# Самараэнерго для Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/thebestbaduser/hass-samaraenergo?label=release)](https://github.com/thebestbaduser/hass-samaraenergo/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Неофициальная интеграция [личного кабинета ПАО «Самараэнерго»](https://lk.samaraenergo.ru/) для [Home Assistant](https://www.home-assistant.io/).

> **Важно.** Проект разработан сообществом и **не связан** с ПАО «Самараэнерго».  
> Используются только публичные API личного кабинета. Интеграция работает в режиме **только чтения** — оплата и изменение данных в ЛК недоступны.

## Возможности

- сумма к оплате и срок оплаты;
- последний платёж и дата платежа;
- показания счётчика (АСКУЭ);
- среднемесячное потребление и затраты;
- история потребления по месяцам (для графиков в Lovelace);
- тип тарифа и ставки день/ночь (раздел «Настройки» в ЛК).

## Требования

- Home Assistant **2024.1** или новее;
- [HACS](https://hacs.xyz/) (рекомендуется) или ручная установка;
- учётная запись на [lk.samaraenergo.ru](https://lk.samaraenergo.ru/).

## Установка через HACS

1. HACS → **Интеграции** → ⋮ → **Пользовательские репозитории**.
2. Добавьте репозиторий:

   ```
   https://github.com/thebestbaduser/hass-samaraenergo
   ```

   Тип: **Integration**.

3. Найдите **Самараэнерго** → **Установить**.
4. Перезапустите Home Assistant.

## Установка вручную

Скопируйте каталог `custom_components/samaraenergo` в `/config/custom_components/` и перезапустите Home Assistant.

## Настройка

**Настройки → Устройства и службы → Добавить интеграцию → Самараэнерго**

| Поле | Описание |
|------|----------|
| Номер лицевого счёта | Ровно **12 цифр**, без пробелов |
| Пароль | Пароль от [личного кабинета](https://lk.samaraenergo.ru/) |

После добавления в карточке устройства можно изменить **интервал обновления** (от 15 минут до суток, по умолчанию — 1 час).

## Сенсоры

| Сенсор | Описание |
|--------|----------|
| `amount_due` | Сумма к оплате, ₽ |
| `due_date` | Оплатить до |
| `last_payment` | Последний платёж, ₽ |
| `last_payment_date` | Дата последнего платежа |
| `last_reading` | Показания счётчика, кВт·ч |
| `last_reading_date` | Дата показаний |
| `avg_monthly_consumption` | Среднемесячное потребление, кВт·ч |
| `avg_monthly_cost` | Среднемесячные затраты, ₽ |
| `consumption_history` | История потребления (в attributes) |
| `tariff_type` | Тип тарифа |
| `tariff_day` | Тариф день / пик, ₽/кВт·ч (`Preisbtr1`) |
| `tariff_semi_peak` | Тариф полупик, ₽/кВт·ч (`Preisbtr2`, только 3 зоны) |
| `tariff_night` | Тариф ночь, ₽/кВт·ч (`Preisbtr2` или `Preisbtr3`) |

## График в Lovelace

У сенсора `sensor.*_consumption_history` в attributes доступны:

- `history_months` — месяцы;
- `history_kwh` — потребление, кВт·ч;
- `history_costs` — затраты, ₽.

Подходит для [apexcharts-card](https://github.com/RomRider/apexcharts-card) и [mini-graph-card](https://github.com/kalkih/mini-graph-card).

## Отладка

При проблемах с входом добавьте в `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.samaraenergo: debug
```

Перезапустите Home Assistant и проверьте **Настройки → Система → Логи** (фильтр `samaraenergo`).

## Ссылки

- Личный кабинет: [lk.samaraenergo.ru](https://lk.samaraenergo.ru/)
- Репозиторий: [github.com/thebestbaduser/hass-samaraenergo](https://github.com/thebestbaduser/hass-samaraenergo)

## Лицензия

[MIT](LICENSE) © [thebestbaduser](https://github.com/thebestbaduser)
