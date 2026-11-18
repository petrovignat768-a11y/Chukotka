#include "tracker/task_tracker.h"

#include <utility>

namespace tracker {
namespace {

bool is_ascii_whitespace(char c) noexcept {
    switch (c) {
        case ' ': case '\t': case '\n': case '\r': case '\v': case '\f':
            return true;
        default:
            return false;
    }
}

}  // namespace

std::string_view message(Result result) noexcept {
    switch (result) {
        case Result::Ok: return "";
        case Result::EmptyText: return "Текст задачи не может быть пустым!";
        case Result::NoSelectionForComplete: return "Выберите задачу из списка!";
        case Result::AlreadyCompleted: return "Эта задача уже выполнена";
        case Result::NoSelectionForDelete: return "Выберите задачу для удаления!";
    }
    return "";  // Defensive fallback; not part of the public Result contract.
}

void TaskTracker::set_input(std::string text) {
    input_ = std::move(text);
}

const std::string& TaskTracker::input() const noexcept {
    return input_;
}

Result TaskTracker::add_from_input() {
    bool has_content = false;
    for (char c : input_) {
        if (!is_ascii_whitespace(c)) {
            has_content = true;
            break;
        }
    }
    if (!has_content) {
        return Result::EmptyText;
    }
    tasks_.push_back(Task{input_, false});
    input_.clear();
    return Result::Ok;
}

bool TaskTracker::valid_index(std::optional<std::size_t> index) const noexcept {
    return index.has_value() && *index < tasks_.size();
}

Result TaskTracker::complete(std::optional<std::size_t> index) {
    if (!valid_index(index)) {
        return Result::NoSelectionForComplete;
    }
    if (tasks_[*index].done) {
        return Result::AlreadyCompleted;
    }
    tasks_[*index].done = true;
    return Result::Ok;
}

Result TaskTracker::remove(std::optional<std::size_t> index) {
    if (!valid_index(index)) {
        return Result::NoSelectionForDelete;
    }
    tasks_.erase(tasks_.begin() + static_cast<std::vector<Task>::difference_type>(*index));
    return Result::Ok;
}

const std::vector<Task>& TaskTracker::tasks() const noexcept {
    return tasks_;
}

std::vector<std::string> TaskTracker::display_lines() const {
    std::vector<std::string> result;
    result.reserve(tasks_.size());
    for (const auto& task : tasks_) {
        result.push_back(std::string(task.done ? "[✓] " : "[ ] ") + task.text);
    }
    return result;
}

}  // namespace tracker
