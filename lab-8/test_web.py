from __future__ import annotations

import csv
import os
import shutil
import sqlite3
import threading
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app import TaskServer

ROOT = Path(__file__).resolve().parent
with (ROOT / "task_data.csv").open(encoding="utf-8", newline="") as f:
    DATA = list(csv.DictReader(f))


@pytest.fixture
def site(tmp_path):
    """У каждого теста собственная БД и сервер, пустые предусловия гарантированы."""
    db_path = tmp_path / "test.sqlite3"
    server = TaskServer(("127.0.0.1", 0), db_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/", db_path
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


@pytest.fixture
def browser(site, tmp_path):
    os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"
    os.environ["no_proxy"] = os.environ["NO_PROXY"]
    binary = os.environ.get("CHROMIUM_BINARY") or shutil.which("chromium") or shutil.which("chromium-browser")
    driver_path = os.environ.get("CHROMEDRIVER") or shutil.which("chromedriver")
    if not binary or not driver_path:
        pytest.fail("Нужны Chromium и совместимый chromedriver; см. REPORT.md")
    options = webdriver.ChromeOptions()
    options.binary_location = binary
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1100,850")
    options.add_argument(f"--user-data-dir={tmp_path / 'chrome-profile'}")
    driver = webdriver.Chrome(service=Service(executable_path=driver_path), options=options)
    driver.set_page_load_timeout(15)
    try:
        driver.get(site[0])
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "task-input")))
        yield driver
    finally:
        driver.quit()


def db_rows(site):
    with sqlite3.connect(site[1]) as db:
        return db.execute("SELECT id, title, completed FROM tasks ORDER BY id").fetchall()


def ui_rows(driver):
    result = []
    for item in driver.find_elements(By.CSS_SELECTOR, "#task-list li"):
        result.append((int(item.get_attribute("data-id")),
                       item.find_element(By.CSS_SELECTOR, ".task-title").get_attribute("textContent"),
                       item.find_element(By.CSS_SELECTOR, ".task-status").get_attribute("textContent")))
    return result


def assert_ui_matches_db(driver, site):
    expected = [(task_id, title, "[✓]" if done else "[ ]") for task_id, title, done in db_rows(site)]
    assert ui_rows(driver) == expected


def submit_and_wait(driver, button_id):
    # Presence alone may match the *old* document before POST/redirect completes.
    # The marker disappears only after a new document has loaded.
    driver.execute_script("window.__webdriver_old_document = true")
    driver.find_element(By.ID, button_id).click()
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script(
            "return window.__webdriver_old_document !== true && document.readyState === 'complete'"
        )
    )


def add(driver, title):
    field = driver.find_element(By.ID, "task-input")
    field.clear()
    field.send_keys(title)
    submit_and_wait(driver, "add")


def select(driver, task_id):
    driver.find_element(By.CSS_SELECTOR, f'input[name="task_id"][value="{task_id}"]').click()


def expect_alert(driver, expected):
    alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
    assert alert.text == expected
    alert.accept()
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "task-input")))


def test_initial_interface_and_storage(browser, site):
    assert browser.title == "Командный трекер задач — демо"
    assert browser.find_element(By.TAG_NAME, "h1").text == "Командный трекер задач"
    for element in ("task-input", "add", "complete", "delete", "task-list"):
        assert browser.find_element(By.ID, element).is_displayed()
    assert ui_rows(browser) == []
    assert db_rows(site) == []


@pytest.mark.parametrize("record", DATA, ids=[x["case"] for x in DATA])
def test_add_from_data_pool(browser, site, record):
    assert db_rows(site) == []
    add(browser, record["title"])
    rows = db_rows(site)
    assert len(rows) == 1 and rows[0][1:] == (record["title"], 0)
    assert_ui_matches_db(browser, site)
    assert browser.find_element(By.ID, "task-input").get_attribute("value") == ""
    browser.refresh()
    assert_ui_matches_db(browser, site)


