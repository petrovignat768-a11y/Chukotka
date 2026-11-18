package ru.petrov.tasktracker;

import static org.junit.jupiter.api.Assertions.*;
import static ru.petrov.tasktracker.TaskTracker.Outcome.*;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.NullAndEmptySource;
import org.junit.jupiter.params.provider.ValueSource;

/** Тесты публичного поведения модели; каждый сценарий получает новый трекер. */
class TaskTrackerTest {
    private TaskTracker tracker;

    @BeforeEach
    void setUp() {
        tracker = new TaskTracker();
    }

    private static List<String> display(TaskTracker tracker) {
        return tracker.getTasks().stream().map(TaskTracker.Task::toDisplayString).toList();
    }

    private static void result(TaskTracker.Result actual, TaskTracker.Outcome outcome,
                               String message, boolean success, boolean clearInput) {
        assertAll("публичные поля результата",
                () -> assertEquals(outcome, actual.getOutcome()),
                () -> assertEquals(message, actual.getMessage()),
                () -> assertEquals(success, actual.isSuccess()),
                () -> assertEquals(clearInput, actual.shouldClearInput()));
    }

    private void threeTasks() {
        tracker.addTask("А");
        tracker.addTask("Б");
        tracker.addTask("В");
    }

    @Test
    void newTrackerIsEmpty() {
        assertTrue(tracker.getTasks().isEmpty());
    }

    @Test
    void outcomeEnumerationProvidesStableNames() {
        TaskTracker.Outcome[] expected = {ADDED, COMPLETED, DELETED, INVALID_TEXT, NO_SELECTION, ALREADY_COMPLETED};
        assertArrayEquals(expected, TaskTracker.Outcome.values());
        for (TaskTracker.Outcome outcome : expected) {
            assertSame(outcome, TaskTracker.Outcome.valueOf(outcome.name()));
        }
        assertThrows(IllegalArgumentException.class, () -> TaskTracker.Outcome.valueOf("UNKNOWN"));
        assertThrows(NullPointerException.class, () -> TaskTracker.Outcome.valueOf(null));
    }

    @Test
    void addCreatesUncompletedTaskWithExactPrefixAndSuccessResult() {
        TaskTracker.Result added = tracker.addTask("Купить молоко");
        result(added, ADDED, "", true, true);
        assertEquals(1, tracker.getTasks().size());
        TaskTracker.Task task = tracker.getTasks().get(0);
        assertAll("публичное состояние задачи",
                () -> assertEquals("Купить молоко", task.getText()),
                () -> assertFalse(task.isCompleted()),
                () -> assertEquals("[ ] Купить молоко", task.toDisplayString()));
    }

    @Test
    void addAppendsWithoutChangingPreviousTextOrderOrStatus() {
        tracker.addTask("Первая");
        tracker.completeTask(0);
        tracker.addTask("Вторая");
        result(tracker.addTask(" Третья "), ADDED, "", true, true);
        assertEquals(List.of("[✓] Первая", "[ ] Вторая", "[ ]  Третья "), display(tracker));
        assertEquals(" Третья ", tracker.getTasks().get(2).getText());
    }

    @ParameterizedTest(name = "пустой ввод #{index}")
    @NullAndEmptySource
    @ValueSource(strings = {" ", "   ", "\t", "\n\r", " \t ", "\u00A0", "\u2003"})
    void blankInputIsRejectedWithoutChangingExistingTasks(String text) {
        tracker.addTask("Готовая");
        tracker.completeTask(0);
        tracker.addTask("Ожидает");
        List<String> before = display(tracker);
        result(tracker.addTask(text), INVALID_TEXT, "Текст задачи не может быть пустым!", false, false);
        assertEquals(before, display(tracker));
    }

