#include "tracker/task_tracker.h"

#include <gtest/gtest.h>

#include <cstddef>
#include <limits>
#include <optional>
#include <ostream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {
using tracker::Result;
using tracker::TaskTracker;
using Snapshot = std::vector<std::pair<std::string, bool>>;

Snapshot snapshot(const TaskTracker& model) {
    Snapshot copy;
    for (const auto& task : model.tasks()) {
        copy.emplace_back(task.text, task.done);
    }
    return copy;
}

TEST(TaskTrackerBasics, StartsEmpty) {
    TaskTracker model;
    EXPECT_TRUE(model.input().empty());
    EXPECT_TRUE(model.tasks().empty());
    EXPECT_TRUE(model.display_lines().empty());
}

TEST(TaskTrackerBasics, SetInputReplacesTheFieldWithoutChangingTasks) {
    TaskTracker model;
    model.set_input("original task");
    ASSERT_EQ(model.add_from_input(), Result::Ok);
    const auto before = snapshot(model);
    model.set_input("first value");
    model.set_input("replacement");
    EXPECT_EQ(model.input(), "replacement");
    EXPECT_EQ(snapshot(model), before);
}

TEST(TaskTrackerBasics, ResultMessagesMatchSpecification) {
    EXPECT_EQ(tracker::message(Result::Ok), std::string_view(""));
    EXPECT_EQ(tracker::message(Result::EmptyText), std::string_view("Текст задачи не может быть пустым!"));
    EXPECT_EQ(tracker::message(Result::NoSelectionForComplete), std::string_view("Выберите задачу из списка!"));
    EXPECT_EQ(tracker::message(Result::AlreadyCompleted), std::string_view("Эта задача уже выполнена"));
    EXPECT_EQ(tracker::message(Result::NoSelectionForDelete), std::string_view("Выберите задачу для удаления!"));
}

TEST(TaskTrackerBasics, ReturnedDisplayLinesAreIndependentCopies) {
    TaskTracker model;
    model.set_input("task");
    ASSERT_EQ(model.add_from_input(), Result::Ok);
    auto lines = model.display_lines();
    ASSERT_EQ(lines.size(), 1u);
    lines[0] = "changed copy";
    EXPECT_EQ(model.display_lines(), (std::vector<std::string>{"[ ] task"}));
    EXPECT_EQ(model.tasks()[0].text, "task");
}

TEST(TaskTrackerBasics, PreservesEmbeddedNulBytes) {
    TaskTracker model;
    const std::string input("x\0y", 3);
    model.set_input(input);
    ASSERT_EQ(model.add_from_input(), Result::Ok);
    ASSERT_EQ(model.tasks().size(), 1u);
    EXPECT_EQ(model.tasks()[0].text, input);
    ASSERT_EQ(model.display_lines().size(), 1u);
    EXPECT_EQ(model.display_lines()[0], std::string("[ ] ") + input);
}

TEST(TaskTrackerBasics, DuplicateTitlesAreIndependentTasks) {
    TaskTracker model;
    for (int i = 0; i < 2; ++i) {
        model.set_input("same");
        ASSERT_EQ(model.add_from_input(), Result::Ok);
    }
    ASSERT_EQ(model.complete(0), Result::Ok);
    EXPECT_EQ(snapshot(model), (Snapshot{{"same", true}, {"same", false}}));
    ASSERT_EQ(model.remove(0), Result::Ok);
    EXPECT_EQ(snapshot(model), (Snapshot{{"same", false}}));
}

class PopulatedTrackerTest : public ::testing::Test {
protected:
    TaskTracker model;

    void SetUp() override {
        for (const auto* text : {"first", "second", "третья"}) {
            model.set_input(text);
            ASSERT_EQ(model.add_from_input(), Result::Ok);
        }
        ASSERT_EQ(model.complete(1), Result::Ok);
        model.set_input("unsubmitted field");
    }
};

TEST_F(PopulatedTrackerTest, FixtureHasExpectedOrderStatusesAndRendering) {
    EXPECT_EQ(snapshot(model), (Snapshot{{"first", false}, {"second", true}, {"третья", false}}));
    EXPECT_EQ(model.display_lines(), (std::vector<std::string>{"[ ] first", "[✓] second", "[ ] третья"}));
    EXPECT_EQ(model.input(), "unsubmitted field");
}

