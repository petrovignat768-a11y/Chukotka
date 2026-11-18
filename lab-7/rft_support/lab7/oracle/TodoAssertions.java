package lab7.oracle;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Оракул спецификации. Не управляет приложением и не является скриптом RFT. */
public final class TodoAssertions {
    private static final String TODO = "[ ]";
    private static final String DONE = "[✓]";
    private TodoAssertions() {}

    public static void assertAdded(List<String> before, List<String> actual, String title) {
        Objects.requireNonNull(before, "before");
        Objects.requireNonNull(actual, "actual");
        if (title == null || title.trim().isEmpty()) {
            throw new IllegalArgumentException("Для assertAdded требуется непустой текст");
        }
        List<String> expected = new ArrayList<>(before);
        expected.add(TODO + " " + title);
        assertListEquals(expected, actual, "добавление");
    }

    public static void assertMarked(List<String> before, List<String> actual, int index) {
        Objects.requireNonNull(before, "before");
        Objects.requireNonNull(actual, "actual");
        if (index < 0 || index >= before.size() || !before.get(index).startsWith(TODO + " ")) {
            throw new IllegalArgumentException("Нужен индекс невыполненной задачи");
        }
        List<String> expected = new ArrayList<>(before);
        expected.set(index, DONE + before.get(index).substring(TODO.length()));
        assertListEquals(expected, actual, "отметка выполненной");
    }

    public static void assertDeleted(List<String> before, List<String> actual, int index) {
        Objects.requireNonNull(before, "before");
        Objects.requireNonNull(actual, "actual");
        if (index < 0 || index >= before.size()) {
            throw new IllegalArgumentException("Неверный индекс удаляемой задачи");
        }
        List<String> expected = new ArrayList<>(before);
        expected.remove(index);
        assertListEquals(expected, actual, "удаление");
    }

    public static void assertUnchanged(List<String> before, List<String> actual) {
        assertListEquals(before, actual, "список не должен измениться");
    }

    public static void assertText(String expected, String actual, String what) {
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError(what + ": ожидалось <" + expected + ">, получено <" + actual + ">");
        }
    }

    public static void assertListEquals(List<String> expected, List<String> actual, String what) {
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError(what + ": ожидалось " + expected + ", получено " + actual);
        }
    }
}
