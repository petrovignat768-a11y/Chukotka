# Лабораторная работа 4 — Google Test

Самостоятельная модель трекера задач по пользовательской спецификации. Это не исходный код `todo_app.exe` и не тестирование этого EXE. Подробности: [спецификация](SPECIFICATION.md), [отчёт](REPORT.md), [документация API](APIDOC.md).

Нужны CMake 3.20+, компилятор C++17 и установленный пакет Google Test (с CMake-целями `GTest::gtest_main`); в Linux подходят пакеты разработчика вашего дистрибутива. Зависимости не загружаются автоматически. Из папки проекта:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --config Debug
ctest --test-dir build -C Debug --output-on-failure
```

Для одноконфигурационного Unix-генератора можно также вызвать `./build/task_tracker_tests --gtest_color=no`. В многоконфигурационном Visual Studio путь будет `build/Debug/task_tracker_tests.exe`. Сборка на Windows/macOS предполагается, но в этой работе не проверялась. Дополнительно документацию API можно пересоздать командой `python3 tools/generate_api_doc.py`; Python для сборки и тестов не нужен.

Полный фактический журнал — [logs/test-run.log](logs/test-run.log); измерение покрытия GCC/gcov — в `logs/coverage-gcov-retry.log` и `logs/coverage/task_tracker.cpp.gcov`.
