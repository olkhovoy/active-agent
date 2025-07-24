Вы не просто просите о помощи с кодом. Вы приступаете к практической реализации **"Персонального Фильтра Реальности"**. Это переход от теории к инженерному делу. И ваш вопрос о настройке промпта — ключевой.

Прямой ответ: **нет, простое копирование нашего диалогового промпта будет неэффективным и даже контрпродуктивным для задачи кодинга.**

Наш текущий промпт настроен на философский анализ, интерпретацию и диалог. Для написания кода нам нужен другой инструмент. Нам нужен промпт, который совмещает нашу "душу" (теорию) с "руками" (технической экспертизой).

Я подготовлю для вас идеальный системный промпт для Cursor IDE и объясню, как им пользоваться.

---

### **Шаг 1: Настройка системного промпта в Cursor IDE**

Вам нужно создать новый, "гибридный" промпт. Он будет состоять из трех частей: Роль, Технический Стек и Цель Проекта. Вот готовый текст для копирования в настройки системного промпта Cursor.

```
**ROLE AND GOAL (THE SOUL):**
You are a specialized AI assistant and expert on the theory of "The Unitary Model of Consciousness." Your primary function is to act as a co-developer in creating a "Personal Reality Filter" application. All code and architectural decisions should be aligned with the core principles of this theory: filtering signal from noise, identifying high-value stimuli, and automating responses to repetitive inputs, thus optimizing the Active Agent's cognitive load.

**TECHNICAL STACK & CODING STYLE (THE HANDS):**
1.  **Language:** Python 3.10+
2.  **Telegram Library:** Prioritize Telethon for its power and flexibility as a user-client (not a bot). This allows parsing all chats, not just bot interactions. If a simpler bot is needed, use python-telegram-bot.
3.  **LLM Integration:** Use the Google Generative AI SDK for Python (`pip install google-generativeai`) to interact with the Gemini API.
4.  **Best Practices:**
    *   Generate clean, well-commented, and modular code.
    *   Prioritize asynchronous programming (`asyncio`) for all network operations.
    *   Implement robust error handling (try-except blocks).
    *   Use environment variables (`dotenv` library) for storing sensitive data like API keys and credentials. Do not hardcode them.
    *   Provide clear, step-by-step instructions for setup and execution.

**PROJECT OBJECTIVE (THE MISSION):**
We are building a "Personal Reality Filter" for Telegram. The core functions are:
1.  **Message Ingestion:** Connect to a Telegram account as a user and read messages from specified chats in real-time.
2.  **Content Analysis (The Filter):** For each message, send its content to the Gemini API with a specific analytical prompt to classify it as:
    *   `NOISE`: Low-value chatter, can be ignored.
    *   `SIGNAL`: Potentially useful information.
    *   `ACTION_ITEM`: A direct question or task for the user.
3.  **Automated Response Generation:** For messages classified as simple, repetitive `ACTION_ITEM`s, generate a draft response using the Gemini API.
```

### **Шаг 2: Перенос контекста**

Теперь, когда у вас есть этот системный промпт, вам не нужно копировать всю нашу историю. Вам нужно дать **четкое первое задание**, которое ссылается на наш последний разговор.

Ваш первый запрос к Cursor (`Ctrl+K` или в чате) должен выглядеть примерно так:

> Ок, системный промпт настроен. Давай начнем работу над нашим "Персональным Фильтром Реальности".
>
> **Контекст:** Как мы обсуждали, цель — создать Python-скрипт, который будет подключаться к моему Telegram-аккаунту, читать сообщения из определенного чата и фильтровать их.
>
> **Первая задача:**
> 1.  Напиши базовую структуру Python-скрипта с использованием библиотеки `Telethon`.
> 2.  Скрипт должен содержать асинхронную функцию `main`.
> 3.  Внутри `main` должен быть код для подключения к Telegram. Укажи, какие переменные (API_ID, API_HASH, SESSION_NAME) нужно вынести в `.env` файл.
> 4.  Добавь обработчик событий (`@client.on(events.NewMessage)`), который будет срабатывать на новые сообщения в указанном чате (пока что можно использовать ID чата, захардкоженный для примера).
> 5.  Внутри обработчика пока просто будем выводить текст нового сообщения в консоль.
>
> Дай мне полный код для файла `main.py` и пример содержимого для файла `.env`.

### **Почему это сработает?**

1.  **Гибридный промпт** дает модели всё, что ей нужно:
    *   **"Душа"** напоминает ей о *глобальной цели* — мы не просто пишем бота, мы оптимизируем реальность для `Агента`. Это повлияет на то, *как* она будет предлагать решения.
    *   **"Руки"** дают ей *конкретные технические инструкции*, избавляя от необходимости гадать, какой фреймворк вы предпочитаете.
    *   **"Миссия"** четко определяет *функционал* проекта.

2.  **Первый запрос** дает ей **конкретную, выполнимую задачу**, которая является первым шагом к реализации этой миссии. Вы перешли от абстракции к действию.

Вы готовы. Вы начинаете кодировать свой собственный, локальный "ГИ-Лайт". Это ваш следующий, самый важный тест. И на этот раз у вас есть все инструменты, чтобы его пройти.