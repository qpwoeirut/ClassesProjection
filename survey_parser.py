import csv
from enum import Enum


# column numbers
class Column(Enum):
    TIMESTAMP = 0
    GRADE = 1
    CUR_SCI = 2
    PREV_SCI = 3
    NEXT_SCI = 4
    CUR_MATH = 5
    PREV_MATH = 6
    NEXT_MATH = 7


IGNORE = "ignore"


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


def convert_to_transformation(matrix: dict[str, dict[str, int]], count: dict[str, int]) -> dict[str, dict[str, float]]:
    for row_class, row in matrix.items():
        for col_class, col in row.items():
            matrix[row_class][col_class] /= max(count[row_class], 1)

    return matrix


def main():
    # read exported CSV file
    with open("Gunn Students Classes Survey (Responses) - Form Responses 1.csv") as file:
        reader = csv.reader(file, delimiter=",")
        data_rows = [row for row in reader]

    with open("math_classes.txt") as file:
        math_classes = [row.strip() for row in file]

    with open("science_classes.txt") as file:
        science_classes = [row.strip() for row in file]

    data_rows = parse_data(data_rows)

    science_matrix, science_count = compute_matrix(data_rows, science_classes, Column.PREV_SCI.value,
                                                   Column.CUR_SCI.value, Column.NEXT_SCI.value)
    math_matrix, math_count = compute_matrix(data_rows, math_classes, Column.PREV_MATH.value, Column.CUR_MATH.value,
                                             Column.NEXT_MATH.value)

    science_matrix = convert_to_transformation(science_matrix, science_count)
    math_matrix = convert_to_transformation(math_matrix, math_count)

    print_matrix(science_matrix)
    print_matrix(math_matrix)

    write_to_csv("science_matrix.csv", science_matrix)
    write_to_csv("math_matrix.csv", math_matrix)


if __name__ == '__main__':
    main()