    @ParameterizedTest
    @ValueSource(strings = {"x", "0", "✓", "  задача  ", "\u00A0x\u00A0", "😀", "[✓] текст", "\u200B"})
    void nonblankTextIsPreservedExactly(String text) {
        result(tracker.addTask(text), ADDED, "", true, true);
        assertEquals(text, tracker.getTasks().get(0).getText());
        assertEquals("[ ] " + text, tracker.getTasks().get(0).toDisplayString());
    }

    @Test
    void longTaskIsNotTruncated() {
        String text = "задача😀".repeat(2000);
        tracker.addTask(text);
        assertEquals(text, tracker.getTasks().get(0).getText());
        assertEquals("[ ] " + text, tracker.getTasks().get(0).toDisplayString());
    }

    @ParameterizedTest
    @ValueSource(ints = {0, 1, 2})
    void completeFirstMiddleOrLastChangesOnlySelectedTask(int index) {
        threeTasks();
        TaskTracker.Result completed = tracker.completeTask(index);
        result(completed, COMPLETED, "", true, false);
        List<String> expected = new ArrayList<>(List.of("[ ] А", "[ ] Б", "[ ] В"));
        expected.set(index, "[✓] " + List.of("А", "Б", "В").get(index));
        assertEquals(expected, display(tracker));
        assertEquals(3, tracker.getTasks().size());
        assertTrue(tracker.getTasks().get(index).isCompleted());
        assertEquals(List.of("А", "Б", "В").get(index), tracker.getTasks().get(index).getText());
    }

    @Test
    void completeWithoutSelectionOnEmptyListWarnsAndDoesNotMutate() {
        result(tracker.completeTask(null), NO_SELECTION, "Выберите задачу из списка!", false, false);
        assertTrue(tracker.getTasks().isEmpty());
    }

    @Test
    void completeWithoutSelectionOnNonemptyListWarnsAndDoesNotMutate() {
        threeTasks();
        tracker.completeTask(1);
        List<String> before = display(tracker);
        result(tracker.completeTask(null), NO_SELECTION, "Выберите задачу из списка!", false, false);
        assertEquals(before, display(tracker));
    }

    @Test
    void completingAlreadyCompletedTaskWarnsWithoutChangingAnything() {
        threeTasks();
        tracker.completeTask(1);
        List<String> before = display(tracker);
        result(tracker.completeTask(1), ALREADY_COMPLETED, "Эта задача уже выполнена", false, false);
        assertEquals(before, display(tracker));
        assertEquals(3, tracker.getTasks().size());
    }

    @ParameterizedTest
    @ValueSource(ints = {-2147483648, -1, 3, 4, 2147483647})
    void invalidCompleteIndexThrowsAndKeepsState(int index) {
        threeTasks();
        tracker.completeTask(1);
        List<String> before = display(tracker);
        IndexOutOfBoundsException error = assertThrows(IndexOutOfBoundsException.class,
                () -> tracker.completeTask(index));
        assertEquals("Индекс задачи вне диапазона: " + index, error.getMessage());
        assertEquals(before, display(tracker));
    }

    @Test
    void indexZeroOnEmptyListIsNotTheSameAsNoSelection() {
        IndexOutOfBoundsException complete = assertThrows(IndexOutOfBoundsException.class,
                () -> tracker.completeTask(0));
        IndexOutOfBoundsException delete = assertThrows(IndexOutOfBoundsException.class,
                () -> tracker.deleteTask(0));
        assertEquals("Индекс задачи вне диапазона: 0", complete.getMessage());
        assertEquals("Индекс задачи вне диапазона: 0", delete.getMessage());
        assertTrue(tracker.getTasks().isEmpty());
    }

    @ParameterizedTest
    @ValueSource(ints = {0, 1, 2})
    void deleteFirstMiddleOrLastPreservesRemainingOrderTextAndStatus(int index) {
        threeTasks();
        tracker.completeTask(1);
        List<String> expected = new ArrayList<>(List.of("[ ] А", "[✓] Б", "[ ] В"));
        expected.remove(index);
        result(tracker.deleteTask(index), DELETED, "", true, false);
        assertEquals(2, tracker.getTasks().size());
        assertEquals(expected, display(tracker));
    }

