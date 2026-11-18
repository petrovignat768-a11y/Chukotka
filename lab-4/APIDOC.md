# Документация публичного API модели

Автоматически извлечено скриптом `tools/generate_api_doc.py` из `include/tracker/task_tracker.h`. Полные контракты и допущения: [SPECIFICATION.md](SPECIFICATION.md).

| Объявление | Описание |
|---|---|
| `struct Task` | Запись задачи; через tasks() доступна только для чтения. |
| `std::string text` | Исходный текст без обрезания. |
| `bool done = false` | Признак выполнения. |
| `enum class Result` | Возможные результаты операций модели. |
| `Ok` | Операция выполнена. |
| `EmptyText` | Поле пусто или состоит только из ASCII-пробельных символов. |
| `NoSelectionForComplete` | Нет допустимого выделения для отметки задачи. |
| `AlreadyCompleted` | Выбранная задача уже выполнена. |
| `NoSelectionForDelete` | Нет допустимого выделения для удаления задачи. |
| `std::string_view message(Result result) noexcept` | Для Ok возвращает пустую строку, иначе точное сообщение на русском языке. |
| `class TaskTracker` | Состояние списка и поля ввода; представление и операционная система не используются. |
| `void set_input(std::string text)` | Заменить содержимое поля ввода, не изменяя список. |
| `const std::string& input() const noexcept` | Получить поле ввода только для чтения; обновлять ссылку после изменения модели. |
| `Result add_from_input()` | Добавить непустое поле в конец и очистить его; иначе вернуть EmptyText без изменений. |
| `Result complete(std::optional<std::size_t> index)` | Отметить выбранную по индексу задачу выполненной или вернуть соответствующую ошибку. |
| `Result remove(std::optional<std::size_t> index)` | Удалить выбранную по индексу задачу или вернуть соответствующую ошибку. |
| `const std::vector<Task>& tasks() const noexcept` | Получить список только для чтения; обновлять ссылку после изменения модели. |
| `std::vector<std::string> display_lines() const` | Получить новые строки с префиксами [ ] или [✓] в порядке списка. |
