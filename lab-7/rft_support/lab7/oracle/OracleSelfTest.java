package lab7.oracle;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/** Проверяет только оракул на известных входах; не проверяет EXE или RFT. */
public final class OracleSelfTest {
    private static int passed = 0;
    private static List<String> l(String... s) { return Arrays.asList(s); }
    private static void accepts(String name, Runnable r) {
        r.run();
        passed++;
        System.out.println("PASS " + name);
    }
    private static void rejects(String name, Runnable r) {
        try {
            r.run();
        } catch (AssertionError expected) {
            passed++;
            System.out.println("PASS " + name + " (ожидаемое обнаружение расхождения)");
            return;
        }
        throw new AssertionError("Оракул не обнаружил расхождение: " + name);
    }
    public static void main(String[] args) {
        accepts("add-empty", () -> TodoAssertions.assertAdded(Collections.emptyList(), l("[ ] A"), "A"));
        accepts("add-tail", () -> TodoAssertions.assertAdded(l("[✓] A"), l("[✓] A", "[ ] B"), "B"));
        accepts("add-duplicate", () -> TodoAssertions.assertAdded(l("[ ] A"), l("[ ] A", "[ ] A"), "A"));
        accepts("mark-middle", () -> TodoAssertions.assertMarked(l("[ ] A", "[ ] B", "[✓] C"), l("[ ] A", "[✓] B", "[✓] C"), 1));
        accepts("delete-middle", () -> TodoAssertions.assertDeleted(l("[ ] A", "[✓] B", "[ ] C"), l("[ ] A", "[ ] C"), 1));
        accepts("unchanged", () -> TodoAssertions.assertUnchanged(l("[ ] A"), l("[ ] A")));
        accepts("empty-input", () -> TodoAssertions.assertText("", "", "поле"));
        accepts("warning", () -> TodoAssertions.assertText("Выберите задачу из списка!", "Выберите задачу из списка!", "диалог"));
        rejects("detect-no-added-record", () -> TodoAssertions.assertAdded(l("[ ] A"), l("[ ] A"), "B"));
        rejects("detect-wrong-text", () -> TodoAssertions.assertAdded(l("[ ] A"), l("[ ] A", "[ ] C"), "B"));
        rejects("detect-changed-previous", () -> TodoAssertions.assertAdded(l("[ ] A"), l("[✓] A", "[ ] B"), "B"));
        rejects("detect-wrong-marked-row", () -> TodoAssertions.assertMarked(l("[ ] A", "[ ] B"), l("[✓] A", "[ ] B"), 1));
        rejects("detect-wrong-delete", () -> TodoAssertions.assertDeleted(l("[ ] A", "[ ] B"), l("[ ] B"), 1));
        rejects("detect-unwanted-mutation", () -> TodoAssertions.assertUnchanged(l("[ ] A"), l("[✓] A")));
        rejects("detect-not-empty", () -> TodoAssertions.assertText("", "A", "поле"));
        rejects("detect-wrong-warning", () -> TodoAssertions.assertText("Выберите задачу из списка!", "Другое предупреждение", "диалог"));
        System.out.println("ИТОГО: " + passed + " самопроверок оракула; EXE и RFT не тестировались.");
    }
}