TEST_F(PopulatedTrackerTest, AddAppendsAndPreservesEveryPriorTask) {
    const auto before = snapshot(model);
    model.set_input("  new task  ");
    ASSERT_EQ(model.add_from_input(), Result::Ok);
    auto after = snapshot(model);
    ASSERT_EQ(after.size(), before.size() + 1);
    EXPECT_EQ(Snapshot(after.begin(), after.end() - 1), before);
    EXPECT_EQ(after.back(), (std::pair<std::string, bool>{"  new task  ", false}));
    EXPECT_TRUE(model.input().empty());
    EXPECT_EQ(model.display_lines().back(), "[ ]   new task  ");
}

TEST_F(PopulatedTrackerTest, RepeatedCompletionDoesNotChangeStateOrField) {
    const auto before = snapshot(model);
    EXPECT_EQ(model.complete(1), Result::AlreadyCompleted);
    EXPECT_EQ(snapshot(model), before);
    EXPECT_EQ(model.input(), "unsubmitted field");
}

TEST_F(PopulatedTrackerTest, RemovingAllTasksEventuallyLeavesEmptyState) {
    ASSERT_EQ(model.remove(1), Result::Ok);
    ASSERT_EQ(model.remove(1), Result::Ok);
    ASSERT_EQ(model.remove(0), Result::Ok);
    EXPECT_TRUE(model.tasks().empty());
    EXPECT_TRUE(model.display_lines().empty());
    EXPECT_EQ(model.input(), "unsubmitted field");
    EXPECT_EQ(model.remove(0), Result::NoSelectionForDelete);
}

struct StringCase {
    const char* name;
    std::string text;
};

void PrintTo(const StringCase& value, std::ostream* out) {
    *out << value.name;
}

class InvalidInputTest : public ::testing::TestWithParam<StringCase> {};
TEST_P(InvalidInputTest, RejectsWithoutChangingListOrInput) {
    TaskTracker model;
    model.set_input("already present");
    ASSERT_EQ(model.add_from_input(), Result::Ok);
    ASSERT_EQ(model.complete(0), Result::Ok);
    const auto before = snapshot(model);
    const auto value = GetParam().text;
    model.set_input(value);
    EXPECT_EQ(model.add_from_input(), Result::EmptyText);
    EXPECT_EQ(snapshot(model), before);
    EXPECT_EQ(model.input(), value);
}
INSTANTIATE_TEST_SUITE_P(InvalidValues, InvalidInputTest, ::testing::ValuesIn(std::vector<StringCase>{
    {"Empty", ""}, {"OneSpace", " "}, {"ManySpaces", "     "},
    {"Tab", "\t"}, {"Newline", "\n"}, {"CarriageReturn", "\r"},
    {"VerticalTab", "\v"}, {"FormFeed", "\f"}, {"MixedWhitespace", " \t\n\r\v\f"}
}), [](const ::testing::TestParamInfo<StringCase>& info) { return info.param.name; });

class ValidInputTest : public ::testing::TestWithParam<StringCase> {};
TEST_P(ValidInputTest, AddsExactTextAndClearsField) {
    TaskTracker model;
    const auto value = GetParam().text;
    model.set_input(value);
    ASSERT_EQ(model.add_from_input(), Result::Ok);
    ASSERT_EQ(model.tasks().size(), 1u);
    EXPECT_EQ(model.tasks()[0].text, value);
    EXPECT_FALSE(model.tasks()[0].done);
    EXPECT_TRUE(model.input().empty());
    EXPECT_EQ(model.display_lines(), (std::vector<std::string>{"[ ] " + value}));
}
INSTANTIATE_TEST_SUITE_P(ValidValues, ValidInputTest, ::testing::ValuesIn(std::vector<StringCase>{
    {"OneCharacter", "0"}, {"Simple", "task"}, {"WhitespaceAround", " task "},
    {"MixedWhitespaceAround", " \tX\n "}, {"Cyrillic", "Задача"},
    {"Emoji", "Задача 🗓"}, {"UnicodeNonBreakingSpace", "\xC2\xA0"}
}), [](const ::testing::TestParamInfo<StringCase>& info) { return info.param.name; });

struct IndexCase {
    const char* name;
    std::optional<std::size_t> index;
};

void PrintTo(const IndexCase& value, std::ostream* out) {
    *out << value.name;
}

class CompleteValidIndexTest : public PopulatedTrackerTest,
                               public ::testing::WithParamInterface<IndexCase> {};
