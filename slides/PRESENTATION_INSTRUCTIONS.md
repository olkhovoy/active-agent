# Banking Coherence Hub - Инструкция по презентации

## Файлы презентации

1. **`banking_coherence_hub_presentation.md`** - Основная презентация в формате Marp (английский)
2. **`banking_coherence_hub_presentation_ru.md`** - Презентация в формате Marp (русский)
3. **`banking_coherence_hub_script_ru.md`** - Сценарий на русском языке
4. **`banking_coherence_hub_deck.md`** - Исходная версия слайдов

## Запуск презентации

### Вариант 1: VS Code + Marp Extension
1. Установите расширение "Marp for VS Code"
2. Откройте `banking_coherence_hub_presentation.md` (английский) или `banking_coherence_hub_presentation_ru.md` (русский)
3. Нажмите `Ctrl+Shift+P` → "Marp: Open Preview"
4. Для показа: `Ctrl+Shift+P` → "Marp: Export Slide Deck..."

### Вариант 2: Marp CLI
```bash
# Установка Marp CLI
npm install -g @marp-team/marp-cli

# Запуск презентации (английский)
marp banking_coherence_hub_presentation.md --server

# Запуск презентации (русский)
marp banking_coherence_hub_presentation_ru.md --server

# Экспорт в PDF (английский)
marp banking_coherence_hub_presentation.md --pdf

# Экспорт в PDF (русский)
marp banking_coherence_hub_presentation_ru.md --pdf

# Экспорт в HTML (английский)
marp banking_coherence_hub_presentation.md --html

# Экспорт в HTML (русский)
marp banking_coherence_hub_presentation_ru.md --html
```

### Вариант 3: Онлайн Marp
1. Перейдите на https://marp.app/
2. Загрузите файл `banking_coherence_hub_presentation.md` (английский) или `banking_coherence_hub_presentation_ru.md` (русский)
3. Используйте встроенный просмотрщик

## Навигация по слайдам

- **Слайды 1-2**: Введение и проблема
- **Слайды 3-4**: Теоретическая основа (UMC)
- **Слайды 5-6**: Обзор решения
- **Слайд 7**: AI Oracle Swarm
- **Слайды 7.5-7.6**: Детали расчета CS и SI
- **Слайды 8-9**: Блокчейн и премиум-уровни
- **Слайды 10-11**: Токеномика
- **Слайды 12-13**: Результаты пилота
- **Слайды 14-15**: Расширения и сравнение
- **Слайды 16-18**: Дорожная карта и заключение

## Ключевые моменты для презентации

### Время выступления: 25-30 минут

1. **Слайд 1-2** (3 мин): Проблема и контекст
2. **Слайд 3-4** (4 мин): UMC теория
3. **Слайд 5-6** (3 мин): Обзор решения
4. **Слайд 7** (2 мин): AI Oracle Swarm
5. **Слайды 7.5-7.6** (5 мин): Детали расчета CS и SI
6. **Слайды 8-9** (3 мин): Блокчейн и премиум
7. **Слайды 10-11** (3 мин): Токеномика
8. **Слайды 12-13** (3 мин): Результаты пилота
9. **Слайды 14-15** (3 мин): Расширения и сравнение
10. **Слайды 16-18** (3 мин): Дорожная карта и заключение

## Подготовка к выступлению

### Материалы для раздачи:
- Краткое резюме (1 страница)
- Техническая спецификация
- Контактная информация

### Ожидаемые вопросы:
1. "Как это влияет на существующие KPI?"
2. "Какие регуляторные риски?"
3. "Сколько стоит внедрение?"
4. "Что если AI ошибётся в оценке?"
5. "Как именно рассчитывается Coherence Score?"
6. "Можно ли подделать или обмануть систему?"

### Подготовленные ответы:
- CS дополняет, не заменяет KPI
- ZK-доказательства упрощают compliance
- ROI положительный уже в первый год
- AI-оракулы учатся на ошибках, есть human oversight
- CS = 60%×coherence_reduction + 30%×stimulation_contribution + 10%×temporal_alignment
- ZK-доказательства и консенсус AI-моделей предотвращают подделку

## Технические требования

### Для показа:
- Проектор с разрешением 1920x1080
- Звуковая система (опционально)
- Интернет-соединение для демо

### Для демонстрации:
- Доступ к Jira/Git репозиторию
- Примеры данных (анонимизированные)
- Демо-версия dashboard

## Контакты

**Alexander Olkhovoy**  
Email: [email]  
LinkedIn: [profile]  
Telegram: [username]

**Active Agent Labs**  
Website: [url]  
GitHub: [repository] 