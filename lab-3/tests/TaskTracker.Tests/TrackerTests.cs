using Lab3.TaskTracker;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Tracker = Lab3.TaskTracker.TaskTracker;

namespace Lab3.TaskTracker.Tests;

[TestClass]
public class TrackerTests
{
    private Tracker _tracker = null!;

    [TestInitialize]
    public void Initialize() => _tracker = new Tracker();

    private static void AssertResult(OperationResult result, ResultCode code,
        string? message = null, bool shouldClearInput = false)
    {
        Assert.AreEqual(code, result.Code);
        Assert.AreEqual(message, result.Message);
        Assert.AreEqual(shouldClearInput, result.ShouldClearInput);
    }

    private static string[] Display(Tracker tracker) =>
        tracker.GetTasks().Select(item => item.DisplayText).ToArray();

    private void AddThree()
    {
        _tracker.AddTask("First");
        _tracker.AddTask("Middle");
        _tracker.AddTask("Last");
    }

    [TestMethod]
    public void NewTracker_HasEmptySnapshot()
    {
        Assert.AreEqual(0, _tracker.GetTasks().Count);
    }

    [TestMethod]
    public void SeparateTrackers_DoNotShareTasks()
    {
        var other = new Tracker();
        _tracker.AddTask("One");
        Assert.AreEqual(0, other.GetTasks().Count);
        other.AddTask("Two");
        CollectionAssert.AreEqual(new[] { "[ ] One" }, Display(_tracker));
        CollectionAssert.AreEqual(new[] { "[ ] Two" }, Display(other));
    }

    [DataTestMethod]
    [DataRow("A")]
    [DataRow("Купить хлеб")]
    [DataRow("  важная задача  ")]
    [DataRow("\tA\n")]
    [DataRow("[✓] не статус, а текст 🚀")]
    public void AddTask_ValidText_AppendsAndRequestsInputClear(string text)
    {
        var result = _tracker.AddTask(text);
        AssertResult(result, ResultCode.Success, shouldClearInput: true);
        var tasks = _tracker.GetTasks();
        Assert.AreEqual(1, tasks.Count);
        Assert.AreEqual(text, tasks[0].Text);
        Assert.IsFalse(tasks[0].IsCompleted);
        Assert.AreEqual("[ ] " + text, tasks[0].DisplayText);
    }

    [TestMethod]
    public void AddTask_LongText_IsPreserved()
    {
        var text = new string('x', 10000);
        AssertResult(_tracker.AddTask(text), ResultCode.Success, shouldClearInput: true);
        Assert.AreEqual(text, _tracker.GetTasks()[0].Text);
    }

    [DataTestMethod]
    [DataRow("")]
    [DataRow(" ")]
    [DataRow("     ")]
    [DataRow("\t")]
    [DataRow("\r\n")]
    [DataRow("\u00a0")]
    public void AddTask_Whitespace_ReportsErrorAndPreservesState(string text)
    {
        AddThree();
        _tracker.CompleteTask(1);
        var before = Display(_tracker);
        var result = _tracker.AddTask(text);
        AssertResult(result, ResultCode.EmptyText, "Текст задачи не может быть пустым!");
        CollectionAssert.AreEqual(before, Display(_tracker));
    }

    [TestMethod]
    public void AddTask_Null_ReportsErrorAndDoesNotChangeList()
    {
        _tracker.AddTask("Existing");
        AssertResult(_tracker.AddTask(null), ResultCode.EmptyText, "Текст задачи не может быть пустым!");
        CollectionAssert.AreEqual(new[] { "[ ] Existing" }, Display(_tracker));
    }

    [TestMethod]
    public void AddTask_ExistingTasksAndStatuses_ArePreservedAndNewItemIsLast()
    {
        _tracker.AddTask("A");
        _tracker.AddTask("B");
        _tracker.CompleteTask(0);
        _tracker.AddTask("C");
        CollectionAssert.AreEqual(new[] { "[✓] A", "[ ] B", "[ ] C" }, Display(_tracker));
    }

    [TestMethod]
    public void AddTask_Duplicates_ProduceDistinctOrderedTasks()
    {
        _tracker.AddTask("same");
        _tracker.AddTask("same");
        _tracker.CompleteTask(1);
        CollectionAssert.AreEqual(new[] { "[ ] same", "[✓] same" }, Display(_tracker));
    }

    [DataTestMethod]
    [DataRow(false)]
    [DataRow(true)]
    public void CompleteTask_NoSelection_ShowsWarningWithoutChanges(bool hasItems)
    {
        if (hasItems) { AddThree(); _tracker.CompleteTask(1); }
        var before = Display(_tracker);
        AssertResult(_tracker.CompleteTask(null), ResultCode.NoSelection, "Выберите задачу из списка!");
        CollectionAssert.AreEqual(before, Display(_tracker));
    }

    [DataTestMethod]
    [DataRow(0)]
    [DataRow(1)]
    [DataRow(2)]
    public void CompleteTask_FirstMiddleOrLast_ChangesOnlySelectedStatus(int selected)
    {
        AddThree();
        var before = _tracker.GetTasks();
        AssertResult(_tracker.CompleteTask(selected), ResultCode.Success);
        var after = _tracker.GetTasks();
        Assert.AreEqual(before.Count, after.Count);
        for (var i = 0; i < after.Count; i++)
        {
            Assert.AreEqual(before[i].Text, after[i].Text);
            Assert.AreEqual(i == selected, after[i].IsCompleted);
            Assert.AreEqual((i == selected ? "[✓] " : "[ ] ") + before[i].Text, after[i].DisplayText);
        }
    }

