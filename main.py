import json
from pathlib import Path


def calculate_mac(pattern, filter_matrix):
    total = 0.0
    size = len(pattern)

    for row in range(size):
        for col in range(size):
            total += pattern[row][col] * filter_matrix[row][col]

    return total


def read_matrix(label, size=3):
    print(f"\n{label} ({size}줄 입력, 공백 구분)")

    matrix = []

    for row_index in range(size):
        while True:
            user_input = input(f"{row_index + 1}행 : ")
            values = user_input.split()

            if len(values) != size:
                print(
                    f"입력 형식 오류 : 각 줄에 {size}개의 숫자를 "
                    "공백으로 구분해 입력하세요."
                )
                continue

            try:
                row = [float(value) for value in values]
            except ValueError:
                print("입력 형식 오류 : 숫자만 입력하세요.")
                continue

            matrix.append(row)
            break

    return matrix


def classify_scores(score_a, score_b, label_a="A", label_b="B", epsilon=1e-9):
    if abs(score_a - score_b) < epsilon:
        return "UNDECIDED"

    if score_a > score_b:
        return label_a

    return label_b


def load_json_data():
    data_path = Path(__file__).resolve().parent / "data.json"

    try:
        with data_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError:
        print("파일 오류 : data.json을 찾을 수 없습니다.")

    except json.JSONDecodeError as error:
        print(f"JSON 문법 오류 : {error}")

    except OSError as error:
        print(f"파일 읽기 오류 : {error}")

    return None


def select_filters_for_pattern(data, pattern_key):
    parts = pattern_key.split("_")

    if (
        len(parts) != 3
        or parts[0] != "size"
        or not parts[1].isdigit()
        or not parts[2].isdigit()
    ):
        raise ValueError(f"잘못된 패턴 키 : {pattern_key}")

    size = int(parts[1])
    index = int(parts[2])

    if size <= 0 or index <= 0:
        raise ValueError(f"잘못된 패턴 키 : {pattern_key}")

    filter_key = f"size_{size}"
    filters = data["filters"][filter_key]

    return size, filters


def normalize_label(raw_label, label_type):
    mappings = {
        "expected": {
            "+": "Cross",
            "x": "X"
        },
        "filter": {
            "cross": "Cross",
            "x": "X"
        }
    }

    if label_type not in mappings:
        raise ValueError(f"알 수 없는 라벨 유형 : {label_type}")

    if not isinstance(raw_label, str):
        raise ValueError(f"문자열이 아닌 라벨 : {raw_label!r}")

    if raw_label not in mappings[label_type]:
        raise ValueError(
            f"지원하지 않는 {label_type} 라벨 : {raw_label!r}"
        )

    return mappings[label_type][raw_label]


def validate_matrix(matrix, size, label):
    if not isinstance(matrix, list):
        raise ValueError(
            f"{label} : 2차원 리스트가 아닙니다."
        )

    if len(matrix) != size:
        raise ValueError(
            f"{label} : 행 개수가 {size}개여야 합니다. "
            f"(현재 {len(matrix)}개)"
        )

    for row_number, row in enumerate(matrix, start=1):
        if not isinstance(row, list):
            raise ValueError(
                f"{label} : {row_number}행이 리스트가 아닙니다."
            )

        if len(row) != size:
            raise ValueError(
                f"{label} : {row_number}행의 열 개수가 "
                f"{size}개여야 합니다. (현재 {len(row)}개)"
            )

        for col_number, value in enumerate(row, start=1):
            if isinstance(value, bool) or not isinstance(
                value, (int, float)
            ):
                raise ValueError(
                    f"{label} : {row_number}행 {col_number}열에 "
                    "숫자가 아닌 값이 있습니다."
                )


def main():
    print("=== Mini NPU Simulator ===")

    print("\n[1] 필터 입력")

    filter_a = read_matrix("필터 A")
    filter_b = read_matrix("필터 B")

    print("\n[저장 확인]")
    print(f"필터 A : {filter_a}")
    print(f"필터 B : {filter_b}")

    print("\n[2] 패턴 입력")

    pattern = read_matrix("패턴")

    score_a = calculate_mac(pattern, filter_a)
    score_b = calculate_mac(pattern, filter_b)

    result = classify_scores(score_a, score_b)

    print("\n[3] MAC 결과")
    print(f"A 점수 : {score_a}")
    print(f"B 점수 : {score_b}")

    if result == "UNDECIDED":
        print("판정 : 판정 불가 (UNDECIDED)")
    else:
        print(f"판정 : {result}")


if __name__ == "__main__":
    main()
