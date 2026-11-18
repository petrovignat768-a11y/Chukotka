# Лабораторная работа 3 — модульное тестирование .NET

Самостоятельная учебная модель трекера задач, а **не исходный код и не проверка** исходного `todo_app.exe`.

- [Отчёт, фактические результаты и ограничения](REPORT.md)
- [Контракт модели и допущения](SPECIFICATION.md)
- Библиотека: `src/TaskTracker/TaskTracker.csproj`; тесты MSTest: `tests/TaskTracker.Tests/TaskTracker.Tests.csproj`.
- [Сгенерированная XML-документация](docs/TaskTracker.xml), [TRX](TestResults/lab3.trx), [покрытие Cobertura](docs/coverage.cobertura.xml).

Запуск в Linux: `./run-tests.sh`. Нужен .NET SDK 8.0 и доступ к NuGet при первоначальном восстановлении. Иной исполняемый файл можно указать через `DOTNET=/path/to/dotnet ./run-tests.sh`. Консольный журнал пишется в `logs/dotnet-test.log`. Сохранённые TRX и покрытие относятся к выполненному запуску; при следующем запуске покрытие будет создано в новом подкаталоге `TestResults`.