    [TestMethod]
    public void CompleteTask_AlreadyCompleted_ShowsWarningAndDoesNotChangeState()
    {
        AddThree();
        _tracker.CompleteTask(1);
        var before = Display(_tracker);
        AssertResult(_tracker.CompleteTask(1), ResultCode.AlreadyCompleted, "Эта задача уже выполнена");
        CollectionAssert.AreEqual(before, Display(_tracker));
    }

    [DataTestMethod]
    [DataRow(-1)]
    [DataRow(3)]
    [DataRow(int.MinValue)]
    [DataRow(int.MaxValue)]
    public void CompleteTask_OutOfRange_ThrowsAndPreservesState(int index)
    {
        AddThree();
        _tracker.CompleteTask(1);
        var before = Display(_tracker);
        var exception = Assert.ThrowsException<ArgumentOutOfRangeException>(() => _tracker.CompleteTask(index));
        Assert.AreEqual("selectedIndex", exception.ParamName);
        CollectionAssert.AreEqual(before, Display(_tracker));
    }

    [TestMethod]
    public void CompleteTask_IndexZeroInEmptyList_ThrowsWithoutChanges()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => _tracker.CompleteTask(0));
        Assert.AreEqual(0, _tracker.GetTasks().Count);
    }

    [DataTestMethod]
    [DataRow(false)]
    [DataRow(true)]
    public void DeleteTask_NoSelection_ShowsWarningWithoutChanges(bool hasItems)
    {
        if (hasItems) { AddThree(); _tracker.CompleteTask(1); }
        var before = Display(_tracker);
        AssertResult(_tracker.DeleteTask(null), ResultCode.NoSelection, "Выберите задачу для удаления!");
        CollectionAssert.AreEqual(before, Display(_tracker));
    }

    [DataTestMethod]
    [DataRow(0, "[✓] Middle", "[ ] Last")]
    [DataRow(1, "[ ] First", "[ ] Last")]
    [DataRow(2, "[ ] First", "[✓] Middle")]
    public void DeleteTask_FirstMiddleOrLast_PreservesOthersInOrder(int selected, string first, string second)
    {
        AddThree();
        _tracker.CompleteTask(1);
        AssertResult(_tracker.DeleteTask(selected), ResultCode.Success);
        Assert.AreEqual(2, _tracker.GetTasks().Count);
        CollectionAssert.AreEqual(new[] { first, second }, Display(_tracker));
    }

    [DataTestMethod]
    [DataRow(false)]
    [DataRow(true)]
    public void DeleteTask_OnlyItem_LeavesEmptyListForEitherStatus(bool complete)
    {
        _tracker.AddTask("Only");
        if (complete) _tracker.CompleteTask(0);
        AssertResult(_tracker.DeleteTask(0), ResultCode.Success);
        Assert.AreEqual(0, _tracker.GetTasks().Count);
    }

    [DataTestMethod]
    [DataRow(-1)]
    [DataRow(3)]
    [DataRow(int.MinValue)]
    [DataRow(int.MaxValue)]
    public void DeleteTask_OutOfRange_ThrowsAndPreservesState(int index)
    {
        AddThree();
        _tracker.CompleteTask(1);
        var before = Display(_tracker);
        var exception = Assert.ThrowsException<ArgumentOutOfRangeException>(() => _tracker.DeleteTask(index));
        Assert.AreEqual("selectedIndex", exception.ParamName);
        CollectionAssert.AreEqual(before, Display(_tracker));
    }

    [TestMethod]
    public void DeleteTask_IndexZeroInEmptyList_ThrowsWithoutChanges()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => _tracker.DeleteTask(0));
        Assert.AreEqual(0, _tracker.GetTasks().Count);
    }

    [TestMethod]
    public void DeleteTask_DuplicateSelectedByIndex_DeletesCorrectOccurrence()
    {
        _tracker.AddTask("same");
        _tracker.AddTask("same");
        _tracker.CompleteTask(0);
        _tracker.DeleteTask(1);
        CollectionAssert.AreEqual(new[] { "[✓] same" }, Display(_tracker));
    }

    [TestMethod]
    public void GetTasks_SnapshotIsReadOnlyAndDoesNotTrackSubsequentChanges()
    {
        _tracker.AddTask("A");
        var snapshot = _tracker.GetTasks();
        var list = (IList<TaskEntry>)snapshot;
        Assert.ThrowsException<NotSupportedException>(() => list.Clear());
        Assert.ThrowsException<NotSupportedException>(() => list[0] = null!);
        _tracker.CompleteTask(0);
        _tracker.AddTask("B");
        Assert.AreEqual(1, snapshot.Count);
        Assert.IsFalse(snapshot[0].IsCompleted);
        Assert.AreEqual("[ ] A", snapshot[0].DisplayText);
        CollectionAssert.AreEqual(new[] { "[✓] A", "[ ] B" }, Display(_tracker));
    }

    [TestMethod]
    public void Workflow_AddCompleteDeleteAndAddAgain_EndsInExpectedState()
    {
        _tracker.AddTask("A");
        _tracker.AddTask("B");
        _tracker.CompleteTask(0);
        _tracker.DeleteTask(1);
        _tracker.AddTask("C");
        _tracker.CompleteTask(1);
        _tracker.DeleteTask(0);
        CollectionAssert.AreEqual(new[] { "[✓] C" }, Display(_tracker));
    }
}
