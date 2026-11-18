#pragma once

#include <cstddef>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace tracker {

/// Запись задачи; через tasks() доступна только для чтения.
struct Task {
    /// Исходный текст без обрезания.
    std::string text;
    /// Признак выполнения.
    bool done = false;
};

/// Возможные результаты операций модели.
enum class Result {
    /// Операция выполнена.
    Ok,
    /// Поле пусто или состоит только из ASCII-пробельных символов.
    EmptyText,
    /// Нет допустимого выделения для отметки задачи.
    NoSelectionForComplete,
    /// Выбранная задача уже выполнена.
    AlreadyCompleted,
    /// Нет допустимого выделения для удаления задачи.
    NoSelectionForDelete
};

/// Для Ok возвращает пустую строку, иначе точное сообщение на русском языке.
std::string_view message(Result result) noexcept;

/// Состояние списка и поля ввода; представление и операционная система не используются.
class TaskTracker {
public:
    /// Заменить содержимое поля ввода, не изменяя список.
    void set_input(std::string text);
    /// Получить поле ввода только для чтения; обновлять ссылку после изменения модели.
    const std::string& input() const noexcept;

    /// Добавить непустое поле в конец и очистить его; иначе вернуть EmptyText без изменений.
    Result add_from_input();
    /// Отметить выбранную по индексу задачу выполненной или вернуть соответствующую ошибку.
    Result complete(std::optional<std::size_t> index);
    /// Удалить выбранную по индексу задачу или вернуть соответствующую ошибку.
    Result remove(std::optional<std::size_t> index);

    /// Получить список только для чтения; обновлять ссылку после изменения модели.
    const std::vector<Task>& tasks() const noexcept;
    /// Получить новые строки с префиксами [ ] или [✓] в порядке списка.
    std::vector<std::string> display_lines() const;

private:
    bool valid_index(std::optional<std::size_t> index) const noexcept;

    std::string input_;
    std::vector<Task> tasks_;
};

}  // namespace tracker