@pytest.mark.parametrize("title", ["", "   ", "\u00a0"], ids=["empty", "spaces", "nonbreaking-space"])
def test_reject_blank_and_preserve_existing(browser, site, title):
    add(browser, "Существующая задача")
    before = db_rows(site)
    field = browser.find_element(By.ID, "task-input")
    field.clear()
    if title:
        field.send_keys(title)
    browser.find_element(By.ID, "add").click()
    expect_alert(browser, "Текст задачи не может быть пустым!")
    assert db_rows(site) == before
    assert_ui_matches_db(browser, site)


@pytest.mark.parametrize("button,message", [
    ("complete", "Выберите задачу из списка!"),
    ("delete", "Выберите задачу для удаления!"),
])
def test_no_selection_preserves_data(browser, site, button, message):
    add(browser, "Задача без выбора")
    before = db_rows(site)
    browser.find_element(By.ID, button).click()
    expect_alert(browser, message)
    assert db_rows(site) == before
    assert_ui_matches_db(browser, site)


def test_complete_selected_and_repeated_warning(browser, site):
    for title in ("Первая", "Вторая", "Третья"):
        add(browser, title)
    before = db_rows(site)
    target = before[1][0]
    select(browser, target)
    submit_and_wait(browser, "complete")
    expected = [before[0], (target, before[1][1], 1), before[2]]
    assert db_rows(site) == expected
    assert_ui_matches_db(browser, site)
    select(browser, target)
    browser.find_element(By.ID, "complete").click()
    expect_alert(browser, "Эта задача уже выполнена")
    assert db_rows(site) == expected
    assert_ui_matches_db(browser, site)
    browser.get(site[0])  # do not resubmit the warning POST
    assert db_rows(site) == expected
    assert_ui_matches_db(browser, site)


def test_delete_selected_preserves_other_order_and_status(browser, site):
    for title in ("Альфа", "Бета", "Гамма"):
        add(browser, title)
    initial = db_rows(site)
    select(browser, initial[0][0])
    submit_and_wait(browser, "complete")
    before = db_rows(site)
    select(browser, before[1][0])
    submit_and_wait(browser, "delete")
    assert db_rows(site) == [before[0], before[2]]
    assert_ui_matches_db(browser, site)
    browser.refresh()
    assert_ui_matches_db(browser, site)


def test_delete_completed_task(browser, site):
    add(browser, "Удалить выполненную")
    task_id = db_rows(site)[0][0]
    select(browser, task_id)
    submit_and_wait(browser, "complete")
    assert db_rows(site) == [(task_id, "Удалить выполненную", 1)]
    assert_ui_matches_db(browser, site)
    select(browser, task_id)
    submit_and_wait(browser, "delete")
    assert db_rows(site) == []
    assert_ui_matches_db(browser, site)


def test_many_records_and_duplicate_titles(browser, site):
    titles = ["Одинаковая запись" if n in (7, 22) else f"Массовая задача {n:02d}" for n in range(1, 31)]
    assert db_rows(site) == []
    for title in titles:
        add(browser, title)
    before = db_rows(site)
    assert len(before) == 30
    assert [r[1] for r in before] == titles
    assert all(r[2] == 0 for r in before)
    assert_ui_matches_db(browser, site)
    # Вторая из одноимённых записей меняется по ID, а не по тексту.
    duplicate = before[21][0]
    select(browser, duplicate)
    submit_and_wait(browser, "complete")
    after = db_rows(site)
    expected = [(i, title, int(i == duplicate)) for i, title, _ in before]
    assert after == expected
    assert_ui_matches_db(browser, site)
    select(browser, before[6][0])
    submit_and_wait(browser, "delete")
    assert db_rows(site) == [row for row in expected if row[0] != before[6][0]]
    assert_ui_matches_db(browser, site)


def test_capture_real_browser_state(browser, site):
    add(browser, "Подготовить отчёт")
    add(browser, "Проверить сохранение")
    first_id = db_rows(site)[0][0]
    select(browser, first_id)
    submit_and_wait(browser, "complete")
    assert [(r[1], r[2]) for r in db_rows(site)] == [("Подготовить отчёт", 1), ("Проверить сохранение", 0)]
    assert_ui_matches_db(browser, site)
    destination = ROOT / "artifacts" / "selenium-demo.png"
    destination.parent.mkdir(exist_ok=True)
    assert browser.save_screenshot(str(destination))
