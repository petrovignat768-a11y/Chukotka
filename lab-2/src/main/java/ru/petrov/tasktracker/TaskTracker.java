package ru.petrov.tasktracker;

import java.util.ArrayList;
import java.util.List;

/**
 * Самостоятельная модель логики командного трекера задач, не связанная с UI.
 * Хранит задачи в памяти, в порядке добавления. Экземпляр не потокобезопасен.
 * Отсутствие выбора в операциях передаётся как {@code null}; недопустимый
 * целочисленный индекс считается ошибкой вызывающей стороны.
 */
public final class TaskTracker {
    private final List<Task> tasks = new ArrayList<>();

    /** Создаёт пустой трекер. */
    public TaskTracker() {
    }

    /** Возможные результаты операций трекера. */
    public enum Outcome {
        /** Задача добавлена. */ ADDED,
        /** Задача отмечена выполненной. */ COMPLETED,
        /** Задача удалена. */ DELETED,
        /** Введён пустой текст. */ INVALID_TEXT,
        /** Не выбрана задача. */ NO_SELECTION,
        /** Выбранная задача уже выполнена. */ ALREADY_COMPLETED
    }

    /** Неизменяемый снимок одной задачи. */
    public static final class Task {
        private final String text;
        private final boolean completed;

        private Task(String text, boolean completed) {
            this.text = text;
            this.completed = completed;
        }

        /**
         * Возвращает текст задачи.
         * @return исходный текст, без обрезания пробелов
         */
        public String getText() {
            return text;
        }

        /**
         * Возвращает состояние выполнения.
         * @return {@code true}, если задача выполнена
         */
        public boolean isCompleted() {
            return completed;
        }

        /**
         * Формирует строку для списка.
         * @return текст с префиксом {@code [ ] } или {@code [✓] }
         */
        public String toDisplayString() {
            return (completed ? "[✓] " : "[ ] ") + text;
        }
    }

    /** Результат операции, пригодный для обработки любым пользовательским интерфейсом. */
    public static final class Result {
        private final Outcome outcome;
        private final String message;
        private final boolean clearInput;

        private Result(Outcome outcome, String message, boolean clearInput) {
            this.outcome = outcome;
            this.message = message;
            this.clearInput = clearInput;
        }

        /**
         * Возвращает код результата.
         * @return код результата операции
         */
        public Outcome getOutcome() {
            return outcome;
        }

        /**
         * Возвращает сообщение.
         * @return текст уведомления; при успехе — пустая строка
         */
        public String getMessage() {
            return message;
        }

        /**
         * Определяет успешность операции.
         * @return была ли операция успешно выполнена
         */
        public boolean isSuccess() {
            return outcome == Outcome.ADDED || outcome == Outcome.COMPLETED || outcome == Outcome.DELETED;
        }

        /**
         * Признак для UI, а не прямое изменение поля ввода.
         * @return {@code true} только после успешного добавления
         */
        public boolean shouldClearInput() {
            return clearInput;
        }
    }

    /**
     * Добавляет невыполненную задачу в конец списка. Существующие задачи не меняются.
     * Текст сохраняется без обрезания пробелов. Пустым считается {@code null},
     * пустая строка либо строка, все кодовые точки которой Java относит к
     * пробельным символам через {@link Character#isWhitespace(int)} или
     * {@link Character#isSpaceChar(int)}. Отказ не изменяет состояние.
     *
     * @param text исходный текст или {@code null}
     * @return результат и указание для UI об очистке поля при успехе
     */
    public Result addTask(String text) {
        if (text == null || text.codePoints().allMatch(
                cp -> Character.isWhitespace(cp) || Character.isSpaceChar(cp))) {
            return new Result(Outcome.INVALID_TEXT, "Текст задачи не может быть пустым!", false);
        }
        tasks.add(new Task(text, false));
        return new Result(Outcome.ADDED, "", true);
    }

    /**
     * Отмечает выбранную задачу выполненной, не меняя количество и порядок.
     * При отсутствии выбора или повторной отметке состояние не меняется.
     *
     * @param index индекс с нуля или {@code null}, если выбора нет
     * @return результат и при необходимости текст предупреждения
     * @throws IndexOutOfBoundsException если индекс не {@code null} и вне диапазона
     */
    public Result completeTask(Integer index) {
        if (index == null) {
            return new Result(Outcome.NO_SELECTION, "Выберите задачу из списка!", false);
        }
        checkIndex(index);
        Task task = tasks.get(index);
        if (task.completed) {
            return new Result(Outcome.ALREADY_COMPLETED, "Эта задача уже выполнена", false);
        }
        tasks.set(index, new Task(task.text, true));
        return new Result(Outcome.COMPLETED, "", false);
    }

    /**
     * Удаляет выбранную задачу, сохраняя текст, статус и относительный порядок
     * остальных. При отсутствии выбора состояние не меняется.
     *
     * @param index индекс с нуля или {@code null}, если выбора нет
     * @return результат и при необходимости текст предупреждения
     * @throws IndexOutOfBoundsException если индекс не {@code null} и вне диапазона
     */
    public Result deleteTask(Integer index) {
        if (index == null) {
            return new Result(Outcome.NO_SELECTION, "Выберите задачу для удаления!", false);
        }
        checkIndex(index);
        tasks.remove(index.intValue());
        return new Result(Outcome.DELETED, "", false);
    }

    /**
     * Возвращает неизменяемый снимок списка неизменяемых задач.
     * Изменения трекера после вызова не изменяют полученный ранее снимок.
     *
     * @return снимок задач в текущем порядке
     */
    public List<Task> getTasks() {
        return List.copyOf(tasks);
    }

    private void checkIndex(int index) {
        if (index < 0 || index >= tasks.size()) {
            throw new IndexOutOfBoundsException("Индекс задачи вне диапазона: " + index);
        }
    }
}
