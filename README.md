# Самараэнерго для Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Интеграция [ПАО «Самараэнерго»](https://lk.samaraenergo.ru/) для Home Assistant.

Только чтение данных из личного кабинета:

- сумма к оплате и срок оплаты
- последний платёж
- показания счётчика (АСКУЭ)
- среднемесячное потребление и затраты
- история потребления по месяцам (для графиков)

## Публикация на GitHub

```powershell
cd C:\Users\gos_ant\Projects\hass-samaraenergo
.\scripts\publish.ps1
```

Если `gh` не установлен, скрипт подскажет создать репозиторий на https://github.com/new и выполнить `git push`.

Опционально: [GitHub CLI](https://cli.github.com/) для автоматического создания репозитория.

## Установка через HACS

1. HACS → Интеграции → три точки → **Пользовательские репозитории**
2. Добавьте репозиторий:

```
https://github.com/thebestbaduser/hass-samaraenergo
```

Тип: **Integration**

3. Найдите **Самараэнерго** и установите
4. Перезапустите Home Assistant

## Установка вручную (Docker)

Скопируйте `custom_components/samaraenergo` в `/config/custom_components/` и перезапустите HA.

```yaml
# docker-compose.yml — пример volume
volumes:
  - ./config:/config
```

## Настройка

**Настройки → Устройства и службы → Добавить интеграцию → Самараэнерго**

- **Номер лицевого счёта** — 12 цифр (например `205000093620`)
- **Пароль** — от личного кабинета

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

## График в Lovelace

У `sensor.*_consumption_history` в attributes:

- `history_months` — месяцы
- `history_kwh` — потребление
- `history_costs` — затраты

Подходит для `apexcharts-card` и `mini-graph-card`.

## Лицензия

MIT