TEST_P(CompleteValidIndexTest, ChangesOnlySelectedStatusAndPreservesOrder) {
    auto expected = snapshot(model);
    const auto selected = *GetParam().index;
    ASSERT_FALSE(expected[selected].second);
    expected[selected].second = true;
    ASSERT_EQ(model.complete(selected), Result::Ok);
    EXPECT_EQ(snapshot(model), expected);
    EXPECT_EQ(model.input(), "unsubmitted field");
    ASSERT_EQ(model.display_lines().size(), expected.size());
    EXPECT_EQ(model.display_lines()[selected], "[✓] " + expected[selected].first);
}
INSTANTIATE_TEST_SUITE_P(BoundaryTasks, CompleteValidIndexTest, ::testing::ValuesIn(std::vector<IndexCase>{
    {"First", 0}, {"Last", 2}
}), [](const ::testing::TestParamInfo<IndexCase>& info) { return info.param.name; });

class DeleteValidIndexTest : public PopulatedTrackerTest,
                             public ::testing::WithParamInterface<IndexCase> {};
TEST_P(DeleteValidIndexTest, DeletesExactlyOneAndPreservesOthers) {
    auto expected = snapshot(model);
    const auto selected = *GetParam().index;
    expected.erase(expected.begin() + static_cast<Snapshot::difference_type>(selected));
    ASSERT_EQ(model.remove(selected), Result::Ok);
    EXPECT_EQ(snapshot(model), expected);
    EXPECT_EQ(model.input(), "unsubmitted field");
    ASSERT_EQ(model.display_lines().size(), expected.size());
    for (std::size_t i = 0; i < expected.size(); ++i) {
        EXPECT_EQ(model.display_lines()[i], std::string(expected[i].second ? "[✓] " : "[ ] ") + expected[i].first);
    }
}
INSTANTIATE_TEST_SUITE_P(Positions, DeleteValidIndexTest, ::testing::ValuesIn(std::vector<IndexCase>{
    {"First", 0}, {"MiddleCompleted", 1}, {"Last", 2}
}), [](const ::testing::TestParamInfo<IndexCase>& info) { return info.param.name; });

const std::vector<IndexCase> invalid_for_three{
    {"NoSelection", std::nullopt}, {"AtSize", 3}, {"BeyondSize", 4},
    {"MaximumIndex", std::numeric_limits<std::size_t>::max()}
};

class CompleteInvalidIndexTest : public PopulatedTrackerTest,
                                 public ::testing::WithParamInterface<IndexCase> {};
TEST_P(CompleteInvalidIndexTest, RejectsWithoutChangingAnyState) {
    const auto before = snapshot(model);
    EXPECT_EQ(model.complete(GetParam().index), Result::NoSelectionForComplete);
    EXPECT_EQ(snapshot(model), before);
    EXPECT_EQ(model.input(), "unsubmitted field");
}
INSTANTIATE_TEST_SUITE_P(InvalidSelection, CompleteInvalidIndexTest, ::testing::ValuesIn(invalid_for_three),
    [](const ::testing::TestParamInfo<IndexCase>& info) { return info.param.name; });

class DeleteInvalidIndexTest : public PopulatedTrackerTest,
                               public ::testing::WithParamInterface<IndexCase> {};
TEST_P(DeleteInvalidIndexTest, RejectsWithoutChangingAnyState) {
    const auto before = snapshot(model);
    EXPECT_EQ(model.remove(GetParam().index), Result::NoSelectionForDelete);
    EXPECT_EQ(snapshot(model), before);
    EXPECT_EQ(model.input(), "unsubmitted field");
}
INSTANTIATE_TEST_SUITE_P(InvalidSelection, DeleteInvalidIndexTest, ::testing::ValuesIn(invalid_for_three),
    [](const ::testing::TestParamInfo<IndexCase>& info) { return info.param.name; });

const std::vector<IndexCase> invalid_for_empty{
    {"NoSelection", std::nullopt}, {"Zero", 0},
    {"MaximumIndex", std::numeric_limits<std::size_t>::max()}
};

class EmptyListSelectionTest : public ::testing::TestWithParam<IndexCase> {};
TEST_P(EmptyListSelectionTest, BothOperationsRejectAndPreserveEmptyState) {
    TaskTracker model;
    model.set_input("draft");
    EXPECT_EQ(model.complete(GetParam().index), Result::NoSelectionForComplete);
    EXPECT_EQ(model.remove(GetParam().index), Result::NoSelectionForDelete);
    EXPECT_TRUE(model.tasks().empty());
    EXPECT_EQ(model.input(), "draft");
}
INSTANTIATE_TEST_SUITE_P(EmptyList, EmptyListSelectionTest, ::testing::ValuesIn(invalid_for_empty),
    [](const ::testing::TestParamInfo<IndexCase>& info) { return info.param.name; });

}  // namespace