    @Test
    void deleteWithoutSelectionOnEmptyListWarnsAndDoesNotMutate() {
        result(tracker.deleteTask(null), NO_SELECTION, "Выберите задачу для удаления!", false, false);
        assertTrue(tracker.getTasks().isEmpty());
    }

    @Test
    void deleteWithoutSelectionOnNonemptyListWarnsAndDoesNotMutate() {
        threeTasks();
        tracker.completeTask(1);
        List<String> before = display(tracker);
        result(tracker.deleteTask(null), NO_SELECTION, "Выберите задачу для удаления!", false, false);
        assertEquals(before, display(tracker));
    }

    @ParameterizedTest
    @ValueSource(ints = {-2147483648, -1, 3, 4, 2147483647})
    void invalidDeleteIndexThrowsAndKeepsState(int index) {
        threeTasks();
        tracker.completeTask(1);
        List<String> before = display(tracker);
        IndexOutOfBoundsException error = assertThrows(IndexOutOfBoundsException.class,
                () -> tracker.deleteTask(index));
        assertEquals("Индекс задачи вне диапазона: " + index, error.getMessage());
        assertEquals(before, display(tracker));
    }

    @Test
    void duplicateTextsAreIndependentAndDeletionUsesSelectedIndex() {
        tracker.addTask("Повтор");
        tracker.addTask("Повтор");
        tracker.completeTask(1);
        assertEquals(List.of("[ ] Повтор", "[✓] Повтор"), display(tracker));
        tracker.deleteTask(0);
        assertEquals(List.of("[✓] Повтор"), display(tracker));
        assertTrue(tracker.getTasks().get(0).isCompleted());
    }

    @Test
    void snapshotsAndTaskValuesAreImmutableAndDoNotTrackLaterChanges() {
        tracker.addTask("А");
        List<TaskTracker.Task> snapshot = tracker.getTasks();
        TaskTracker.Task oldTask = snapshot.get(0);
        assertAll("список нельзя модифицировать извне",
                () -> assertThrows(UnsupportedOperationException.class, () -> snapshot.add(oldTask)),
                () -> assertThrows(UnsupportedOperationException.class, () -> snapshot.set(0, oldTask)),
                () -> assertThrows(UnsupportedOperationException.class, () -> snapshot.remove(0)),
                () -> assertThrows(UnsupportedOperationException.class, snapshot::clear));
        tracker.completeTask(0);
        tracker.addTask("Б");
        assertEquals(1, snapshot.size());
        assertEquals("А", oldTask.getText());
        assertFalse(oldTask.isCompleted());
        assertEquals("[ ] А", oldTask.toDisplayString());
        assertEquals(List.of("[✓] А", "[ ] Б"), display(tracker));
        tracker.deleteTask(0);
        assertEquals("[ ] А", snapshot.get(0).toDisplayString());
        assertEquals(List.of("[ ] Б"), display(tracker));
    }

    @Test
    void sequentialOperationsUseCurrentIndicesAfterDeletion() {
        threeTasks();
        tracker.completeTask(2);
        tracker.deleteTask(0);
        assertEquals(List.of("[ ] Б", "[✓] В"), display(tracker));
        tracker.completeTask(0);
        tracker.addTask("Г");
        tracker.deleteTask(1);
        assertEquals(List.of("[✓] Б", "[ ] Г"), display(tracker));
    }

    @Test
    void separateTrackersDoNotShareState() {
        TaskTracker other = new TaskTracker();
        tracker.addTask("Только первый");
        other.addTask("Только второй");
        tracker.completeTask(0);
        assertEquals(List.of("[✓] Только первый"), display(tracker));
        assertEquals(List.of("[ ] Только второй"), display(other));
    }
}
