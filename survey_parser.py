import csv
from enum import Enum

# column numbers
TIMESTAMP = 0
GRADE = 1
CUR_SCI = 2
PREV_SCI = 3
NEXT_SCI = 4
CUR_MATH = 5
PREV_MATH = 6
NEXT_MATH = 7

IGNORE = "ignore"
NO_CLASS_AT_GUNN = "No class at Gunn"


def parse_data(data: list) -> list[list[set]]:
    with open("mapping.txt") as file:
        mapping = {row.split("=>")[0].strip(): row.split("=>")[1].strip() for row in file}

    headings, data = data[0], data[1:]
    data = [
        [[x.strip() for x in value.split(',')] for value in row]
        for row in data
    ]
    data = [
        [[x if x not in mapping else mapping[x] for x in values] for values in row]
        for row in data
    ]
    data = [
        [{x for x in values if x != IGNORE} for values in row]
        for row in data
    ]
    return data


def compute_matrix(data_rows: list, classes: list, prev_class_col: int, cur_class_col: int,
                   next_class_col: int) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    matrix = {
        class1: {class2: 0 for class2 in classes}
        for class1 in classes
    }

    count = {c: 0 for c in classes}

    for row in data_rows:
        prev_classes = row[prev_class_col]
        cur_classes = row[cur_class_col]
        next_classes = row[next_class_col]

        for current_class in cur_classes:
            for previous_class in prev_classes:
                matrix[previous_class][current_class] += 1
                count[previous_class] += 1
            for next_class in next_classes:
                matrix[current_class][next_class] += 1
            count[current_class] += 1

    return matrix, count


def print_matrix(matrix: dict[str, dict[str, float]]):
    for row_class, row in matrix.items():
        print(row_class, row)


def write_to_csv(filename: str, matrix: dict[str, dict[str, float]]):
    classes = [""] + [row_class for row_class in matrix.keys()]

    with open(filename, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(classes)
        for row_class, row in matrix.items():
            row_values = [row_class]
            row_values.extend(row.values())
            writer.writerow(row_values)


def convert_to_probability(matrix: dict[str, dict[str, int]], count: dict[str, int]) -> dict[str, dict[str, float]]:
    for row_class, row in matrix.items():
        for col_class, col in row.items():
            matrix[row_class][col_class] /= max(count[row_class], 1)

    return matrix


def calculate_reg_honors(data_rows: list, is_honors, prev_class_col: int, cur_class_col: int,
                         next_class_col: int) -> tuple[float, float]:
    reg_to_honors = 0
    honors_to_reg = 0
    total = 0
    for row in data_rows:
        prev_honors = any(is_honors[prev_class] for prev_class in row[prev_class_col])
        current_honors = any(is_honors[current_class] for current_class in row[cur_class_col])
        next_honors = any(is_honors[next_class] for next_class in row[next_class_col])

        if NO_CLASS_AT_GUNN not in row[prev_class_col] and NO_CLASS_AT_GUNN not in row[cur_class_col]:
            if prev_honors is False and current_honors is True:
                reg_to_honors += 1
            if prev_honors is True and current_honors is False:
                honors_to_reg += 1
            total += 1

        if NO_CLASS_AT_GUNN not in row[cur_class_col] and NO_CLASS_AT_GUNN not in row[next_class_col]:
            if current_honors is False and next_honors is True:
                reg_to_honors += 1
            if current_honors is True and next_honors is False:
                honors_to_reg += 1
            total += 1

    return reg_to_honors / total, honors_to_reg / total


def main():
    # read exported CSV file
    with open("Gunn Students Classes Survey (Responses) - Form Responses 1.csv") as file:
        reader = csv.reader(file, delimiter=",")
        data_rows = [row for row in reader]

    with open("math_classes.txt") as file:
        math_class_list = [row.strip().split('|') for row in file]
        math_classes = [math_class[1].strip() for math_class in math_class_list]

    with open("science_classes.txt") as file:
        science_class_list = [row.strip().split('|') for row in file]
        science_classes = [math_class[1].strip() for math_class in science_class_list]

    is_honors = {c[1].strip(): c[0].strip() == "Hon" for c in math_class_list + science_class_list}

    data_rows = parse_data(data_rows)

    math_matrix, math_count = compute_matrix(data_rows, math_classes, PREV_MATH, CUR_MATH, NEXT_MATH)
    science_matrix, science_count = compute_matrix(data_rows, science_classes, PREV_SCI, CUR_SCI, NEXT_SCI)

    math_matrix = convert_to_probability(math_matrix, math_count)
    science_matrix = convert_to_probability(science_matrix, science_count)

    math_reg_to_honors, math_honors_to_reg = calculate_reg_honors(data_rows, is_honors, PREV_MATH, CUR_MATH, NEXT_MATH)
    math_honors_retained = 1 - math_honors_to_reg

    science_reg_to_honors, science_honors_to_reg = calculate_reg_honors(data_rows, is_honors, PREV_SCI, CUR_SCI,
                                                                        NEXT_SCI)
    science_honors_retained = 1 - science_honors_to_reg

    write_to_csv("math_matrix.csv", math_matrix)
    write_to_csv("science_matrix.csv", science_matrix)

    print("–" * 11, "Math", "–" * 12)
    print("Regular to Honors:", math_reg_to_honors * 100)
    print("Honors to Regular:", math_honors_to_reg * 100)
    print("Honors Retained:  ", math_honors_retained * 100)
    print()
    print("–" * 10, "Science", "–" * 10)
    print("Regular to Honors:", science_reg_to_honors * 100)
    print("Honors to Regular:", science_honors_to_reg * 100)
    print("Honors Retained:  ", science_honors_retained * 100)


if __name__ == '__main__':
    main()
