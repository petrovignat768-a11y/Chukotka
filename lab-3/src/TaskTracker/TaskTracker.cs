namespace Lab3.TaskTracker;

/// <summary>Код результата пользовательского действия.</summary>
public enum ResultCode
{
    /// <summary>Действие выполнено.</summary>
    Success,
    /// <summary>Текст отсутствует или состоит из пробельных символов.</summary>
    EmptyText,
    /// <summary>Задача не выбрана.</summary>
    NoSelection,
    /// <summary>Задача уже выполнена.</summary>
    AlreadyCompleted
}

/// <summary>Результат действия, передаваемый в вызывающий интерфейс.</summary>
public sealed class OperationResult
{
    internal OperationResult(ResultCode code, string? message = null, bool shouldClearInput = false)
    {
        Code = code;
        Message = message;
        ShouldClearInput = shouldClearInput;
    }

    /// <summary>Код результата.</summary>
    public ResultCode Code { get; }
    /// <summary>Текст предупреждения или null в случае успеха.</summary>
    public string? Message { get; }
    /// <summary>Очистить поле ввода; true только при успешном добавлении.</summary>
    public bool ShouldClearInput { get; }
}

/// <summary>Неизменяемая запись задачи на момент получения снимка списка.</summary>
public sealed class TaskEntry
{
    internal TaskEntry(string text, bool isCompleted = false)
    {
        Text = text;
        IsCompleted = isCompleted;
    }

    /// <summary>Исходный текст задачи без обрезки.</summary>
    public string Text { get; }
    /// <summary>True, если задача выполнена.</summary>
    public bool IsCompleted { get; }
    /// <summary>Отображение с префиксом статуса.</summary>
    public string DisplayText => $"{(IsCompleted ? "[✓]" : "[ ]")} {Text}";
}

/// <summary>Однопользовательская модель списка задач без пользовательского интерфейса.</summary>
public sealed class TaskTracker
{
    private readonly List<TaskEntry> _tasks = new();

    /// <summary>Создаёт трекер с пустым списком.</summary>
    public TaskTracker() { }

    /// <summary>Добавляет непустой текст в конец; возвращает признак очистки поля.</summary>
    /// <param name="text">Текст задачи; null или пробельная строка не добавляются.</param>
    /// <returns>Успех с признаком очистки либо ошибка с предупреждением.</returns>
    public OperationResult AddTask(string? text)
    {
        if (string.IsNullOrWhiteSpace(text))
            return new OperationResult(ResultCode.EmptyText, "Текст задачи не может быть пустым!");

        _tasks.Add(new TaskEntry(text));
        return new OperationResult(ResultCode.Success, shouldClearInput: true);
    }

    /// <summary>Отмечает выбранную задачу как выполненную, сохраняя порядок.</summary>
    /// <param name="selectedIndex">Нулевой индекс, либо null при отсутствии выбора.</param>
    /// <returns>Успех либо предупреждение об отсутствии выбора или повторном выполнении.</returns>
    /// <exception cref="ArgumentOutOfRangeException">Выбранный индекс вне диапазона списка.</exception>
    public OperationResult CompleteTask(int? selectedIndex)
    {
        if (selectedIndex is null)
            return new OperationResult(ResultCode.NoSelection, "Выберите задачу из списка!");

        var index = ValidateIndex(selectedIndex.Value);
        var task = _tasks[index];
        if (task.IsCompleted)
            return new OperationResult(ResultCode.AlreadyCompleted, "Эта задача уже выполнена");

        _tasks[index] = new TaskEntry(task.Text, isCompleted: true);
        return new OperationResult(ResultCode.Success);
    }

    /// <summary>Удаляет выбранную задачу, сохраняя относительный порядок остальных.</summary>
    /// <param name="selectedIndex">Нулевой индекс, либо null при отсутствии выбора.</param>
    /// <returns>Успех либо предупреждение об отсутствии выбора.</returns>
    /// <exception cref="ArgumentOutOfRangeException">Выбранный индекс вне диапазона списка.</exception>
    public OperationResult DeleteTask(int? selectedIndex)
    {
        if (selectedIndex is null)
            return new OperationResult(ResultCode.NoSelection, "Выберите задачу для удаления!");

        var index = ValidateIndex(selectedIndex.Value);
        _tasks.RemoveAt(index);
        return new OperationResult(ResultCode.Success);
    }

    /// <summary>Возвращает снимок, который нельзя изменить через интерфейс списка.</summary>
    /// <returns>Упорядоченный снимок неизменяемых записей.</returns>
    public IReadOnlyList<TaskEntry> GetTasks() => Array.AsReadOnly(_tasks.ToArray());

    private int ValidateIndex(int selectedIndex)
    {
        if (selectedIndex < 0 || selectedIndex >= _tasks.Count)
            throw new ArgumentOutOfRangeException(nameof(selectedIndex));
        return selectedIndex;
    }
}
